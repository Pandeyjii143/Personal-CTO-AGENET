
import os
import re

from openai import OpenAI

from app.services.validator_service import ValidatorService
from app.agents.repair_agent import RepairAgent


class RepairLoopService:

    MAX_REPAIR_ATTEMPTS = 3
    MAX_REPAIR_CONTEXT_CHARS = 6500

    @staticmethod
    def _load_project_files(project_folder: str) -> dict[str, str]:
        files = {}

        for root, _, filenames in os.walk(project_folder):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue

                file_path = os.path.join(root, filename)

                relative_path = os.path.relpath(
                    file_path,
                    project_folder
                ).replace("\\", "/")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        files[relative_path] = f.read()
                except (OSError, UnicodeDecodeError):
                    continue

        return files

    @classmethod
    def _select_relevant_files(
        cls,
        project_folder: str,
        validation_report: dict,
        all_files: dict[str, str]
    ) -> dict[str, str]:

        selected = {}

        # 1. Select files explicitly reported as syntax errors.
        syntax_errors = validation_report.get(
            "syntax_errors", []
        )

        project_root = os.path.abspath(project_folder)

        for error in syntax_errors:
            match = re.search(
                r"(.+?\.py):",
                str(error)
            )

            if not match:
                continue

            reported_path = match.group(1).strip()

            if not os.path.isabs(reported_path):
                reported_path = os.path.abspath(reported_path)

            reported_path = os.path.normcase(
                os.path.normpath(reported_path)
            )

            for relative_path in all_files:
                full_path = os.path.normcase(
                    os.path.normpath(
                        os.path.abspath(
                            os.path.join(
                                project_root,
                                relative_path
                            )
                        )
                    )
                )

                if full_path == reported_path:
                    selected[relative_path] = all_files[
                        relative_path
                    ]

        # 2. Include the application entry point when available.
        important_files = [
            "app/main.py",
            "app/config.py",
            "app/core/config.py",
        ]

        for file_path in important_files:
            if file_path in all_files:
                selected.setdefault(
                    file_path,
                    all_files[file_path]
                )

        # 3. If nothing matched, use one small project file
        # rather than sending the entire project.
        if not selected and all_files:
            first_file = sorted(all_files)[0]
            selected[first_file] = all_files[first_file]

        # 4. Keep the selected file contents within budget.
        final_files = {}
        total_chars = 0

        for file_path, content in selected.items():
            remaining = (
                cls.MAX_REPAIR_CONTEXT_CHARS - total_chars
            )

            if remaining <= 0:
                break

            if len(content) > remaining:
                content = content[:remaining]

            final_files[file_path] = content
            total_chars += len(content)

        print(
            f"Repair Context | "
            f"Files: {len(final_files)} | "
            f"Characters: {total_chars}"
        )

        return final_files

    @staticmethod
    def _apply_fixes(
        project_folder: str,
        repaired_files: list
    ):

        project_root = os.path.abspath(project_folder)

        for file_data in repaired_files:
            file_path = file_data.get("file_path")
            code = file_data.get("code")

            if not file_path or not isinstance(code, str):
                continue

            full_path = os.path.abspath(
                os.path.join(
                    project_root,
                    file_path
                )
            )

            # Do not allow generated repair paths to escape
            # the generated project directory.
            try:
                if os.path.commonpath(
                    [project_root, full_path]
                ) != project_root:
                    print(
                        f"Skipping unsafe repair path: {file_path}"
                    )
                    continue
            except ValueError:
                continue

            os.makedirs(
                os.path.dirname(full_path),
                exist_ok=True
            )

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(code)

            print(f"Repaired file: {file_path}")

    @classmethod
    def execute(cls, project_folder: str, llm_client: OpenAI | None = None):

        for attempt in range(
            cls.MAX_REPAIR_ATTEMPTS
        ):

            report = ValidatorService.validate_project(
                project_folder
            )

            validation_report = report.model_dump()

            if report.success:
                return {
                    "success": True,
                    "attempts": attempt,
                    "report": validation_report
                }

            all_files = cls._load_project_files(
                project_folder
            )

            relevant_files = cls._select_relevant_files(
                project_folder=project_folder,
                validation_report=validation_report,
                all_files=all_files
            )

            print(
                f"Repair Attempt: {attempt + 1}/"
                f"{cls.MAX_REPAIR_ATTEMPTS}"
            )

            repair_result = RepairAgent.execute(
                validation_report=validation_report,
                file_contents=relevant_files,
                llm_client=llm_client,
            )

            if not isinstance(repair_result, dict):
                raise ValueError(
                    "RepairAgent returned an invalid result"
                )

            if not repair_result.get("files"):
                print(
                    "RepairAgent returned no files to repair"
                )
                break

            cls._apply_fixes(
                project_folder,
                repair_result["files"]
            )

        final_report = ValidatorService.validate_project(
            project_folder
        )

        return {
            "success": final_report.success,
            "attempts": cls.MAX_REPAIR_ATTEMPTS,
            "report": final_report.model_dump()
        }
