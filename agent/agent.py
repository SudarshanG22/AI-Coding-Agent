from agent.file_reader import CodebaseReader
from agent.gemini_service import GeminiService
from agent.change_generator import ChangeGenerator
from agent.diff_generator import DiffGenerator
from agent.file_writer import FileWriter
from agent.test_runner import TestRunner
from pathlib import Path


# ==================================================
# PROJECT PATH
# ==================================================

PROJECT_PATH = Path(__file__).resolve().parent.parent


# ==================================================
# BUILD CODEBASE CONTEXT
# ==================================================

def build_codebase_context(codebase):

    context = ""

    for filename, content in codebase.items():

        context += f"""
==================================================
FILE: {filename}
==================================================

{content}

"""

    return context


# ==================================================
# EXTRACT RELEVANT FILES
# ==================================================

def extract_relevant_files(
    analysis,
    available_files
):

    relevant_files = []

    normalized_analysis = analysis.replace(
        "\\",
        "/"
    )

    for filename in available_files:

        normalized_filename = filename.replace(
            "\\",
            "/"
        )

        if normalized_filename in normalized_analysis:

            relevant_files.append(
                filename
            )

    return relevant_files


# ==================================================
# EXTRACT FILES THAT MUST BE MODIFIED
# ==================================================

def extract_files_to_modify(
    analysis,
    available_files
):

    files_to_modify = []

    normalized_analysis = analysis.replace(
        "\\",
        "/"
    )

    lines = normalized_analysis.splitlines()

    for line in lines:

        line_lower = line.lower().strip()

        if not line_lower.startswith("- modify:"):

            continue

        filename = line.split(
            ":",
            1
        )[1].strip()

        for available_file in available_files:

            normalized_available = available_file.replace(
                "\\",
                "/"
            )

            if normalized_available.lower() == filename.lower():

                if available_file not in files_to_modify:

                    files_to_modify.append(
                        available_file
                    )

    return files_to_modify


# ==================================================
# STEP 1: ANALYZE TASK
# ==================================================

def analyze_task(user_request):

    reader = CodebaseReader(
        PROJECT_PATH
    )

    codebase = reader.read_codebase()

    codebase_context = build_codebase_context(
        codebase
    )

    prompt = f"""
You are an AI Coding Agent.

You are working on an existing software project.

==================================================
USER REQUEST
==================================================

{user_request}

==================================================
EXISTING CODEBASE
==================================================

{codebase_context}

==================================================
YOUR TASK
==================================================

Analyze the developer's request and the existing
codebase.

Return exactly these sections:

## Task Understanding

Explain what the developer wants.

## Relevant Files

For every relevant file, clearly classify whether
the file must be modified or only read for context.

Use EXACTLY this format:

- MODIFY: path/to/file.py
- READ ONLY: path/to/file.py

Only use files that actually exist in the provided
codebase.

## Step-by-Step Plan

Give a clear implementation plan.

## Expected Changes

Explain what should be changed in each file marked
MODIFY.

Do not say that changes have already been made.

## Validation

Explain how the requested change should be tested.

==================================================
IMPORTANT RULES
==================================================

1. Do not modify files.

2. Do not pretend that changes have already been made.

3. Do not invent files.

4. Do not include files that do not exist.

5. If a file needs to be changed to satisfy the
   developer request, mark it MODIFY.

6. If a file is only needed to understand the code,
   mark it READ ONLY.

7. If the developer explicitly names a file that
   needs to be updated, mark that file MODIFY.

8. Preserve the existing project structure.

9. Do not add unrelated requirements.

10. Do not refactor unrelated code.
"""

    gemini = GeminiService()

    analysis = gemini.generate_response(
        prompt
    )

    return analysis


# ==================================================
# STEP 2: GENERATE CODE CHANGES
# ==================================================

def generate_code_changes(
    user_request,
    analysis
):

    reader = CodebaseReader(
        PROJECT_PATH
    )

    codebase = reader.read_codebase()

    available_files = list(
        codebase.keys()
    )

    # ------------------------------------------------
    # Extract files identified by analysis
    # ------------------------------------------------

    relevant_files = extract_relevant_files(
        analysis,
        available_files
    )

    # ------------------------------------------------
    # Extract files explicitly marked MODIFY
    # ------------------------------------------------

    files_to_modify = extract_files_to_modify(
        analysis,
        available_files
    )

    # ------------------------------------------------
    # If analysis used MODIFY correctly,
    # use those files for code generation.
    # ------------------------------------------------

    if files_to_modify:

        relevant_files = files_to_modify

    # ------------------------------------------------
    # If developer explicitly requested tests,
    # make sure an existing test file is included.
    # ------------------------------------------------

    request_lower = user_request.lower()

    if "test" in request_lower:

        test_files = [
            filename
            for filename in available_files
            if "test" in filename.lower()
        ]

        for test_file in test_files:

            if test_file not in relevant_files:

                relevant_files.append(
                    test_file
                )

    # ------------------------------------------------
    # Safety check
    # ------------------------------------------------

    if not relevant_files:

        raise ValueError(
            "No relevant files were identified."
        )

    # ------------------------------------------------
    # Generate changes
    # ------------------------------------------------

    change_generator = ChangeGenerator()

    changes = change_generator.generate_changes(
        user_request,
        codebase,
        relevant_files
    )

    return changes


# ==================================================
# STEP 3: GENERATE DIFF
# ==================================================

def generate_code_diff(
    user_request,
    analysis
):

    reader = CodebaseReader(
        PROJECT_PATH
    )

    codebase = reader.read_codebase()

    changes = generate_code_changes(
        user_request,
        analysis
    )

    # ------------------------------------------------
    # Make sure Gemini generated changes
    # ------------------------------------------------

    if not changes.get("changes"):

        raise ValueError(
            "The agent did not generate any code changes."
        )

    # ------------------------------------------------
    # If user requested tests, make sure a test
    # file was modified.
    # ------------------------------------------------

    if "test" in user_request.lower():

        test_change_found = any(
            "test" in change.get(
                "file",
                ""
            ).lower()

            for change in changes["changes"]
        )

        if not test_change_found:

            raise ValueError(
                "The user requested a test, but the agent "
                "did not generate a test-file change."
            )

    # ------------------------------------------------
    # Generate diff
    # ------------------------------------------------

    diff_generator = DiffGenerator()

    diff = diff_generator.generate_diff(
        codebase,
        changes
    )

    return changes, diff


# ==================================================
# STEP 4: APPLY APPROVED CHANGES
# ==================================================

def apply_code_changes(changes):

    writer = FileWriter(
        PROJECT_PATH
    )

    applied_files = writer.apply_changes(
        changes
    )

    return applied_files


# ==================================================
# STEP 5: RUN TESTS
# ==================================================

def run_project_tests():

    runner = TestRunner(
        PROJECT_PATH
    )

    result = runner.run_tests()

    return result


# ==================================================
# CLI TEST
# ==================================================

if __name__ == "__main__":

    request = input(
        "Enter your coding task: "
    )

    result = analyze_task(
        request
    )

    print("\n")

    print(
        "=" * 70
    )

    print(
        "AI CODING AGENT"
    )

    print(
        "=" * 70
    )

    print(
        result
    )