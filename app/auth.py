from marshmallow import ValidationError
from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required

from app.extensions import db
from app.models import User
from app.schemas import LoginSchema, RegisterSchema
from app.utils import api_response, current_user, role_required

auth_bp = Blueprint("auth", __name__)

register_schema = RegisterSchema()
login_schema = LoginSchema()


@auth_bp.post("/register")
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, email, password]
          properties:
            name: {type: string, example: Ajay}
            email: {type: string, example: ajay@example.com}
            password: {type: string, example: StrongPass123}
            role: {type: string, example: user}
    responses:
      201:
        description: User registered
    """
    try:
        payload = register_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation Error", "messages": err.messages}), 400

    if User.query.filter_by(email=payload["email"].lower()).first():
        return jsonify({"error": "Conflict", "message": "Email is already registered."}), 409

    user = User(
        name=payload["name"].strip(),
        email=payload["email"].lower(),
        role=payload["role"],
    )
    user.set_password(payload["password"])
    db.session.add(user)
    db.session.commit()

    return api_response(
        "User registered successfully.",
        {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        },
        201,
    )


@auth_bp.post("/login")
def login():
    """
    Login and get a JWT token
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email: {type: string, example: admin@example.com}
            password: {type: string, example: Admin@123}
    responses:
      200:
        description: Login success
    """
    try:
        payload = login_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation Error", "messages": err.messages}), 400

    user = User.query.filter_by(email=payload["email"].lower()).first()
    if not user or not user.check_password(payload["password"]):
        return jsonify({"error": "Unauthorized", "message": "Invalid email or password."}), 401

    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return api_response(
        "Login successful.",
        {
            "access_token": token,
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role},
        },
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    """
    Get current user profile
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      200:
        description: Current user returned
    """
    user = current_user()
    return api_response(
        "User profile fetched successfully.",
        {"user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}},
    )


@auth_bp.get("/admin/users")
@role_required("admin")
def admin_users():
    """
    List all users (admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: Users listed
    """
    users = User.query.order_by(User.created_at.desc()).all()
    data = [
        {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        for user in users
    ]
    return api_response("Users fetched successfully.", {"users": data})


@auth_bp.get("/admin/summary")
@role_required("admin")
def admin_summary():
    """
    Fetch admin dashboard summary
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: Summary returned
    """
    from app.models import Task

    return api_response(
        "Admin summary fetched successfully.",
        {
            "counts": {
                "users": User.query.count(),
                "admins": User.query.filter_by(role="admin").count(),
                "tasks": Task.query.count(),
            }
        },
    )
