from pathlib import Path


from agent.file_reader import CodebaseReader
from agent.gemini_service import GeminiService
from agent.change_generator import ChangeGenerator
from agent.diff_generator import DiffGenerator
from agent.file_writer import FileWriter
from agent.test_runner import TestRunner


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
# NORMALIZE ANALYSIS TEXT
# ==================================================

def normalize_analysis_text(text):

    return (
        text
        .replace("\\", "/")
        .replace("**", "")
        .replace("`", "")
        .strip()
    )


# ==================================================
# EXTRACT RELEVANT FILES
# ==================================================

def extract_relevant_files(
    analysis,
    available_files
):

    relevant_files = []

    normalized_analysis = normalize_analysis_text(
        analysis
    ).lower()

    for filename in available_files:

        normalized_filename = (
            filename
            .replace("\\", "/")
            .lower()
            .strip()
        )

        if normalized_filename in normalized_analysis:

            if filename not in relevant_files:

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

    normalized_analysis = normalize_analysis_text(
        analysis
    )

    lines = normalized_analysis.splitlines()

    for line in lines:

        line_clean = line.strip()

        lower_line = line_clean.lower()

        # ------------------------------------------------
        # Find MODIFY anywhere in the line.
        #
        # Supports:
        #
        # MODIFY: login_demo.py
        # - MODIFY: login_demo.py
        # * MODIFY: login_demo.py
        # 1. MODIFY: login_demo.py
        # ------------------------------------------------

        modify_position = lower_line.find(
            "modify:"
        )

        if modify_position == -1:

            continue

        filename = line_clean[
            modify_position + len("modify:")
        ].strip()

        # Remove Markdown/list characters
        filename = filename.strip(
            " -*•\t"
        ).strip()

        # ------------------------------------------------
        # Match against actual project files
        # ------------------------------------------------

        for available_file in available_files:

            normalized_available = (
                available_file
                .replace("\\", "/")
                .lower()
                .strip()
            )

            normalized_candidate = (
                filename
                .replace("\\", "/")
                .lower()
                .strip("`")
                .strip()
            )

            # Exact match
            if (
                normalized_candidate
                == normalized_available
            ):

                if available_file not in files_to_modify:

                    files_to_modify.append(
                        available_file
                    )

                break

            # Filename followed by explanation
            #
            # Example:
            #
            # MODIFY: login_demo.py - update validation
            #
            if (
                normalized_candidate.startswith(
                    normalized_available + " "
                )
                or normalized_candidate.startswith(
                    normalized_available + "-"
                )
            ):

                if available_file not in files_to_modify:

                    files_to_modify.append(
                        available_file
                    )

                break

    return files_to_modify


# ==================================================
# EXTRACT FILES THAT MAY BE CREATED
# ==================================================

def extract_files_to_create(
    analysis,
    available_files
):

    files_to_create = []

    normalized_analysis = normalize_analysis_text(
        analysis
    )

    lines = normalized_analysis.splitlines()

    for line in lines:

        line_clean = line.strip()

        lower_line = line_clean.lower()

        # ------------------------------------------------
        # Supported formats:
        #
        # CREATE: validation.py
        # - CREATE: validation.py
        # * CREATE: validation.py
        # 1. CREATE: validation.py
        # CREATE - validation.py
        # CREATE validation.py
        # ------------------------------------------------

        filename = None

        # CREATE:
        create_position = lower_line.find(
            "create:"
        )

        if create_position != -1:

            filename = line_clean[
                create_position + len("create:")
            ].strip()

        # CREATE -
        elif "create -" in lower_line:

            create_position = lower_line.find(
                "create -"
            )

            filename = line_clean[
                create_position + len("create -"):
            ].strip()

        # CREATE filename
        elif lower_line.startswith(
            "create "
        ):

            filename = line_clean[
                len("create "):
            ].strip()

        if not filename:

            continue

        # Remove Markdown/list characters
        filename = filename.strip(
            " -*•\t"
        ).strip()

        # ------------------------------------------------
        # Match against existing files.
        #
        # CREATE must never refer to an existing file.
        # ------------------------------------------------

        already_exists = False

        normalized_candidate = (
            filename
            .replace("\\", "/")
            .lower()
            .strip("`")
            .strip()
        )

        for available_file in available_files:

            normalized_available = (
                available_file
                .replace("\\", "/")
                .lower()
                .strip()
            )

            if (
                normalized_candidate
                == normalized_available
            ):

                already_exists = True
                break

        if already_exists:

            continue

        # ------------------------------------------------
        # Security validation
        # ------------------------------------------------

        candidate_path = Path(
            filename
        )

        # Do not allow absolute paths
        if candidate_path.is_absolute():

            continue

        # Do not allow path traversal
        if ".." in candidate_path.parts:

            continue

        # ------------------------------------------------
        # Add authorized CREATE file
        # ------------------------------------------------

        if filename not in files_to_create:

            files_to_create.append(
                filename
            )

    # ----------------------------------------------------
    # Fallback for the shared-validation requirement.
    #
    # If Gemini clearly understands that validation.py
    # is required but formatting prevented the parser
    # from detecting CREATE:, authorize it safely.
    # ----------------------------------------------------

    analysis_lower = normalized_analysis.lower()

    if (
        "validation.py" in analysis_lower
        and "shared" in analysis_lower
        and "validation" in analysis_lower
    ):

        validation_exists = any(

            Path(file).name.lower()
            == "validation.py"

            for file in available_files

        )

        if not validation_exists:

            if "validation.py" not in files_to_create:

                files_to_create.append(
                    "validation.py"
                )

    return files_to_create


