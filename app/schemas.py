from marshmallow import Schema, ValidationError, fields, validate, validates

ALLOWED_ROLES = {"user", "admin"}
ALLOWED_STATUSES = {"pending", "in_progress", "completed"}
ALLOWED_PRIORITIES = {"low", "medium", "high"}


class RegisterSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.String(required=True, load_only=True, validate=validate.Length(min=8, max=128))
    role = fields.String(load_default="user")

    @validates("role")
    def validate_role(self, value, **_kwargs):
        if value not in ALLOWED_ROLES:
            raise ValidationError("Role must be either 'user' or 'admin'.")


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.String(required=True, load_only=True)


class TaskSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String(required=True, validate=validate.Length(min=3, max=160))
    description = fields.String(load_default="")
    status = fields.String(load_default="pending")
    priority = fields.String(load_default="medium")
    due_date = fields.Date(allow_none=True)
    owner_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates("status")
    def validate_status(self, value, **_kwargs):
        if value not in ALLOWED_STATUSES:
            raise ValidationError("Status must be pending, in_progress, or completed.")

    @validates("priority")
    def validate_priority(self, value, **_kwargs):
        if value not in ALLOWED_PRIORITIES:
            raise ValidationError("Priority must be low, medium, or high.")
