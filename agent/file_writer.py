from pathlib import Path


class FileWriter:

    def __init__(self, project_path):

        self.project_path = Path(
            project_path
        ).resolve()

    def apply_changes(self, changes):

        applied_files = []

        for change in changes.get(
            "changes",
            []
        ):

            filename = change.get(
                "file"
            )

            new_content = change.get(
                "new_content"
            )

            action = change.get(
                "action",
                "MODIFY"
            )

            if not filename:

                raise ValueError(
                    "Change does not contain a filename."
                )

            if new_content is None:

                raise ValueError(
                    f"No new content provided for {filename}."
                )

            # Normalize action
            action = str(
                action
            ).strip().upper()

            if action not in {
                "MODIFY",
                "CREATE"
            }:

                raise ValueError(
                    f"Unsupported file action '{action}' "
                    f"for {filename}."
                )

            # Resolve the requested path
            file_path = (
                self.project_path / filename
            ).resolve()

            # --------------------------------------------------
            # SECURITY CHECK
            # Prevent writing outside the project directory.
            # --------------------------------------------------

            try:

                file_path.relative_to(
                    self.project_path
                )

            except ValueError:

                raise ValueError(
                    f"Unsafe file path rejected: {filename}"
                )

            # --------------------------------------------------
            # MODIFY EXISTING FILE
            # --------------------------------------------------

            if action == "MODIFY":

                if not file_path.exists():

                    raise FileNotFoundError(
                        f"File does not exist: {filename}"
                    )

                if not file_path.is_file():

                    raise ValueError(
                        f"Path is not a file: {filename}"
                    )

            # --------------------------------------------------
            # CREATE NEW FILE
            # --------------------------------------------------

            elif action == "CREATE":

                # Never overwrite an existing file when the
                # agent explicitly requested CREATE.
                if file_path.exists():

                    raise FileExistsError(
                        f"Cannot create '{filename}' "
                        f"because the file already exists."
                    )

                # Create parent directories if the authorized
                # new file is inside a new directory.
                file_path.parent.mkdir(
                    parents=True,
                    exist_ok=True
                )

            # --------------------------------------------------
            # WRITE FILE
            # --------------------------------------------------

            file_path.write_text(
                new_content,
                encoding="utf-8"
            )

            applied_files.append(
                filename
            )

        return applied_files