import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from fastapi import BackgroundTasks, HTTPException
from openai import OpenAI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.agents.base_agent import BaseAgent
from app.models.generation_run import GenerationRun
from app.api import generation as generation_api
from app.schemas.generation_run import GenerationRunCreate
from app.services import app_generation_service, generation_run_service


class AppGenerationServiceTests(unittest.TestCase):
    def test_agent_errors_do_not_echo_request_api_key(self):
        request_key = "private-request-key"
        llm_client = OpenAI(api_key=request_key)
        with self.assertRaises(RuntimeError) as raised:
            with patch.object(
                llm_client.responses,
                "create",
                side_effect=RuntimeError(f"Provider rejected {request_key}"),
            ):
                BaseAgent.call_llm("Create a small app", llm_client)

        self.assertNotIn(request_key, str(raised.exception))

    def test_request_api_key_is_only_passed_to_background_task(self):
        request_prompt = "Create a useful application"
        run = GenerationRun(id=21, prompt=request_prompt, status="queued")
        background_tasks = BackgroundTasks()

        with (
            patch.object(generation_api.settings, "openai_api_key", ""),
            patch.object(
                generation_api.GenerationRunService,
                "create",
                return_value=run,
            ),
        ):
            result = generation_api.start_generation(
                request=GenerationRunCreate(prompt=request_prompt),
                background_tasks=background_tasks,
                db=object(),
                x_openai_api_key="  test-key  ",
            )

        self.assertIs(result, run)
        self.assertEqual(background_tasks.tasks[0].args, (21, "test-key"))
        self.assertNotIn(
            "openai_api_key",
            {column.name for column in GenerationRun.__table__.columns},
        )

    def test_background_run_forwards_request_key_without_persisting_it(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine = create_engine(f"sqlite:///{Path(temporary_directory) / 'runs.db'}")
            GenerationRun.__table__.create(engine)
            make_session = sessionmaker(bind=engine)
            db = make_session()
            run = GenerationRun(prompt="Create a useful application", status="queued")
            db.add(run)
            db.commit()
            run_id = run.id
            db.close()
            llm_client = OpenAI(api_key="test-key")
            generated = {
                "project_name": "generated-project",
                "project_folder": "generated_projects/generated-project",
                "result": {"file_count": 1},
            }

            with (
                patch.object(generation_run_service, "SessionLocal", make_session),
                patch.object(
                    generation_run_service,
                    "get_openai_client",
                    return_value=llm_client,
                ) as get_client,
                patch.object(
                    generation_run_service.AppGenerationService,
                    "generate",
                    return_value=generated,
                ) as generate,
            ):
                generation_run_service.GenerationRunService.execute(
                    run_id,
                    "request-only-key",
                )

            get_client.assert_called_once_with("request-only-key")
            generate.assert_called_once_with("Create a useful application", llm_client)
            db = make_session()
            stored_run = db.get(GenerationRun, run_id)
            self.assertEqual(stored_run.status, "completed")
            self.assertFalse(hasattr(stored_run, "openai_api_key"))
            db.close()
            engine.dispose()

    def test_generation_without_any_api_key_is_rejected(self):
        with (
            patch.object(generation_api.settings, "openai_api_key", ""),
            patch.object(generation_api.GenerationRunService, "create") as create_run,
        ):
            with self.assertRaisesRegex(HTTPException, "OpenAI API key is not configured"):
                generation_api.start_generation(
                    request=GenerationRunCreate(prompt="Create a useful application"),
                    background_tasks=BackgroundTasks(),
                    db=object(),
                    x_openai_api_key=None,
                )

        create_run.assert_not_called()

    def test_generated_paths_must_stay_inside_project(self):
        service = app_generation_service.AppGenerationService
        self.assertEqual(service._validate_file_path("app/main.py"), "app/main.py")

        for unsafe_path in ("../outside.py", r"..\outside.py", r"C:\outside.py", "/outside.py"):
            with self.subTest(path=unsafe_path):
                with self.assertRaisesRegex(ValueError, "Unsafe generated file path"):
                    service._validate_file_path(unsafe_path)

    def test_generate_writes_files_and_does_not_execute_generated_tests(self):
        service = app_generation_service.AppGenerationService
        prompt = "Create a small todo app for a single user."
        llm_client = OpenAI(api_key="test-key")
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            with (
                patch.object(service, "BACKEND_ROOT", root),
                patch.object(
                    app_generation_service.BackendAgent,
                    "execute",
                    return_value={
                        "backend_summary": "A small FastAPI app",
                        "required_files": ["app/main.py", "tests/test_app.py"],
                    },
                ) as backend_agent,
                patch.object(
                    app_generation_service.BackendCodeAgent,
                    "execute",
                    side_effect=lambda context, file_path, llm_client=None: {
                        "file_path": file_path,
                        "code": f"# {file_path}",
                    },
                ) as code_agent,
                patch.object(
                    app_generation_service.READMEAgent,
                    "execute",
                    return_value={"file_path": "README.md", "code": "# Generated"},
                ) as readme_agent,
                patch.object(
                    app_generation_service.RepairLoopService,
                    "execute",
                    return_value={
                        "success": True,
                        "attempts": 0,
                        "report": {"success": True},
                    },
                ) as repair_loop,
            ):
                result = service.generate(prompt, llm_client)

            project_folder = root / result["project_folder"]
            backend_agent.assert_called_once_with(prompt, llm_client)
            self.assertEqual(len(code_agent.call_args_list), 2)
            self.assertTrue(all(
                call.kwargs["llm_client"] is llm_client
                for call in code_agent.call_args_list
            ))
            self.assertIs(readme_agent.call_args.args[1], llm_client)
            self.assertIs(repair_loop.call_args.args[1], llm_client)
            self.assertEqual(result["result"]["file_count"], 3)
            self.assertEqual(result["result"]["tests"]["status"], "not_run")
            self.assertEqual(
                (project_folder / "app" / "main.py").read_text(encoding="utf-8"),
                "# app/main.py",
            )
            self.assertTrue((project_folder / "tests" / "test_app.py").exists())

    def test_failed_run_does_not_expose_internal_error(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine = create_engine(f"sqlite:///{Path(temporary_directory) / 'runs.db'}")
            GenerationRun.__table__.create(engine)
            make_session = sessionmaker(bind=engine)
            db = make_session()
            run = GenerationRun(prompt="Create a useful application", status="queued")
            db.add(run)
            db.commit()
            run_id = run.id
            db.close()

            with (
                patch.object(generation_run_service, "SessionLocal", make_session),
                patch.object(
                    generation_run_service.AppGenerationService,
                    "generate",
                    side_effect=RuntimeError("private provider details"),
                ),
            ):
                generation_run_service.GenerationRunService.execute(run_id)

            db = make_session()
            failed_run = db.get(GenerationRun, run_id)
            self.assertIsNotNone(failed_run)
            self.assertEqual(failed_run.status, "failed")
            self.assertNotIn("private provider details", failed_run.error_message)
            db.close()
            engine.dispose()

    def test_archive_excludes_dot_env_and_rejects_paths_outside_output(self):
        service = app_generation_service.AppGenerationService
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            project = root / "generated_projects" / "sample"
            project.mkdir(parents=True)
            (project / "main.py").write_text("print('hello')", encoding="utf-8")
            (project / ".env").write_text("SECRET=value", encoding="utf-8")
            run = GenerationRun(
                prompt="Create an example",
                status="completed",
                project_name="sample",
                project_folder="generated_projects/sample",
            )

            with patch.object(service, "BACKEND_ROOT", root):
                archive, filename = generation_run_service.GenerationRunService.build_archive(run)
                self.assertEqual(filename, "sample.zip")
                with ZipFile(archive) as zip_file:
                    self.assertEqual(zip_file.namelist(), ["sample/main.py"])
                    self.assertNotIn(
                        "SECRET=value",
                        zip_file.read(zip_file.namelist()[0]).decode(),
                    )

                run.project_folder = "../outside"
                with self.assertRaises(HTTPException):
                    generation_run_service.GenerationRunService.build_archive(run)


if __name__ == "__main__":
    unittest.main()
