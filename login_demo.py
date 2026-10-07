import streamlit as st
import re
from validation import validate_username


def login_demo():
    st.markdown(
        """
        <div style="
            max-width: 520px;
            margin: 70px auto 20px auto;
            text-align: center;
        ">
            <div style="font-size: 48px;">🔐</div>
            <h1>Login Demo</h1>
            <p style="opacity: 0.7;">
                Test the username validation implemented by the AI Coding Agent.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    with st.container(border=True):

        username = st.text_input(
            "Username",
            placeholder="Enter username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter password"
        )

        login_button = st.button(
            "🔐 Login",
            type="primary",
            use_container_width=True
        )

    if login_button:

        if not password:
            st.error("❌ Username and password are required.")
        else:
            is_valid, error_message = validate_username(username)
            if not is_valid:
                st.error(f"❌ {error_message}")
            else:
                st.success(
                    f"✅ Login successful! Welcome, {username}."
                )
