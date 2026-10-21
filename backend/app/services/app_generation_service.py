import os
import re
import shutil
import uuid
from pathlib import Path, PurePosixPath

from openai import OpenAI

from app.agents.backend_agent import BackendAgent
from app.agents.backend_code_agent import BackendCodeAgent
from app.agents.readme_agent import READMEAgent
from app.models.execution_context import ExecutionContext
from app.services.repair_loop_service import RepairLoopService


class AppGenerationService:
    MAX_GENERATED_FILES = 40
    MAX_GENERATED_FILE_CHARS = 100_000
    BACKEND_ROOT = Path(__file__).resolve().parents[2]

    @classmethod
    def _project_directory(cls, project_name: str) -> Path:
        root = (cls.BACKEND_ROOT / "generated_projects").resolve()
        project = (root / project_name).resolve()
        if not project.is_relative_to(root):
            raise ValueError("Generated project path escapes the output directory")
        return project

    @staticmethod
    def _validate_file_path(value: object) -> str:
        if not isinstance(value, str) or not value or "\x00" in value:
            raise ValueError("Generated file path must be a non-empty string")

        normalized = value.replace("\\", "/")
        path = PurePosixPath(normalized)
        if (
            path.is_absolute()
            or re.match(r"^[a-zA-Z]:", normalized)
            or any(part in {"", ".", ".."} for part in normalized.split("/"))
        ):
            raise ValueError(f"Unsafe generated file path: {value}")
        return path.as_posix()

    @classmethod
    def generate(cls, prompt: str, llm_client: OpenAI | None = None) -> dict:
        plan = BackendAgent.execute(prompt, llm_client)
        if not isinstance(plan, dict) or not isinstance(plan.get("required_files"), list):
            raise ValueError("Backend planner returned an invalid file plan")
        if plan.get("success") is False:
            raise ValueError(plan.get("error", "Backend planner could not create a file plan"))

        required_files = list(dict.fromkeys(
            cls._validate_file_path(path) for path in plan["required_files"]
        ))
        if not required_files:
            raise ValueError("Backend planner returned no files to generate")
        if len(required_files) > cls.MAX_GENERATED_FILES:
            raise ValueError(
                f"Backend planner requested {len(required_files)} files; "
                f"the limit is {cls.MAX_GENERATED_FILES}"
            )

        project_name = f"generated_project_{uuid.uuid4().hex[:12]}"
        project_folder = cls._project_directory(project_name)
        project_folder.mkdir(parents=True, exist_ok=False)

        try:
            context = ExecutionContext(task=prompt, backend_plan=plan)
            generated_files: dict[str, str] = {}

            for file_path in required_files:
                generated = BackendCodeAgent.execute(
                    context=context,
                    file_path=file_path,
                    llm_client=llm_client,
                )
                if not isinstance(generated, dict) or not isinstance(generated.get("code"), str):
                    raise ValueError(f"Code agent returned invalid content for {file_path}")
                returned_path = cls._validate_file_path(generated.get("file_path", file_path))
                if returned_path != file_path:
                    raise ValueError(
                        f"Code agent returned {returned_path} while generating {file_path}"
                    )
                if len(generated["code"]) > cls.MAX_GENERATED_FILE_CHARS:
                    raise ValueError(f"Generated file exceeds size limit: {file_path}")
                generated_files[file_path] = generated["code"]

            context.generated_files = generated_files
            readme = READMEAgent.execute(context, llm_client)
            if (
                not isinstance(readme, dict)
                or not isinstance(readme.get("code"), str)
                or cls._validate_file_path(readme.get("file_path")) != "README.md"
            ):
                raise ValueError("README agent returned an invalid README")
            if len(readme["code"]) > cls.MAX_GENERATED_FILE_CHARS:
                raise ValueError("Generated README exceeds size limit")
            generated_files["README.md"] = readme["code"]

            for file_path, code in generated_files.items():
                destination = (project_folder / file_path).resolve()
                if not destination.is_relative_to(project_folder):
                    raise ValueError(f"Generated file path escapes project: {file_path}")
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(code, encoding="utf-8")

            repair_result = RepairLoopService.execute(
                str(project_folder),
                llm_client,
            )
        except Exception:
            if project_folder.is_relative_to(
                (cls.BACKEND_ROOT / "generated_projects").resolve()
            ):
                shutil.rmtree(project_folder, ignore_errors=True)
            raise

        return {
            "project_name": project_name,
            "project_folder": os.path.relpath(project_folder, cls.BACKEND_ROOT),
            "result": {
                "file_count": len(generated_files),
                "validation": repair_result,
                "tests": {
                    "status": "not_run",
                    "reason": "Generated test code is not executed automatically.",
                },
            },
        }
