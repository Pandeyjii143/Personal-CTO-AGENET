from pydantic import BaseModel, Field


class ValidationReport(BaseModel):
    success: bool = True

    missing_files: list[str] = Field(default_factory=list)

    structure_errors: list[str] = Field(default_factory=list)

    syntax_errors: list[str] = Field(default_factory=list)

    ai_issues: list[str] = Field(default_factory=list)