# ==================================================
# CHECK WHETHER USER EXPLICITLY REQUESTED TEST CHANGES
# ==================================================

def user_explicitly_requests_test_changes(
    user_request
):

    request = user_request.lower().strip()

    # ------------------------------------------------
    # Conditional test instructions do NOT mean that
    # the user explicitly requested test modification.
    # ------------------------------------------------

    conditional_test_phrases = [

        "only if",
        "if required",
        "if necessary",
        "if needed",
        "if implementation requires",
        "if the implementation requires",
        "only when required",
        "only when necessary",
        "only when needed",

    ]

    has_conditional_test_instruction = (

        "test" in request

        and any(
            phrase in request
            for phrase in conditional_test_phrases
        )

    )

    if has_conditional_test_instruction:

        return False

    # ------------------------------------------------
    # Explicit test-change requests
    # ------------------------------------------------

    test_change_phrases = [

        "add test",
        "add tests",

        "create test",
        "create tests",

        "write test",
        "write tests",

        "update test",
        "update tests",

        "modify test",
        "modify tests",

        "change test",
        "change tests",

        "fix test",
        "fix tests",

        "add pytest",
        "create pytest",
        "write pytest",

        "update pytest",
        "modify pytest",
        "change pytest",
        "fix pytest"

    ]

    return any(

        phrase in request

        for phrase in test_change_phrases

    )


# ==================================================
# STEP 1: ANALYZE TASK
# ==================================================

def analyze_task(
    user_request
):

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

List every relevant existing file.

For existing files use:

- MODIFY: path/to/file.py
- READ ONLY: path/to/file.py

If the implementation genuinely requires a new
file that does not currently exist, use:

- CREATE: path/to/new_file.py

A CREATE file must be genuinely necessary.

Do not create files just for convenience.

## Step-by-Step Plan

Give a clear implementation plan.

## Expected Changes

Explain what should change in every MODIFY file.

For every CREATE file, explain why the new file
is required and what it should contain.

## Validation

Explain how the requested change should be tested.

==================================================
IMPORTANT RULES
==================================================

1. Do not modify files during analysis.

2. Do not pretend changes have already been made.

3. Do not invent unnecessary files.

4. Existing files must be classified as MODIFY
   or READ ONLY.

5. A genuinely required new file may be classified
   as CREATE.

6. Preserve the existing project structure.

7. Do not add unrelated requirements.

8. Do not refactor unrelated code.

9. Make the smallest possible implementation change.

10. Preserve unrelated existing functionality.

11. Do not remove existing routes, functions,
    classes, imports, variables, or UI.

12. Filenames for existing files must match the
    actual codebase filenames.

13. Use the exact words MODIFY, CREATE, and
    READ ONLY for file classification.

14. If the developer asks for logic to be shared
    between multiple components and no suitable
    shared module exists, identify a small dedicated
    shared module as CREATE.

15. Do not put shared logic inside one consumer
    module when another consumer also needs it.

16. Do not make a Streamlit UI depend on a Flask
    route module merely to reuse a shared helper.

17. Do not use localhost HTTP requests when the
    developer explicitly says they are not required.
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
    # Extract all existing filenames mentioned
    # ------------------------------------------------

    relevant_files = extract_relevant_files(
        analysis,
        available_files
    )

    # ------------------------------------------------
    # Extract explicit MODIFY files
    # ------------------------------------------------

    files_to_modify = extract_files_to_modify(
        analysis,
        available_files
    )

    if files_to_modify:

        relevant_files = files_to_modify

    # ------------------------------------------------
    # Extract authorized CREATE files
    # ------------------------------------------------

    files_to_create = extract_files_to_create(
        analysis,
        available_files
    )

    # ------------------------------------------------
    # Include existing test files only when the user
    # explicitly requested test modifications.
    # ------------------------------------------------

    if user_explicitly_requests_test_changes(
        user_request
    ):

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
    # SAFETY CHECK
    # ------------------------------------------------

    if (
        not relevant_files
        and not files_to_create
    ):

        raise ValueError(
            "No relevant files were identified. "
            "The analysis did not return any "
            "recognized MODIFY, READ ONLY, or CREATE "
            "files."
        )

    # ------------------------------------------------
    # Generate changes
    # ------------------------------------------------

    change_generator = ChangeGenerator()

    changes = change_generator.generate_changes(

        user_request,

        codebase,

        relevant_files,

        create_files=files_to_create

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

    if not changes.get(
        "changes"
    ):

        raise ValueError(
            "The agent did not generate any code changes."
        )

    # ------------------------------------------------
    # If the developer explicitly requested test
    # changes, make sure a test file was modified.
    # ------------------------------------------------

    if user_explicitly_requests_test_changes(
        user_request
    ):

        test_change_found = any(

            "test" in change.get(
                "file",
                ""
            ).lower()

            for change in changes[
                "changes"
            ]

        )

        if not test_change_found:

            raise ValueError(
                "The user explicitly requested test changes, "
                "but the agent did not generate a test-file change."
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
# STEP 4: APPLY CODE CHANGES
# ==================================================

def apply_code_changes(
    changes
):

    writer = FileWriter(
        PROJECT_PATH
    )

    applied_files = writer.apply_changes(
        changes
    )

    return applied_files


# ==================================================
# STEP 5: RUN PROJECT TESTS
# ==================================================

def run_project_tests():

    runner = TestRunner(
        PROJECT_PATH
    )

    result = runner.run_tests()

    return result


# ==================================================
# COMMAND LINE MODE
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