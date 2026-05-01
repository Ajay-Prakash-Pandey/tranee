from marshmallow import ValidationError
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Task
from app.schemas import TaskSchema
from app.utils import api_response, current_user

tasks_bp = Blueprint("tasks", __name__)

task_schema = TaskSchema()
tasks_schema = TaskSchema(many=True)


@tasks_bp.get("/tasks")
@jwt_required()
def list_tasks():
    """
    List tasks
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    responses:
      200:
        description: Tasks listed
    """
    user = current_user()
    query = Task.query.order_by(Task.created_at.desc())
    if user.role != "admin":
        query = query.filter_by(owner_id=user.id)
    tasks = query.all()
    return api_response("Tasks fetched successfully.", {"tasks": tasks_schema.dump(tasks)})


@tasks_bp.post("/tasks")
@jwt_required()
def create_task():
    """
    Create a task
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title]
          properties:
            title: {type: string, example: Submit assignment}
            description: {type: string}
            status: {type: string, example: pending}
            priority: {type: string, example: high}
            due_date: {type: string, format: date, example: 2026-05-10}
    responses:
      201:
        description: Task created
    """
    try:
        payload = task_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"error": "Validation Error", "messages": err.messages}), 400

    user = current_user()
    task = Task(**payload, owner_id=user.id)
    db.session.add(task)
    db.session.commit()
    return api_response("Task created successfully.", {"task": task_schema.dump(task)}, 201)


@tasks_bp.get("/tasks/<int:task_id>")
@jwt_required()
def get_task(task_id):
    """
    Get a single task
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    responses:
      200:
        description: Task returned
    """
    task = _task_for_request(task_id)
    if not task:
        return jsonify({"error": "Not Found", "message": "Task not found."}), 404
    return api_response("Task fetched successfully.", {"task": task_schema.dump(task)})


@tasks_bp.put("/tasks/<int:task_id>")
@jwt_required()
def update_task(task_id):
    """
    Update a task
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    responses:
      200:
        description: Task updated
    """
    task = _task_for_request(task_id)
    if not task:
        return jsonify({"error": "Not Found", "message": "Task not found."}), 404

    try:
        payload = task_schema.load(request.get_json() or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": "Validation Error", "messages": err.messages}), 400

    for key, value in payload.items():
        setattr(task, key, value)

    db.session.commit()
    return api_response("Task updated successfully.", {"task": task_schema.dump(task)})


@tasks_bp.delete("/tasks/<int:task_id>")
@jwt_required()
def delete_task(task_id):
    """
    Delete a task
    ---
    tags:
      - Tasks
    security:
      - Bearer: []
    responses:
      200:
        description: Task deleted
    """
    task = _task_for_request(task_id)
    if not task:
        return jsonify({"error": "Not Found", "message": "Task not found."}), 404

    db.session.delete(task)
    db.session.commit()
    return api_response("Task deleted successfully.")


def _task_for_request(task_id):
    user = current_user()
    task = Task.query.get(task_id)
    if not task:
        return None
    if user.role != "admin" and task.owner_id != user.id:
        return None
    return task
