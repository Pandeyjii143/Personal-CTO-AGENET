from app.db.base import Base
from app.models.project import Project
from app.models.blueprint import Blueprint
from app.models.milestone import Milestone
from app.models.task import Task
from app.models.generated_project import GeneratedProject
from app.models.generated_file import GeneratedFile


target_metadata = Base.metadata