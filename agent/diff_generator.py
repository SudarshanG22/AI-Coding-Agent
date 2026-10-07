import difflib
from pathlib import Path


class DiffGenerator:

    def __init__(self):
        pass

    # =========================================================
    # FIND EXISTING FILE
    # =========================================================

    def _find_existing_file(self, filename, codebase):

        normalized_filename = (
            str(filename)
            .replace("\\", "/")
            .strip()
            .lstrip("./")
        )

        # -----------------------------------------------------
        # Exact match
        # -----------------------------------------------------

        for existing_file in codebase:

            normalized_existing = (
                str(existing_file)
                .replace("\\", "/")
                .strip()
                .lstrip("./")
            )

            if normalized_existing.lower() == normalized_filename.lower():
                return existing_file

        # -----------------------------------------------------
        # Match when Gemini includes project folder
        #
        # Example:
        #
        # Gemini:
        # sample_project/routes.py
        #
        # Codebase:
        # routes.py
        # -----------------------------------------------------

        filename_path = Path(normalized_filename)

        filename_only = filename_path.name.lower()

        matching_files = []

        for existing_file in codebase:

            normalized_existing = (
                str(existing_file)
                .replace("\\", "/")
                .strip()
                .lstrip("./")
            )

            if Path(normalized_existing).name.lower() == filename_only:

                matching_files.append(existing_file)

        # -----------------------------------------------------
        # If exactly one file has that name, use it.
        # -----------------------------------------------------

        if len(matching_files) == 1:
            return matching_files[0]

        # -----------------------------------------------------
        # Try suffix matching
        # -----------------------------------------------------

        for existing_file in codebase:

            normalized_existing = (
                str(existing_file)
                .replace("\\", "/")
                .strip()
                .lstrip("./")
            )

            if normalized_filename.lower().endswith(
                "/" + normalized_existing.lower()
            ):
                return existing_file

        return None

    # =========================================================
    # GENERATE DIFF
    # =========================================================

    def generate_diff(self, codebase, changes):

        if not isinstance(changes, dict):

            raise ValueError(
                "Changes must be a dictionary."
            )

        if "changes" not in changes:

            raise ValueError(
                "Changes dictionary does not contain 'changes'."
            )

        generated_changes = changes["changes"]

        if not isinstance(generated_changes, list):

            raise ValueError(
                "'changes' must be a list."
            )

        if not generated_changes:

            raise ValueError(
                "No code changes were generated."
            )

        diff_sections = []

        for change in generated_changes:

            filename = (
                str(change.get("file", ""))
                .replace("\\", "/")
                .strip()
            )

            if not filename:

                raise ValueError(
                    "Generated change contains an empty filename."
                )

            action = (
                str(change.get("action", "MODIFY"))
                .upper()
                .strip()
            )

            new_content = change.get(
                "new_content",
                ""
            )

            if not isinstance(new_content, str):

                new_content = str(new_content)

            # =================================================
            # CREATE NEW FILE
            # =================================================

            if action == "CREATE":

                diff = difflib.unified_diff(
                    [],
                    new_content.splitlines(
                        keepends=True
                    ),
                    fromfile="/dev/null",
                    tofile=filename,
                    lineterm=""
                )

                diff_text = "".join(diff)

                if not diff_text:

                    diff_text = (
                        f"--- /dev/null\n"
                        f"+++ {filename}\n"
                    )

                diff_sections.append(
                    f"CREATE: {filename}\n"
                    f"{diff_text}"
                )

                continue

            # =================================================
            # MODIFY EXISTING FILE
            # =================================================

            if action == "MODIFY":

                actual_filename = (
                    self._find_existing_file(
                        filename,
                        codebase
                    )
                )

                # -------------------------------------------------
                # Important:
                #
                # Gemini may return:
                #
                # sample_project/routes.py
                #
                # while codebase contains:
                #
                # routes.py
                #
                # actual_filename resolves that difference.
                # -------------------------------------------------

                if actual_filename is None:

                    raise ValueError(
                        f"Cannot modify unknown file: {filename}"
                    )

                old_content = codebase[
                    actual_filename
                ]

                if not isinstance(
                    old_content,
                    str
                ):

                    old_content = str(
                        old_content
                    )

                diff = difflib.unified_diff(
                    old_content.splitlines(
                        keepends=True
                    ),
                    new_content.splitlines(
                        keepends=True
                    ),
                    fromfile=actual_filename,
                    tofile=filename,
                    lineterm=""
                )

                diff_text = "".join(diff)

                diff_sections.append(
                    f"MODIFY: {filename}\n"
                    f"{diff_text}"
                )

                continue

            # =================================================
            # INVALID ACTION
            # =================================================

            raise ValueError(
                f"Invalid action '{action}' "
                f"for file: {filename}"
            )

        # =====================================================
        # RETURN COMPLETE DIFF
        # =====================================================

        return "\n\n".join(
            diff_sections
        )