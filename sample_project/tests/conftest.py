import sys
from pathlib import Path

import pytest


# Add sample_project to Python's import path
PROJECT_DIR = Path(__file__).resolve().parents[1]

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))


from app import create_app


@pytest.fixture
def client():
    """
    Creates a Flask test client for API testing.
    """

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client