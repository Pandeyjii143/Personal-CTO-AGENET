from fastapi import APIRouter

from app.graphs.repair_graph import repair_graph

from app.services.generated_project_service import GeneratedProjectService

repair_router = APIRouter(
    prefix="/projects",
    tags=["Repair Loop"]
)


@repair_router.post(
    "/{project_id}/repair"
)
def repair_project(
    project_id: int
):

    project_folder = (
        f"generated_projects/project_{project_id}"
    )

    result = repair_graph.invoke(
        {
            "project_folder": project_folder,
            "validation_report": {},
            "test_report": {},
            "repair_attempts": 0,
            "success": False,
            "test_success": False
        }
    )

    return result

@repair_router.post(
    "/latest/repair"
)
def repair_latest_project():

    folder = (
        GeneratedProjectService
        .get_latest_project()
    )

    return repair_graph.invoke(
        {
            "project_folder": folder,
            "validation_report": {},
            "test_report": {},
            "repair_attempts": 0,
            "success": False,
            "test_success": False
        }
    )