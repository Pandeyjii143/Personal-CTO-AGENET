from app.services.test_service import TestService


def test_node(state):

    report = TestService.run_tests(
        state["project_folder"]
    )

    return {
        "test_report": report,
        "test_success": report["success"]
    }