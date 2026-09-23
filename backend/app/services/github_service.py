from github import Github
import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

class GitHubService:

    @staticmethod
    def create_repo(repo_name):

        token = os.getenv("GITHUB_TOKEN")

        print("TOKEN =", token)

        github = Github(token)

        user = github.get_user()

        print("USER =", user.login)

        repo = user.create_repo(
            name=repo_name,
            private=False
        )

        return repo.clone_url

    @staticmethod
    def push_project(
        project_folder,
        repo_name
    ):
        clone_url = GitHubService.create_repo(
            repo_name
        )

        username = os.getenv(
            "GITHUB_USERNAME"
        )

        token = os.getenv(
            "GITHUB_TOKEN"
        )
        

        auth_url = clone_url.replace(
            "https://",
            f"https://{username}:{token}@"
        )

        subprocess.run(
            ["git", "init"],
            cwd=project_folder
        )

        subprocess.run(
            ["git", "add", "."],
            cwd=project_folder
        )

        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Initial AI generated project"
            ],
            cwd=project_folder
        )

        subprocess.run(
            [
                "git",
                "branch",
                "-M",
                "main"
            ],
            cwd=project_folder
        )

        subprocess.run(
            [
                "git",
                "remote",
                "add",
                "origin",
                auth_url
            ],
            cwd=project_folder
        )

        subprocess.run(
            [
                "git",
                "push",
                "-u",
                "origin",
                "main"
            ],
            cwd=project_folder
        )

        return clone_url