import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from sqlalchemy import func

from ..extensions import db, jwt
from ..models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def _error_response(code: str, message: str, status_code: int, detail: str | None = None):
    error = {"code": code, "message": message}
    if detail:
        error["detail"] = detail
    return jsonify({"error": error}), status_code


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _next_user_id() -> int:
    max_id = db.session.query(func.max(User.id)).scalar()
    return int(max_id or 0) + 1


def _serialize_user(user: User):
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "status": user.status.value,
    }


def _validate_register_payload(payload: dict):
    email = payload.get("email")
    password = payload.get("password")
    display_name = payload.get("display_name")

    if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
        return None, None, None, _error_response(
            "auth/validation_error",
            "email is required and must be a valid email address.",
            400,
        )

    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return None, None, None, _error_response(
            "auth/validation_error",
            f"password is required and must be at least {MIN_PASSWORD_LENGTH} characters.",
            400,
        )

    normalized_display_name = (
        display_name.strip() if isinstance(display_name, str) and display_name.strip() else email.split("@")[0]
    )
    if len(normalized_display_name) > 80:
        return None, None, None, _error_response(
            "auth/validation_error",
            "display_name must be 80 characters or fewer.",
            400,
        )

    return _normalize_email(email), password, normalized_display_name, None


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    email, password, display_name, validation_error = _validate_register_payload(payload)
    if validation_error:
        return validation_error

    existing_user = User.query.filter(func.lower(User.email) == email).first()
    if existing_user:
        return _error_response(
            "auth/email_already_registered",
            "The email address is already registered.",
            409,
        )

    user = User(id=_next_user_id(), email=email, display_name=display_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"scope": "user", "auth_method": "password"},
    )

    return (
        jsonify(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "user": _serialize_user(user),
            }
        ),
        201,
    )


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    password = payload.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return _error_response(
            "auth/validation_error",
            "email and password are required.",
            400,
        )

    normalized_email = _normalize_email(email)
    user = User.query.filter(func.lower(User.email) == normalized_email).first()
    if not user or not user.check_password(password):
        return _error_response(
            "auth/invalid_credentials",
            "Invalid email or password.",
            401,
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"scope": "user", "auth_method": "password"},
    )

    return (
        jsonify(
            {
                "access_token": access_token,
                "token_type": "Bearer",
                "user": _serialize_user(user),
            }
        ),
        200,
    )


@auth_bp.post("/dev-token")
def issue_dev_token():
    if not current_app.config.get("AUTH_ENABLE_DEV_TOKEN_ENDPOINT", False):
        return _error_response(
            "auth/dev_token_disabled",
            "Development token endpoint is disabled.",
            403,
        )

    payload = request.get_json(silent=True) or {}
    user_id = str(payload.get("user_id", "dev-user-1"))

    token = create_access_token(
        identity=user_id,
        additional_claims={"scope": "dev", "auth_method": "dev-token"},
    )

    return (
        jsonify(
            {
                "access_token": token,
                "token_type": "Bearer",
                "identity": user_id,
                "note": "Development-only endpoint. Disable in production with AUTH_ENABLE_DEV_TOKEN_ENDPOINT=false.",
            }
        ),
        200,
    )


@auth_bp.get("/protected")
@jwt_required()
def protected():
    return (
        jsonify(
            {
                "message": "Protected access succeeded.",
                "identity": get_jwt_identity(),
                "claims": get_jwt(),
            }
        ),
        200,
    )


@auth_bp.get("/me")
@jwt_required()
def me():
    identity = get_jwt_identity()
    try:
        user_id = int(identity)
    except (TypeError, ValueError):
        return _error_response(
            "auth/user_not_found",
            "Authenticated user does not exist.",
            404,
        )

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return _error_response(
            "auth/user_not_found",
            "Authenticated user does not exist.",
            404,
        )
    return jsonify({"user": _serialize_user(user)}), 200


@jwt.unauthorized_loader
def handle_missing_token(reason: str):
    return _error_response(
        "auth/missing_token",
        "Authorization header is missing or invalid.",
        401,
        detail=reason,
    )


@jwt.invalid_token_loader
def handle_invalid_token(reason: str):
    return _error_response(
        "auth/invalid_token",
        "JWT is invalid.",
        401,
        detail=reason,
    )


@jwt.expired_token_loader
def handle_expired_token(jwt_header, jwt_payload):
    return _error_response(
        "auth/token_expired",
        "JWT has expired.",
        401,
    )
