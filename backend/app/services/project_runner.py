import subprocess

class ProjectRunner:

    @staticmethod
    def run_tests():

        result = subprocess.run(
            ["pytest"],
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
test_result = ProjectRunner.run_tests()