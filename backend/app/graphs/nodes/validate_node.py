from app.services.validator_service import ValidatorService

from app.services.test_service import TestService


def test_node(state):

    report = TestService.run_tests(
        state["project_folder"]
    )

    return {
        "test_report": report,
        "test_success": report["success"]
    }
def validate_node(state):

    report = ValidatorService.validate_project(
        state["project_folder"]
    )

    return {
        "validation_report": report.model_dump(),
        "success": report.success
    }