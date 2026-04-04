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
from ..models import OauthProvider, User, UserOauthAccount

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


def _next_user_oauth_account_id() -> int:
    max_id = db.session.query(func.max(UserOauthAccount.id)).scalar()
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


def _verify_google_id_token(raw_id_token: str, client_id: str):
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2 import id_token as google_id_token

    return google_id_token.verify_oauth2_token(
        raw_id_token,
        GoogleRequest(),
        client_id,
    )


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


@auth_bp.post("/google")
def google_login():
    payload = request.get_json(silent=True) or {}
    raw_id_token = payload.get("id_token")
    if not isinstance(raw_id_token, str) or not raw_id_token.strip():
        return _error_response(
            "auth/validation_error",
            "id_token is required.",
            400,
        )

    client_id = current_app.config.get("GOOGLE_OAUTH_CLIENT_ID")
    if not client_id:
        return _error_response(
            "auth/google_oauth_not_configured",
            "Google OAuth client id is not configured.",
            500,
        )

    try:
        claims = _verify_google_id_token(raw_id_token, client_id)
    except ModuleNotFoundError:
        return _error_response(
            "auth/google_oauth_unavailable",
            "Google OAuth dependency is unavailable.",
            500,
        )
    except ValueError as exc:
        return _error_response(
            "auth/invalid_google_token",
            "Google token verification failed.",
            401,
            detail=str(exc),
        )

    issuer = claims.get("iss")
    if issuer not in {"accounts.google.com", "https://accounts.google.com"}:
        return _error_response(
            "auth/invalid_google_token",
            "Google token issuer is invalid.",
            401,
        )

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.strip():
        return _error_response(
            "auth/invalid_google_token",
            "Google token subject is missing.",
            401,
        )

    email = claims.get("email")
    if not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
        return _error_response(
            "auth/google_email_required",
            "Google account email is required.",
            400,
        )

    if claims.get("email_verified") is False:
        return _error_response(
            "auth/google_email_not_verified",
            "Google account email is not verified.",
            401,
        )

    normalized_email = _normalize_email(email)

    oauth_account = UserOauthAccount.query.filter_by(
        provider=OauthProvider.google,
        provider_user_id=subject,
    ).first()
    if oauth_account:
        user = oauth_account.user
        oauth_account.provider_email = normalized_email
    else:
        user = User.query.filter(func.lower(User.email) == normalized_email).first()
        if not user:
            display_name = claims.get("name")
            normalized_display_name = (
                display_name.strip()
                if isinstance(display_name, str) and display_name.strip()
                else normalized_email.split("@")[0]
            )
            user = User(
                id=_next_user_id(),
                email=normalized_email,
                display_name=normalized_display_name[:80],
                avatar_url=claims.get("picture") if isinstance(claims.get("picture"), str) else None,
            )
            db.session.add(user)

        oauth_account = UserOauthAccount(
            id=_next_user_oauth_account_id(),
            user=user,
            provider=OauthProvider.google,
            provider_user_id=subject,
            provider_email=normalized_email,
        )
        db.session.add(oauth_account)

    user.last_login_at = datetime.now(timezone.utc)
    db.session.commit()

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"scope": "user", "auth_method": "google"},
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
