import os
import ast
from pathlib import Path

from app.schemas.validation import ValidationReport



class ValidatorService:

    @staticmethod
    def validate_project(
        project_folder: str
    ) -> ValidationReport:

        required_files = [
            "requirements.txt",
            ".env.example"
        ]

        missing_files = ValidatorService.check_files(
            project_folder,
            required_files
        )

        structure_errors = ValidatorService.check_structure(
            project_folder
        )

        syntax_errors = ValidatorService.check_syntax(
            project_folder
        )

        ai_issues = ValidatorService.ai_review(
            project_folder
        )

        success = (
            len(missing_files) == 0
            and len(structure_errors) == 0
            and len(syntax_errors) == 0
            and len(ai_issues) == 0
        )

        return ValidationReport(
            success=success,
            missing_files=missing_files,
            structure_errors=structure_errors,
            syntax_errors=syntax_errors,
            ai_issues=ai_issues
        )
    @staticmethod
    def check_files(
        project_folder: str,
        required_files: list[str]
    ):

        missing = []

        root = Path(project_folder)

        for file_path in required_files:

            if not (root / file_path).exists():

                missing.append(file_path)

        return missing  
    
    @staticmethod
    def check_structure(
        project_folder: str
    ):

        required_dirs = [
            "app",
            "tests"
        ]

        errors = []

        root = Path(project_folder)

        for directory in required_dirs:

            if not (root / directory).exists():

                errors.append(
                    f"Missing directory: {directory}"
                )

        return errors
    
    @staticmethod
    def check_syntax(
        project_folder: str
    ):

        errors = []

        root = Path(project_folder)

        for file in root.rglob("*.py"):

            try:

                content = file.read_text(
                    encoding="utf-8"
                )

                ast.parse(content)

            except Exception as e:

                errors.append(
                    f"{file}: {str(e)}"
                )

        return errors

    @staticmethod
    def ai_review(
        project_folder: str
    ):
        return []
                    