import streamlit as st
from pathlib import Path

from agent.agent import (
    analyze_task,
    generate_code_diff,
    apply_code_changes,
    run_project_tests
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="AI Coding Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# BACKGROUND IMAGE
# ============================================================

BACKGROUND_IMAGE = (
    Path(__file__).resolve().parent
    / "assets"
    / "ai_coding_background.png"
)


# ============================================================
# CUSTOM CSS
# ============================================================

if BACKGROUND_IMAGE.exists():

    import base64

    with open(BACKGROUND_IMAGE, "rb") as image_file:
        encoded_image = base64.b64encode(
            image_file.read()
        ).decode()

    background_css = f"""
    <style>

    /* ========================================================
       MAIN APP BACKGROUND
       ======================================================== */

    .stApp {{
        background-image:
            linear-gradient(
                rgba(5, 8, 18, 0.86),
                rgba(5, 8, 18, 0.94)
            ),
            url("data:image/png;base64,{encoded_image}");

        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}


    /* ========================================================
       SIDEBAR BACKGROUND
       ======================================================== */

    [data-testid="stSidebar"] {{
        background-image:
            linear-gradient(
                rgba(5, 8, 18, 0.91),
                rgba(5, 8, 18, 0.96)
            ),
            url("data:image/png;base64,{encoded_image}");

        background-size: cover;
        background-position: center;
    }}


    /* ========================================================
       MAIN CONTAINER
       ======================================================== */

    .block-container {{
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }}


    /* ========================================================
       HEADER
       ======================================================== */

    .hero-card {{
        padding: 28px 30px;
        border-radius: 18px;

        border: 1px solid rgba(120, 170, 255, 0.25);

        background:
            linear-gradient(
                135deg,
                rgba(20, 30, 55, 0.72),
                rgba(10, 15, 30, 0.58)
            );

        backdrop-filter: blur(12px);

        box-shadow:
            0 8px 35px rgba(0, 0, 0, 0.35);

        margin-bottom: 25px;
    }}

    .hero-title {{
        font-size: 36px;
        font-weight: 750;
        margin-bottom: 8px;
    }}

    .hero-subtitle {{
        font-size: 16px;
        opacity: 0.78;
        line-height: 1.6;
        margin-bottom: 16px;
    }}

    .status-badge {{
        display: inline-block;

        padding: 6px 13px;

        border-radius: 20px;

        border: 1px solid rgba(46, 204, 113, 0.5);

        background: rgba(46, 204, 113, 0.08);

        font-size: 13px;
        font-weight: 600;
    }}


    /* ========================================================
       SECTION TITLES
       ======================================================== */

    .section-title {{
        font-size: 22px;
        font-weight: 650;

        margin-top: 22px;
        margin-bottom: 10px;
    }}


    /* ========================================================
       WORKFLOW CARDS
       ======================================================== */

    .workflow-card {{
        text-align: center;

        padding: 16px 8px;

        border-radius: 13px;

        border: 1px solid rgba(120, 170, 255, 0.22);

        background:
            linear-gradient(
                135deg,
                rgba(25, 35, 60, 0.65),
                rgba(10, 15, 30, 0.55)
            );

        backdrop-filter: blur(8px);

        box-shadow:
            0 5px 20px rgba(0, 0, 0, 0.20);
    }}

    .workflow-icon {{
        font-size: 25px;
    }}

    .workflow-name {{
        font-weight: 650;
        margin-top: 5px;
    }}

    .workflow-description {{
        font-size: 12px;
        opacity: 0.65;
    }}


    /* ========================================================
       SIDEBAR
       ======================================================== */

    .sidebar-card {{
        padding: 14px;

        border-radius: 12px;

        border: 1px solid rgba(120, 170, 255, 0.22);

        background:
            rgba(10, 15, 30, 0.58);

        backdrop-filter: blur(10px);

        margin-bottom: 12px;
    }}


    /* ========================================================
       FILE TAG
       ======================================================== */

    .file-tag {{
        display: inline-block;

        padding: 5px 9px;

        margin: 3px 2px;

        border-radius: 7px;

        border: 1px solid rgba(120, 170, 255, 0.20);

        background: rgba(20, 30, 50, 0.50);

        font-size: 12px;
    }}


    /* ========================================================
       TASK AREA
       ======================================================== */

    [data-testid="stTextArea"] textarea {{
        background: rgba(10, 15, 30, 0.68) !important;

        border: 1px solid rgba(120, 170, 255, 0.25) !important;

        border-radius: 12px !important;

        backdrop-filter: blur(8px) !important;
    }}


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {{
        border-radius: 10px;

        font-weight: 600;

        transition:
            transform 0.15s ease,
            box-shadow 0.15s ease;
    }}

    .stButton > button:hover {{
        transform: translateY(-1px);

        box-shadow:
            0 5px 18px rgba(0, 0, 0, 0.25);
    }}


    /* ========================================================
       CODE / DIFF BOX
       ======================================================== */

    [data-testid="stCode"] {{
        border-radius: 12px;
    }}


    /* ========================================================
       FOOTER
       ======================================================== */

    .footer-text {{
        text-align: center;

        opacity: 0.5;

        font-size: 12px;

        margin-top: 35px;
    }}


    /* ========================================================
       HIDE STREAMLIT BRANDING
       ======================================================== */

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}

    </style>
    """

    st.markdown(
        background_css,
        unsafe_allow_html=True
    )

else:

    st.warning(
        "⚠️ Background image not found. "
        "Expected: assets/ai_coding_background.png"
    )


# ============================================================
# SESSION STATE
# ============================================================

if "pending_changes" not in st.session_state:
    st.session_state.pending_changes = None

if "changes_generated" not in st.session_state:
    st.session_state.changes_generated = False

if "changes_applied" not in st.session_state:
    st.session_state.changes_applied = False

if "analysis" not in st.session_state:
    st.session_state.analysis = None

if "diff" not in st.session_state:
    st.session_state.diff = None

if "test_result" not in st.session_state:
    st.session_state.test_result = None

if "task_input" not in st.session_state:
    st.session_state.task_input = ""


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown("## 🤖 AI Coding Agent")

    st.markdown(
        """
        <div class="sidebar-card">
            <b>📂 Project</b><br>
            Sample Flask Project
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📁 Project Files")

    project_files = [
        "app.py",
        "database.py",
        "models.py",
        "routes.py",
        "tests/test_tasks.py"
    ]

    for file in project_files:

        st.markdown(
            f'<span class="file-tag">📄 {file}</span>',
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.markdown("### ⚙️ Agent Workflow")

    st.write("🧠 Understand task")
    st.write("📂 Find relevant files")
    st.write("📝 Generate changes")
    st.write("👤 User approval")
    st.write("✍️ Apply changes")
    st.write("🧪 Run tests")

    st.markdown("---")

    st.markdown("### 🟢 System Status")

    st.success("Agent Ready")

    st.caption(
        "Gemini-powered coding assistant"
    )

    st.markdown("---")

    if st.button(
        "🗑️ Clear Current Task",
        use_container_width=True
    ):

        st.session_state.pending_changes = None
        st.session_state.changes_generated = False
        st.session_state.changes_applied = False
        st.session_state.analysis = None
        st.session_state.diff = None
        st.session_state.test_result = None
        st.session_state.task_input = ""

        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="hero-card">
<div class="hero-title">🤖 AI Coding Agent</div>
<div class="hero-subtitle">An AI-powered coding assistant that understands your codebase, identifies relevant files, proposes code changes, and validates them with automated tests.</div>
<span class="status-badge">🟢 Agent Ready</span>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# WORKFLOW
# ============================================================

st.markdown(
    '<div class="section-title">🔄 Agent Workflow</div>',
    unsafe_allow_html=True
)

col1, arrow1, col2, arrow2, col3, arrow3, col4, arrow4, col5 = st.columns(
    [2, 0.35, 2, 0.35, 2, 0.35, 2, 0.35, 2]
)


with col1:

    st.markdown(
        """
<div class="workflow-card">
<div class="workflow-icon">🧠</div>
<div class="workflow-name">Understand</div>
<div class="workflow-description">Analyze request</div>
</div>
""",
        unsafe_allow_html=True
    )


with arrow1:

    st.markdown(
        "<br>➡️",
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        """
<div class="workflow-card">
<div class="workflow-icon">📂</div>
<div class="workflow-name">Inspect</div>
<div class="workflow-description">Find files</div>
</div>
""",
        unsafe_allow_html=True
    )


with arrow2:

    st.markdown(
        "<br>➡️",
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        """
<div class="workflow-card">
<div class="workflow-icon">📝</div>
<div class="workflow-name">Generate</div>
<div class="workflow-description">Create changes</div>
</div>
""",
        unsafe_allow_html=True
    )


with arrow3:

    st.markdown(
        "<br>➡️",
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        """
<div class="workflow-card">
<div class="workflow-icon">👤</div>
<div class="workflow-name">Approve</div>
<div class="workflow-description">Review changes</div>
</div>
""",
        unsafe_allow_html=True
    )


with arrow4:

    st.markdown(
        "<br>➡️",
        unsafe_allow_html=True
    )


with col5:

    st.markdown(
        """
<div class="workflow-card">
<div class="workflow-icon">🧪</div>
<div class="workflow-name">Validate</div>
<div class="workflow-description">Run tests</div>
</div>
""",
        unsafe_allow_html=True
    )


# ============================================================
# TASK INPUT
# ============================================================

st.markdown(
    '<div class="section-title">💬 Describe Your Coding Task</div>',
    unsafe_allow_html=True
)

st.caption(
    "Tell the AI agent what you want to change in the existing project."
)


user_request = st.text_area(
    "Coding task",
    value=st.session_state.task_input,
    placeholder=(
        "Example:\n"
        "Add validation so that task title cannot be empty "
        "and create a test for it."
    ),
    height=130,
    label_visibility="collapsed"
)

st.session_state.task_input = user_request


# ============================================================
# EXAMPLE TASKS
# ============================================================

st.markdown("#### 💡 Example Tasks")

example_col1, example_col2, example_col3 = st.columns(3)


with example_col1:

    if st.button(
        "Validate task title",
        use_container_width=True
    ):

        st.session_state.task_input = (
            "Add validation so that task title cannot be empty "
            "and create a test for it."
        )

        st.rerun()


with example_col2:

    if st.button(
        "Validate task status",
        use_container_width=True
    ):

        st.session_state.task_input = (
            "Add validation to ensure task status is either "
            "pending or completed and create a test for it."
        )

        st.rerun()


with example_col3:

    if st.button(
        "Improve API response",
        use_container_width=True
    ):

        st.session_state.task_input = (
            "Improve the task creation API response and create "
            "a test for the updated response."
        )

        st.rerun()


# ============================================================
# RUN AGENT
# ============================================================

st.markdown("")

run_agent = st.button(
    "🚀 Analyze & Generate Changes",
    type="primary",
    use_container_width=True
)


if run_agent:

    if not user_request.strip():

        st.warning(
            "⚠️ Please describe a coding task first."
        )

    else:

        try:

            # ------------------------------------------------
            # STEP 1 — ANALYZE CODEBASE
            # ------------------------------------------------

            with st.spinner(
                "🧠 AI agent is analyzing your codebase..."
            ):

                analysis = analyze_task(
                    user_request
                )

            st.session_state.analysis = analysis

            st.success(
                "✅ Codebase analysis completed."
            )

            st.markdown(
                '<div class="section-title">🧠 Agent Analysis</div>',
                unsafe_allow_html=True
            )

            with st.container(border=True):

                st.markdown(
                    analysis
                )


            # ------------------------------------------------
            # STEP 2 — GENERATE CODE CHANGES
            # ------------------------------------------------

            with st.spinner(
                "📝 AI agent is generating code changes..."
            ):

                changes, diff = generate_code_diff(
                    user_request,
                    analysis
                )

            st.session_state.pending_changes = changes
            st.session_state.diff = diff
            st.session_state.changes_generated = True
            st.session_state.changes_applied = False

            st.success(
                "✅ Proposed changes generated successfully."
            )


            # ------------------------------------------------
            # STEP 3 — SHOW DIFF
            # ------------------------------------------------

            st.markdown(
                '<div class="section-title">📝 Proposed Changes</div>',
                unsafe_allow_html=True
            )

            with st.container(border=True):

                st.caption(
                    "Review the generated changes before approving them."
                )

                st.code(
                    diff,
                    language="diff"
                )


        except Exception as e:

            error_message = str(e)

            if (
                "429" in error_message
                or "RESOURCE_EXHAUSTED" in error_message
            ):

                st.error(
                    "⚠️ Gemini API quota has been exhausted."
                )

                st.info(
                    "The Gemini project has reached its current "
                    "API quota. Please wait for the quota reset "
                    "before running the AI agent again."
                )

            else:

                st.error(
                    f"❌ Agent error: {error_message}"
                )


# ============================================================
# APPROVAL SECTION
# ============================================================

if st.session_state.changes_generated:

    st.markdown("---")

    st.markdown(
        '<div class="section-title">👤 Review & Approve</div>',
        unsafe_allow_html=True
    )

    st.warning(
        "⚠️ Review the proposed code changes carefully before applying them."
    )

    approve = st.button(
        "✅ Approve & Apply Changes",
        type="primary",
        use_container_width=True
    )


    if approve:

        try:

            # ------------------------------------------------
            # APPLY CHANGES
            # ------------------------------------------------

            with st.spinner(
                "✍️ Applying approved changes..."
            ):

                applied_files = apply_code_changes(
                    st.session_state.pending_changes
                )

            st.session_state.changes_applied = True

            st.success(
                "✅ Changes applied successfully!"
            )


            # ------------------------------------------------
            # MODIFIED FILES
            # ------------------------------------------------

            st.markdown(
                '<div class="section-title">📁 Modified Files</div>',
                unsafe_allow_html=True
            )

            for filename in applied_files:

                st.success(
                    f"📄 {filename}"
                )


            # ------------------------------------------------
            # RUN TESTS
            # ------------------------------------------------

            st.markdown(
                '<div class="section-title">🧪 Validation</div>',
                unsafe_allow_html=True
            )

            with st.spinner(
                "🧪 Running automated tests..."
            ):

                test_result = run_project_tests()

            st.session_state.test_result = test_result


            if test_result["success"]:

                st.success(
                    "🎉 All tests passed successfully!"
                )

            else:

                st.error(
                    "❌ Some tests failed."
                )


            # ------------------------------------------------
            # TEST OUTPUT
            # ------------------------------------------------

            with st.expander(
                "📊 View Test Output",
                expanded=True
            ):

                if test_result["stdout"]:

                    st.code(
                        test_result["stdout"],
                        language="text"
                    )

                if test_result["stderr"]:

                    st.markdown(
                        "#### ⚠️ Test Errors"
                    )

                    st.code(
                        test_result["stderr"],
                        language="text"
                    )


        except Exception as e:

            st.error(
                f"❌ Failed to apply changes or run tests: {e}"
            )


# ============================================================
# FINAL STATUS
# ============================================================

if st.session_state.changes_applied:

    st.markdown("---")

    st.success(
        "🎯 Agent task completed — changes were applied "
        "and automated validation was executed."
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="footer-text">
AI Coding Agent • Gemini • Streamlit • Automated Testing
</div>
""",
    unsafe_allow_html=True
)