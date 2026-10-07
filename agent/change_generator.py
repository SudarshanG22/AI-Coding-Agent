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
        user_request
    ):

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

        # Normalize Windows and Linux path separators
        normalized_allowed_files = {
            str(file).replace("\\", "/")
            for file in allowed_files
        }

        for index, change in enumerate(changes["changes"]):

            if not isinstance(change, dict):
                raise ValueError(
                    f"Change #{index + 1} is not a valid object."
                )

            required_fields = [
                "file",
                "reason",
                "new_content_lines"
            ]

            for field in required_fields:

                if field not in change:
                    raise ValueError(
                        f"Change #{index + 1} is missing required field: {field}"
                    )

            filename = str(change["file"]).replace("\\", "/")

            if filename not in normalized_allowed_files:
                raise ValueError(
                    f"Gemini attempted to modify an unauthorized file: {filename}"
                )

            if not isinstance(change["new_content_lines"], list):
                raise ValueError(
                    f"'new_content_lines' for {filename} must be a list."
                )

            for line in change["new_content_lines"]:

                if not isinstance(line, str):
                    raise ValueError(
                        f"Every line in {filename} must be a string."
                    )

            change["file"] = filename

            change["new_content"] = "\n".join(
                change.pop("new_content_lines")
            )

        # ====================================================
        # TEST REQUIREMENT VALIDATION
        # ====================================================

        request_lower = user_request.lower()

        test_requested = any(
            keyword in request_lower
            for keyword in [
                "test",
                "pytest",
                "unit test",
                "testing"
            ]
        )

        if test_requested:

            test_change_found = any(
                (
                    "test" in change["file"].lower()
                    or "tests/" in change["file"].lower()
                    or "/tests/" in change["file"].lower()
                )
                for change in changes["changes"]
            )

            if not test_change_found:
                raise ValueError(
                    "The user requested a test, but Gemini did not generate a test-file change."
                )

        return changes

    # ========================================================
    # GENERATE CHANGES
    # ========================================================

    def generate_changes(
        self,
        user_request,
        codebase,
        relevant_files
    ):

        selected_code = ""

        for filename in relevant_files:

            if filename in codebase:

                selected_code += f"""
==================================================
FILE: {filename}
==================================================

{codebase[filename]}

"""

        prompt = f"""
You are an AI Coding Agent working on an existing software project.

==================================================
DEVELOPER REQUEST
==================================================

{user_request}


==================================================
RELEVANT FILES
==================================================

{selected_code}


==================================================
YOUR JOB
==================================================

Generate ONLY the code changes required to satisfy the
developer's request.

The developer's request is the SOURCE OF TRUTH.

Do not add requirements that the developer did not request.


==================================================
VERY IMPORTANT SCOPE RULE
==================================================

You MUST follow the developer request exactly.

DO NOT invent additional requirements.

DO NOT add unrelated functionality.

DO NOT add unrelated validation.

DO NOT add unrelated API behavior.

DO NOT add unrelated edge cases.

DO NOT add tests for behavior that the developer did not request.

DO NOT refactor unrelated code.

DO NOT improve unrelated code.

DO NOT add extra features just because they may be considered
good programming practice.

For example:

If the developer asks:

"Add validation for empty or whitespace-only title and write
a pytest test."

Then implement ONLY:

1. Empty title validation.
2. Whitespace-only title validation.
3. Tests for those requested cases.

Do NOT additionally implement:

- Missing JSON validation.
- Invalid JSON validation.
- Missing title validation unless explicitly requested.
- Authentication.
- Authorization.
- Database changes.
- Extra API validation.
- Unrelated success tests.
- Other edge cases.

Stay within the exact scope of the request.


==================================================
TEST RULES
==================================================

If the developer requests tests:

1. Modify the existing appropriate test file.

2. Write tests ONLY for behavior explicitly requested.

3. Do not invent additional test cases.

4. Preserve existing tests unless they conflict with the
requested change.

5. Use the existing "client" pytest fixture for Flask API tests.

6. Tests must be runnable using pytest.

7. Do not create new fixtures unless absolutely necessary.

8. Do not test unrelated behavior.

9. Do not add a test simply because it is a common edge case.

10. The test must directly verify the requested behavior.


==================================================
CODE RULES
==================================================

1. Only modify files listed under RELEVANT FILES.

2. Never invent a new file.

3. Never modify unrelated files.

4. Preserve the existing project structure.

5. Include complete replacement content for every modified file.

6. Make the SMALLEST possible change required by the developer request.

7. Preserve every existing function, route, import, variable,
   database operation, and behavior that is unrelated to the request.

8. NEVER rewrite or simplify an entire file when only a small
   part of the file needs to change.

9. NEVER remove existing functionality unless the developer
   explicitly requested its removal.

10. Before returning each modified file, compare it mentally
    with the original file and make sure unrelated code remains
    unchanged.

11. If the requested change affects only one condition,
    expression, function, or test, modify only that part while
    preserving the rest of the file exactly.

12. Do not rename existing functions, classes, routes, variables,
    blueprints, or imports unless explicitly requested.


==================================================
EXISTING PROJECT INFORMATION
==================================================

The project contains an existing pytest fixture named
"client" inside:

tests/conftest.py

Use this fixture when testing Flask API endpoints.


==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

Use exactly this structure:

{{
    "changes": [
        {{
            "file": "routes.py",
            "reason": "Explain why this file changes",
            "new_content_lines": [
                "line 1",
                "line 2",
                "line 3"
            ]
        }}
    ]
}}


==================================================
NEW_CONTENT_LINES RULE
==================================================

"new_content_lines" MUST be an array.

Every array element MUST contain exactly ONE line.

Do not put multiple lines inside one array element.

Do not use Markdown.

Do not use ```json.

Do not add text before or after the JSON.


==================================================
FINAL SELF-CHECK
==================================================

Before returning the JSON, verify:

1. The JSON is valid.

2. Every requested code change is included.

3. Every requested test is included.

4. No unrelated functionality was added.

5. No unrelated tests were added.

6. Every modified file exists in RELEVANT FILES.

7. Existing tests are preserved.

8. All imports are present.

9. No undefined fixtures exist.

10. No undefined functions or variables exist.

11. Generated tests can run with pytest.

12. The implementation directly satisfies the developer request.

13. The implementation does NOT introduce additional
requirements that were not requested.
"""

        response = self.gemini.generate_json_response(prompt)

        try:

            cleaned_response = self._extract_json(response)

            changes = json.loads(cleaned_response)

        except json.JSONDecodeError as error:

            raise ValueError(
                "Gemini returned invalid JSON.\n\n"
                f"JSON parsing error: {error}\n\n"
                f"Gemini response:\n{response}"
            )

        validated_changes = self._validate_changes(
            changes,
            relevant_files,
            user_request
        )

        return validated_changes