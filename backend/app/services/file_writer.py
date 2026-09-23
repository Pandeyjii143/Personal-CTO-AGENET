import os

class FileWriter:

    @staticmethod
    def write_files(generated_files, project_name):

        project_folder = os.path.join(
            "generated_projects",
            project_name
        )

        os.makedirs(
            project_folder,
            exist_ok=True
        )

        for file_path, file_data in generated_files.items():

            if "." not in os.path.basename(file_path):
              print(f"Skipping directory: {file_path}")
              continue

            # Skip directories
            if file_path.endswith("/"):
                os.makedirs(
                    os.path.join(project_folder, file_path),
                    exist_ok=True
                )
                continue

            full_path = os.path.join(
                project_folder,
                file_path
            )

            os.makedirs(
                os.path.dirname(full_path),
                exist_ok=True
            )

            code = file_data.get("code", "")

            with open(
                full_path,
                "w",
                encoding="utf-8"
            ) as f:
                f.write(code)

        print(
            f"Project saved in {project_folder}"
        )

        return project_folder