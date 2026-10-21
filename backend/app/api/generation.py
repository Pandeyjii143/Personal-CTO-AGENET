from io import BytesIO

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.settings import settings
from app.db.dependencies import get_db
from app.models.generation_run import GenerationRun
from app.schemas.generation_run import GenerationRunCreate, GenerationRunResponse
from app.services.generation_run_service import GenerationRunService

router = APIRouter(prefix="/generation-runs", tags=["Generation"])


@router.post("", response_model=GenerationRunResponse, status_code=202)
def start_generation(
    request: GenerationRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    x_openai_api_key: str | None = Header(
        default=None,
        alias="X-OpenAI-API-Key",
        max_length=512,
    ),
) -> GenerationRun:
    api_key = x_openai_api_key.strip() if x_openai_api_key else None
    if not api_key and not settings.openai_api_key.strip():
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured. Provide one with this request or configure it on the backend.",
        )

    run = GenerationRunService.create(db, request.prompt)
    background_tasks.add_task(GenerationRunService.execute, run.id, api_key)
    return run


@router.get("", response_model=list[GenerationRunResponse])
def list_generation_runs(db: Session = Depends(get_db)) -> list[GenerationRun]:
    return GenerationRunService.list_runs(db)


@router.get("/{run_id}", response_model=GenerationRunResponse)
def get_generation_run(
    run_id: int,
    db: Session = Depends(get_db),
) -> GenerationRun:
    return GenerationRunService.get_run(db, run_id)


@router.get("/{run_id}/download")
def download_generated_project(
    run_id: int,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    run = GenerationRunService.get_run(db, run_id)
    archive, filename = GenerationRunService.build_archive(run)
    return StreamingResponse(
        BytesIO(archive.getvalue()),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
