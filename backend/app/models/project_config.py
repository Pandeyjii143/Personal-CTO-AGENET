from pydantic import BaseModel
from typing import Optional


class ProjectConfig(BaseModel):
    project_name: str
    description: str

    frontend: bool = False
    backend: bool = True
    ai: bool = False

    database: str = "postgresql"

    deployment: str = "docker"

    github_mode: str = "new_repo"

    existing_repo: Optional[str] = None