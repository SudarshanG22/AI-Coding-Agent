from pathlib import Path


class CodebaseReader:

    def __init__(self, project_path):
        self.project_path = Path(project_path)

    def get_files(self):

        allowed_extensions = {
            ".py",
            ".js",
            ".ts",
            ".java",
            ".cpp",
            ".c",
            ".sql",
            ".html",
            ".css"
        }

        files = []

        for file_path in self.project_path.rglob("*"):

            if file_path.is_file() and file_path.suffix in allowed_extensions:
                files.append(file_path)

        return files

    def read_file(self, file_path):

        try:
            return file_path.read_text(
                encoding="utf-8"
            )

        except UnicodeDecodeError:
            return "[Unable to read this file as text]"

    def read_codebase(self):

        codebase = {}

        for file_path in self.get_files():

            relative_path = file_path.relative_to(
                self.project_path
            )

            codebase[str(relative_path)] = self.read_file(
                file_path
            )

        return codebase