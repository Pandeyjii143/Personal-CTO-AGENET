from typing import TypedDict


class RepairState(TypedDict):
    project_folder: str

    validation_report: dict

    test_report: dict

    repair_attempts: int

    success: bool

    test_success: bool