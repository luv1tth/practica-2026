"""Фабрика Flask-приложения «Сервис заметок»."""
import os

from flask import Flask, jsonify

from . import db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE_PATH", os.path.join(app.instance_path, "notes.sqlite")),
        JSON_AS_ASCII=False,
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)
    app.json.ensure_ascii = False
    db.init_app(app)
    app.register_blueprint(bp)

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Не найдено"), 404

    @app.errorhandler(405)
    def method_not_allowed(_):
        return jsonify(error="Метод не поддерживается"), 405

    @app.after_request
    def add_cors(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return resp

    return app
