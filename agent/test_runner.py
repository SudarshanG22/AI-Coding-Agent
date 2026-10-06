import subprocess
import sys
from pathlib import Path


class TestRunner:

    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()

    def run_tests(self):

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q"
            ],
            cwd=self.project_path,
            capture_output=True,
            text=True
        )

        return {
            "success": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }