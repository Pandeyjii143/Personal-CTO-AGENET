import subprocess


class TestService:

    @staticmethod
    def run_tests(project_folder: str):

        try:

            result = subprocess.run(
                ["pytest"],
                cwd=project_folder,
                capture_output=True,
                text=True,
                timeout=120
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }

        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e)
            }