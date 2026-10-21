from pydantic import BaseModel,Field

class ValidationError(BaseModel):
    error_type: str
    file_path: str
    message: str


class ValidationReport(BaseModel):
    success: bool = True
    
    missing_files: list[str] = Field(default_factory=list)
    
    structure_errors: list[str] = Field(default_factory=list)
    
    syntax_errors: list[str] = Field(default_factory=list)
    
    ai_issues: list[str] = Field(default_factory=list)


    