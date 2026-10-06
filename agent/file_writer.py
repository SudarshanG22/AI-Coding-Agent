from pathlib import Path


class FileWriter:

    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()

    def apply_changes(self, changes):
        applied_files = []

        for change in changes.get("changes", []):

            filename = change.get("file")
            new_content = change.get("new_content")

            if not filename:
                raise ValueError(
                    "Change does not contain a filename."
                )

            if new_content is None:
                raise ValueError(
                    f"No new content provided for {filename}."
                )

            file_path = (
                self.project_path / filename
            ).resolve()

            # Security check:
            # Prevent writing outside the sample project.
            try:
                file_path.relative_to(self.project_path)
            except ValueError:
                raise ValueError(
                    f"Unsafe file path rejected: {filename}"
                )

            # Only allow modification of existing files.
            if not file_path.exists():
                raise FileNotFoundError(
                    f"File does not exist: {filename}"
                )

            file_path.write_text(
                new_content,
                encoding="utf-8"
            )

            applied_files.append(filename)

        return applied_files