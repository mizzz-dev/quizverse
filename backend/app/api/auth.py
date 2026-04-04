from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from ..extensions import jwt

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/dev-token")
def issue_dev_token():
    if not current_app.config.get("AUTH_ENABLE_DEV_TOKEN_ENDPOINT", False):
        return (
            jsonify(
                {
                    "error": {
                        "code": "auth/dev_token_disabled",
                        "message": "Development token endpoint is disabled.",
                    }
                }
            ),
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
                "note": "Temporary endpoint for JWT foundation verification. Replace in login/register issue.",
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
    return jsonify({"user_id": get_jwt_identity()}), 200


@jwt.unauthorized_loader
def handle_missing_token(reason: str):
    return (
        jsonify(
            {
                "error": {
                    "code": "auth/missing_token",
                    "message": "Authorization header is missing or invalid.",
                    "detail": reason,
                }
            }
        ),
        401,
    )


@jwt.invalid_token_loader
def handle_invalid_token(reason: str):
    return (
        jsonify(
            {
                "error": {
                    "code": "auth/invalid_token",
                    "message": "JWT is invalid.",
                    "detail": reason,
                }
            }
        ),
        401,
    )


@jwt.expired_token_loader
def handle_expired_token(jwt_header, jwt_payload):
    return (
        jsonify(
            {
                "error": {
                    "code": "auth/token_expired",
                    "message": "JWT has expired.",
                }
            }
        ),
        401,
    )
