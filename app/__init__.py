from flask import Flask, jsonify, send_from_directory
from flasgger import Swagger

from config import Config
from app.auth import auth_bp
from app.extensions import db, jwt
from app.models import User
from app.tasks import tasks_bp


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="../frontend", static_url_path="")
    app.config.from_object(config_class)

    register_extensions(app)
    register_routes(app)
    register_errors(app)
    register_shell_context(app)

    with app.app_context():
        db.create_all()
        seed_admin()

    return app


def register_extensions(app):
    db.init_app(app)
    jwt.init_app(app)
    Swagger(app, template=_swagger_template())

    @jwt.unauthorized_loader
    def handle_missing_token(reason):
        return jsonify({"error": "Unauthorized", "message": reason}), 401

    @jwt.invalid_token_loader
    def handle_invalid_token(reason):
        return jsonify({"error": "Unauthorized", "message": reason}), 401

    @jwt.expired_token_loader
    def handle_expired_token(_jwt_header, _jwt_payload):
        return jsonify({"error": "Unauthorized", "message": "Token has expired."}), 401


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/v1")

    @app.get("/")
    def root():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "backend-assignment-api"})


def register_errors(app):
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Not Found", "message": "The requested resource does not exist."}), 404

    @app.errorhandler(500)
    def internal_error(_error):
        db.session.rollback()
        return jsonify({"error": "Internal Server Error", "message": "Something went wrong on the server."}), 500


def register_shell_context(app):
    @app.shell_context_processor
    def shell_context():
        return {"db": db, "User": User}


def seed_admin():
    admin_email = "admin@example.com"
    if User.query.filter_by(email=admin_email).first():
        return

    admin = User(
        name="System Admin",
        email=admin_email,
        role="admin",
    )
    admin.set_password("Admin@123")
    db.session.add(admin)
    db.session.commit()


def _swagger_template():
    return {
        "swagger": "2.0",
        "info": {
            "title": "Backend Developer Internship Assignment API",
            "description": "JWT authentication, RBAC, and task CRUD built with Flask.",
            "version": "1.0.0",
        },
        "basePath": "/",
        "schemes": ["http"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Add: Bearer <JWT token>",
            }
        },
    }
