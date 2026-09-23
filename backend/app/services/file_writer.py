import os

class FileWriter:

    @staticmethod
    def write_files(
        generated_files,
        project_name
    ):

        project_folder = os.path.join(
            "generated_projects",
            project_name
        )
        os.makedirs(
    project_folder,
    exist_ok=True
)

        for file_path, file_data in generated_files.items():

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
                f.write(file_data["code"])

        print(
            f"Project saved in {project_folder}"
        )