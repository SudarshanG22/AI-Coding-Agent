# 🤖 AI Coding Agent

An AI-powered coding assistant that understands a small existing codebase, identifies relevant files, generates code changes from natural-language developer requests, shows the proposed diff for review, applies approved changes, and validates them using automated tests.

The project is built as a small end-to-end AI coding agent using Streamlit and Google's Gemini API.

---

## 🚀 Live Demo

**Deployed Application:**

https://ai-coding-agent-bfa2s5yihfnjqj7zsxcnc2c.streamlit.app

---

## 📂 GitHub Repository

**Source Code:**

https://github.com/SudarshanG22/AI-Coding-Agent

---

## ✨ Features

### 🤖 AI Coding Agent

- Accepts coding tasks in natural language.
- Understands the requested change.
- Reads the sample project codebase.
- Identifies relevant files.
- Generates a step-by-step implementation plan.
- Generates proposed code changes.
- Displays the changes as a diff.
- Requires user approval before applying changes.
- Applies approved changes.
- Runs automated pytest validation.
- Displays test results.

### 🔐 Login Demo

A separate interactive page demonstrates the result of the coding-agent workflow.

The Login Demo validates:

- Username
- Password
- Alphabetic-only usernames

Examples:

```text
Sudarshan       → ✅ Login successful
Sudarshan123    → ❌ Username validation error
Sudarshan@      → ❌ Username validation error
