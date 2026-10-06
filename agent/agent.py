from agent.file_reader import CodebaseReader
from agent.gemini_service import GeminiService
from agent.change_generator import ChangeGenerator
from agent.diff_generator import DiffGenerator
from agent.file_writer import FileWriter
from agent.test_runner import TestRunner


PROJECT_PATH = "sample_project"


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


def extract_relevant_files(analysis, available_files):

    relevant_files = []

    normalized_analysis = analysis.replace(
        "\\",
        "/"
    )

    for filename in available_files:

        filename = filename.replace(
            "\\",
            "/"
        )

        if filename in normalized_analysis:

            relevant_files.append(
                filename
            )

    return relevant_files


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

USER REQUEST:
{user_request}

EXISTING CODEBASE:
{codebase_context}

Analyze the user's coding request and the existing codebase.

Return exactly these sections:

## Task Understanding

Explain what the developer wants.

## Relevant Files

List ONLY files from the provided codebase that are relevant.

## Step-by-Step Plan

Give a clear implementation plan.

## Expected Changes

Explain what should be changed in each relevant file.

## Validation

Explain how the change should be tested.

IMPORTANT:
- Do not modify files.
- Do not pretend that changes have already been made.
- Do not include files that do not exist in the provided codebase.
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

    available_files = codebase.keys()

    relevant_files = extract_relevant_files(
        analysis,
        available_files
    )

    # If the developer explicitly asks for a test,
    # make sure an existing test file is included.

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

    if not relevant_files:

        raise ValueError(
            "No relevant files were identified."
        )

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

    # Make sure Gemini generated something.

    if not changes.get("changes"):

        raise ValueError(
            "The agent did not generate any code changes."
        )

    # If the user requested a test,
    # make sure Gemini generated a test-file change.

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