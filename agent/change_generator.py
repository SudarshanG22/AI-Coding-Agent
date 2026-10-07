import json
import re

from agent.gemini_service import GeminiService


class ChangeGenerator:

    def __init__(self):
        self.gemini = GeminiService()

    # ========================================================
    # EXTRACT JSON
    # ========================================================

    def _extract_json(self, response):
        response = response.strip()

        match = re.search(
            r"```json\s*(.*?)\s*```",
            response,
            re.DOTALL | re.IGNORECASE
        )

        if match:
            response = match.group(1).strip()

        if response.startswith("```") and response.endswith("```"):
            lines = response.splitlines()

            if len(lines) >= 3:
                response = "\n".join(lines[1:-1]).strip()

        return response

    # ========================================================
    # VALIDATE GENERATED RESPONSE
    # ========================================================

    def _validate_changes(
        self,
        changes,
        allowed_files,
        user_request,
        create_files=None
    ):

        if create_files is None:
            create_files = []

        if not isinstance(changes, dict):
            raise ValueError(
                "Gemini response must be a JSON object."
            )

        if "changes" not in changes:
            raise ValueError(
                "Gemini response does not contain a 'changes' field."
            )

        if not isinstance(changes["changes"], list):
            raise ValueError(
                "'changes' must be a list."
            )

        if not changes["changes"]:
            raise ValueError(
                "Gemini did not generate any code changes."
            )

        # Normalize existing files
        normalized_allowed_files = {
            str(file).replace("\\", "/").strip()
            for file in allowed_files
        }

        # Normalize explicitly detected new files
        normalized_create_files = {
            str(file).replace("\\", "/").strip()
            for file in create_files
        }

        for index, change in enumerate(changes["changes"]):

            if not isinstance(change, dict):
                raise ValueError(
                    f"Change #{index + 1} is not a valid object."
                )

            # ------------------------------------------------
            # Required fields
            # ------------------------------------------------

            if "file" not in change:
                raise ValueError(
                    f"Change #{index + 1} is missing required field: file"
                )

            if "reason" not in change:
                raise ValueError(
                    f"Change #{index + 1} is missing required field: reason"
                )

            if "new_content_lines" not in change:

                # Support Gemini returning new_content directly
                if "new_content" in change:
                    content = change["new_content"]

                    if not isinstance(content, str):
                        raise ValueError(
                            f"'new_content' for change #{index + 1} "
                            "must be a string."
                        )

                    change["new_content_lines"] = content.splitlines()

                else:
                    raise ValueError(
                        f"Change #{index + 1} is missing "
                        "required field: new_content_lines"
                    )

            # ------------------------------------------------
            # Normalize filename
            # ------------------------------------------------

            filename = str(change["file"]).replace("\\", "/").strip()

            if not filename:
                raise ValueError(
                    f"Change #{index + 1} contains an empty filename."
                )

            # ------------------------------------------------
            # Determine action
            # ------------------------------------------------

            requested_action = str(
                change.get("action", "")
            ).upper().strip()

            # =================================================
            # IMPORTANT FIX
            #
            # If Gemini does not provide CREATE but the file
            # is not an existing file, automatically treat it
            # as CREATE.
            #
            # This prevents:
            #
            # Gemini tried to modify unknown file: validation.py
            #
            # =================================================

            if filename in normalized_allowed_files:

                # Existing file must be MODIFY
                action = "MODIFY"

            else:

                # File does not exist in current codebase.
                # Therefore it must be a CREATE operation.
                action = "CREATE"

            # If Gemini explicitly says MODIFY for a new file,
            # automatically correct it to CREATE.
            if requested_action == "CREATE":
                action = "CREATE"

            elif requested_action == "MODIFY":
                if filename in normalized_allowed_files:
                    action = "MODIFY"
                else:
                    action = "CREATE"

            # ------------------------------------------------
            # Validate CREATE path
            # ------------------------------------------------

            if action == "CREATE":

                # Prevent absolute paths
                if filename.startswith("/"):
                    raise ValueError(
                        f"Invalid new file path: {filename}"
                    )

                # Windows absolute path
                if len(filename) >= 2 and filename[1] == ":":
                    raise ValueError(
                        f"Invalid new file path: {filename}"
                    )

                # Prevent path traversal
                path_parts = filename.split("/")

                if ".." in path_parts:
                    raise ValueError(
                        f"Invalid new file path: {filename}"
                    )

            # ------------------------------------------------
            # Validate content
            # ------------------------------------------------

            if not isinstance(change["new_content_lines"], list):
                raise ValueError(
                    f"'new_content_lines' for {filename} "
                    "must be a list."
                )

            for line in change["new_content_lines"]:

                if not isinstance(line, str):
                    raise ValueError(
                        f"Every line in {filename} must be a string."
                    )

            # ------------------------------------------------
            # Save normalized change
            # ------------------------------------------------

            change["file"] = filename
            change["action"] = action

            change["new_content"] = "\n".join(
                change.pop("new_content_lines")
            )

        # Test-file validation is handled in agent.py.
        #
        # Do not check "test" in user_request here because
        # phrases such as:
        #
        # "modify tests only if required"
        #
        # do not mean that tests were explicitly requested.

        return changes

    # ========================================================
    # GENERATE CHANGES
    # ========================================================

    def generate_changes(
        self,
        user_request,
        codebase,
        relevant_files,
        create_files=None
    ):

        if create_files is None:
            create_files = []

        # ----------------------------------------------------
        # Build selected codebase
        # ----------------------------------------------------

        selected_code = ""

        for filename in relevant_files:

            if filename in codebase:

                selected_code += f"""
==================================================
FILE: {filename}
==================================================

{codebase[filename]}

"""

        # ----------------------------------------------------
        # Build information about possible new files
        # ----------------------------------------------------

        allowed_create_files = []

        for filename in create_files:

            normalized = str(filename).replace(
                "\\",
                "/"
            ).strip()

            if (
                normalized
                and normalized not in allowed_create_files
            ):
                allowed_create_files.append(normalized)

        create_section = "\n".join(
            f"- CREATE: {filename}"
            for filename in allowed_create_files
        )

        if not create_section:
            create_section = "No specific new file was detected."

        # ----------------------------------------------------
        # Gemini prompt
        # ----------------------------------------------------

        prompt = f"""
You are an AI Coding Agent working on an existing software project.

==================================================
DEVELOPER REQUEST
==================================================

{user_request}

==================================================
RELEVANT EXISTING FILES
==================================================

{selected_code}

==================================================
POSSIBLE NEW FILES
==================================================

{create_section}

==================================================
YOUR JOB
==================================================

Generate ONLY the code changes required to satisfy the
developer's request.

The developer's request is the SOURCE OF TRUTH.

Do not add requirements that the developer did not request.

==================================================
IMPORTANT SCOPE RULE
==================================================

Follow the developer request exactly.

DO NOT invent unrelated requirements.

DO NOT add unrelated functionality.

DO NOT add unrelated validation.

DO NOT add unrelated API behavior.

DO NOT add unrelated edge cases.

DO NOT refactor unrelated code.

DO NOT improve unrelated code.

DO NOT add extra features.

Make the SMALLEST possible change.

==================================================
FILE RULES
==================================================

1. Existing files should be returned as MODIFY.

2. A file that does not already exist should be returned as CREATE.

3. If a shared helper module is required by the developer
   request, create it.

4. Do not create unrelated files.

5. Preserve all existing functionality.

6. Include complete content for every modified file.

7. Include complete content for every newly created file.

8. Do not remove existing functions.

9. Do not rename existing functions.

10. Do not remove existing routes.

11. Do not remove existing database operations.

12. Preserve unrelated imports and functionality.

==================================================
TEST RULES
==================================================

If the developer explicitly requests tests:

1. Modify the existing appropriate test file.

2. Write tests ONLY for the requested behavior.

3. Preserve existing tests.

4. Use the existing "client" pytest fixture
   for Flask API tests.

5. Tests must be runnable using pytest.

If the developer says tests should be modified
"only if required", do NOT automatically modify tests.

==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "changes": [
        {{
            "action": "MODIFY",
            "file": "routes.py",
            "reason": "Explain why this file changes",
            "new_content_lines": [
                "line 1",
                "line 2"
            ]
        }},
        {{
            "action": "CREATE",
            "file": "validation.py",
            "reason": "Explain why this new file is required",
            "new_content_lines": [
                "line 1",
                "line 2"
            ]
        }}
    ]
}}

The "action" must be either:

MODIFY

or

CREATE

==================================================
NEW_CONTENT_LINES RULE
==================================================

"new_content_lines" MUST be an array.

Every array element must contain exactly ONE line.

Do not put multiple lines inside one array element.

Do not use Markdown.

Do not use ```json.

Do not add text before or after the JSON.

==================================================
FINAL SELF-CHECK
==================================================

Before returning JSON verify:

1. JSON is valid.

2. Every requested change is included.

3. No unrelated functionality was added.

4. Existing functionality is preserved.

5. Every existing file is marked MODIFY.

6. Every new file is marked CREATE.

7. All imports are present.

8. No undefined functions exist.

9. No undefined variables exist.

10. Test changes are included only when required.

11. The implementation directly satisfies the developer request.
"""

        # ----------------------------------------------------
        # Call Gemini
        # ----------------------------------------------------

        response = self.gemini.generate_json_response(prompt)

        # ----------------------------------------------------
        # Parse JSON
        # ----------------------------------------------------

        try:

            cleaned_response = self._extract_json(
                response
            )

            changes = json.loads(
                cleaned_response
            )

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON.\n\n"
                f"JSON parsing error: {error}\n\n"
                f"Gemini response:\n{response}"
            )

        # ----------------------------------------------------
        # Validate changes
        # ----------------------------------------------------

        validated_changes = self._validate_changes(
            changes,
            relevant_files,
            user_request,
            create_files=allowed_create_files
        )

        return validated_changes