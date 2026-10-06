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
    data = request.get_json()
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