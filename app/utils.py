from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from app.models import User


def api_response(message, data=None, status=200):
    payload = {"message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return jsonify({"error": "Forbidden", "message": "You do not have access to this resource."}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def current_user():
    identity = get_jwt_identity()
    return User.query.get(int(identity))
