from flask import Blueprint, request, jsonify
from database import get_db_connection

task_routes = Blueprint("task_routes", __name__)


@task_routes.route("/tasks", methods=["GET"])
def get_tasks():
    connection = get_db_connection()
    tasks = connection.execute("SELECT * FROM tasks").fetchall()
    connection.close()

    return jsonify([dict(task) for task in tasks])


@task_routes.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)
    title = data.get("title")
    description = data.get("description", "")

    if not title or not title.strip():
        return jsonify({"error": "Title cannot be empty or whitespace only"}), 400

    connection = get_db_connection()

    cursor = connection.execute(
        """
        INSERT INTO tasks (title, description)
        VALUES (?, ?)
        """,
        (title, description)
    )

    connection.commit()

    task_id = cursor.lastrowid

    connection.close()

    return jsonify({
        "id": task_id,
        "title": title,
        "description": description
    }), 201

@task_routes.route("/login", methods=["POST"])
def login():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    username = data.get("username", "")
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if not username.isalpha():
        return jsonify({"error": "Username must contain only alphabetic characters"}), 400

    return jsonify({
        "message": "User logged in successfully",
        "username": username
    }), 200