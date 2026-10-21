import os

from app.agents.repair_agent import RepairAgent


def load_project_files(project_folder):

    files = {}

    for root, _, filenames in os.walk(project_folder):

        for filename in filenames:

            if not filename.endswith(".py"):
                continue

            file_path = os.path.join(
                root,
                filename
            )

            relative_path = os.path.relpath(
                file_path,
                project_folder
            )

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:

                files[relative_path] = f.read()

    return files


def apply_fixes(
    project_folder,
    repaired_files
):

    for file_data in repaired_files:

        file_path = file_data.get(
            "file_path"
        )

        code = file_data.get(
            "code"
        )

        if not file_path:
            continue

        full_path = os.path.join(
            project_folder,
            file_path
        )

        os.makedirs(
            os.path.dirname(full_path),
            exist_ok=True
        )

        with open(
            full_path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(code)


def repair_node(state):

    files = load_project_files(
        state["project_folder"]
    )

    repair_result = RepairAgent.execute(
    validation_report=state["validation_report"],
    file_contents=files,
    test_report=state.get("test_report")
)

    apply_fixes(
        state["project_folder"],
        repair_result.get(
            "files",
            []
        )
    )

    return {
        "repair_attempts":
            state["repair_attempts"] + 1
    }