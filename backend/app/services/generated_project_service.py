import os


class GeneratedProjectService:

    BASE_DIR = "generated_projects"

    @classmethod
    def get_latest_project(cls):

        folders = [
            os.path.join(
                cls.BASE_DIR,
                folder
            )
            for folder in os.listdir(
                cls.BASE_DIR
            )
        ]

        folders = [
            f for f in folders
            if os.path.isdir(f)
        ]

        folders.sort(
            key=os.path.getmtime,
            reverse=True
        )

        return folders[0]