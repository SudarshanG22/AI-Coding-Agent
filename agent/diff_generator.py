import difflib


class DiffGenerator:

    def generate_diff(self, codebase, changes):
        diff_output = ""

        # Normalize codebase paths so Windows "\" and "/" are treated equally
        normalized_codebase = {
            str(filename).replace("\\", "/"): content
            for filename, content in codebase.items()
        }

        for change in changes.get("changes", []):

            filename = str(change["file"]).replace("\\", "/")
            new_content = change["new_content"]

            if filename not in normalized_codebase:
                raise ValueError(
                    f"Gemini tried to modify an unknown file: {filename}"
                )

            old_content = normalized_codebase[filename]

            diff = difflib.unified_diff(
                old_content.splitlines(),
                new_content.splitlines(),
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}",
                lineterm=""
            )

            file_diff = "\n".join(diff)

            if file_diff:
                diff_output += f"\n{'=' * 70}\n"
                diff_output += f"FILE: {filename}\n"
                diff_output += f"{'=' * 70}\n"
                diff_output += file_diff
                diff_output += "\n"

        if not diff_output:
            return "No changes were generated."

        return diff_output