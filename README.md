# 🤖 AI Coding Agent

An AI-powered coding assistant that understands a small existing codebase, analyzes a developer's natural-language request, identifies relevant files, generates code changes, displays a unified diff for review, applies approved changes, and automatically runs tests to validate the implementation.

The project uses Google Gemini as the LLM and Streamlit as the web interface.

---

## 🚀 Project Overview

The AI Coding Agent is designed to demonstrate an end-to-end agentic coding workflow.

A developer can enter a request such as:

> Add input validation to the Tasks API and write tests for it.

The agent then:

1. Understands the developer's request.
2. Reads the existing project files.
3. Identifies the relevant files.
4. Creates an implementation plan.
5. Generates the required code changes.
6. Generates a unified diff.
7. Shows the proposed changes for review.
8. Applies the changes only after approval.
9. Runs the project's pytest test suite.
10. Displays the final validation result.

This provides a simple but complete AI-assisted software development workflow.

---

## ✨ Key Features

- 🧠 Natural-language coding task understanding
- 📂 Automatic codebase inspection
- 🎯 Relevant file identification
- 📝 AI-generated implementation plan
- 🤖 Gemini-powered code generation
- 🔍 Unified diff generation
- 👀 Human review before applying changes
- ✏️ Controlled file modification
- 🧪 Automated pytest execution
- ✅ Test result reporting
- 🖥️ Streamlit web interface
- 🔐 Environment-variable based API key handling
- 🛡️ Validation of AI-generated file changes

---

## 🏗️ System Architecture

```text
                    ┌─────────────────────┐
                    │     Developer       │
                    │ Natural Language    │
                    │       Task          │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Streamlit UI      │
                    │      app.py         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    AI Agent         │
                    │    agent.py         │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │  Codebase       │        │    Gemini       │
        │    Reader       │        │      LLM        │
        │ file_reader.py  │        │ gemini_service  │
        └────────┬────────┘        └────────┬────────┘
                 │                          │
                 └────────────┬─────────────┘
                              ▼
                    ┌─────────────────────┐
                    │ Change Generator    │
                    │ change_generator.py  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Diff Generator    │
                    │ diff_generator.py   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Human Review &      │
                    │ Approval            │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    File Writer      │
                    │  file_writer.py     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Test Runner      │
                    │  test_runner.py     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Validation Result  │
                    └─────────────────────┘
