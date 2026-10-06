from flask import Flask
from database import init_db
from routes import task_routes


def create_app():

    app = Flask(__name__)

    init_db()

    app.register_blueprint(task_routes)

    return app


if __name__ == "__main__":

    app = create_app()

    app.run(debug=True)