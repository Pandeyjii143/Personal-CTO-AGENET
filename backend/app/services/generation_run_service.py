from io import BytesIO
import logging
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session

from app.agents.openai_client import get_openai_client
from app.db.session import SessionLocal
from app.models.generation_run import GenerationRun
from app.services.app_generation_service import AppGenerationService

logger = logging.getLogger(__name__)


class GenerationRunService:
    @staticmethod
    def create(db: Session, prompt: str) -> GenerationRun:
        run = GenerationRun(prompt=prompt, status="queued")
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def list_runs(db: Session, limit: int = 50) -> list[GenerationRun]:
        return (
            db.query(GenerationRun)
            .order_by(GenerationRun.created_at.desc(), GenerationRun.id.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_run(db: Session, run_id: int) -> GenerationRun:
        run = db.query(GenerationRun).filter(GenerationRun.id == run_id).first()
        if run is None:
            raise HTTPException(status_code=404, detail="Generation run not found")
        return run

    @classmethod
    def execute(cls, run_id: int, api_key: str | None = None) -> None:
        db = SessionLocal()
        try:
            run = db.query(GenerationRun).filter(GenerationRun.id == run_id).first()
            if run is None:
                raise LookupError(f"Generation run {run_id} no longer exists")

            run.status = "running"
            db.commit()
            prompt = run.prompt

            generated = AppGenerationService.generate(
                prompt,
                get_openai_client(api_key),
            )
            run.project_name = generated["project_name"]
            run.project_folder = generated["project_folder"]
            run.result = generated["result"]
            run.status = "completed"
            db.commit()
        except Exception:
            logger.exception("Generation run %s failed", run_id)
            db.rollback()
            run = db.query(GenerationRun).filter(GenerationRun.id == run_id).first()
            if run is not None:
                run.status = "failed"
                run.error_message = "Generation failed. Check the backend logs for details."
                db.commit()
            else:
                raise
        finally:
            db.close()

    @staticmethod
    def build_archive(run: GenerationRun) -> tuple[BytesIO, str]:
        if run.status != "completed" or not run.project_folder:
            raise HTTPException(
                status_code=409,
                detail="This project is not ready to download yet",
            )

        backend_root = AppGenerationService.BACKEND_ROOT.resolve()
        project_folder = (backend_root / run.project_folder).resolve()
        generated_root = (backend_root / "generated_projects").resolve()
        if (
            not project_folder.is_relative_to(generated_root)
            or not project_folder.is_dir()
        ):
            raise HTTPException(status_code=404, detail="Generated project files not found")

        archive = BytesIO()
        with ZipFile(archive, mode="w", compression=ZIP_DEFLATED) as zip_file:
            for file_path in project_folder.rglob("*"):
                if not file_path.is_file() or file_path.name == ".env":
                    continue
                resolved = file_path.resolve()
                if not resolved.is_relative_to(project_folder):
                    raise HTTPException(status_code=400, detail="Unsafe generated file path")
                zip_file.write(resolved, Path(run.project_name or project_folder.name) / resolved.relative_to(project_folder))

        archive.seek(0)
        filename = f"{run.project_name or project_folder.name}.zip"
        return archive, filename
