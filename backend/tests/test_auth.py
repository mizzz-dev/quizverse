from app import create_app
from app.extensions import db
from app.models import User


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-32-plus-bytes"
    AUTH_ENABLE_DEV_TOKEN_ENDPOINT = True


def _create_client(config=TestConfig):
    app = create_app(config)
    with app.app_context():
        db.create_all()
    return app, app.test_client()


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def test_register_success_issues_access_token_and_hashes_password():
    app, client = _create_client()

    response = client.post(
        "/api/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "safePassword123",
            "display_name": "New User",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert "access_token" in body
    assert body["user"]["email"] == "new-user@example.com"

    with app.app_context():
        user = User.query.filter_by(email="new-user@example.com").first()
        assert user is not None
        assert user.password_hash != "safePassword123"
        assert user.check_password("safePassword123") is True


def test_register_rejects_duplicate_email():
    app, client = _create_client()

    first_response = client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "safePassword123"},
    )
    second_response = client.post(
        "/api/auth/register",
        json={"email": "dup@example.com", "password": "safePassword123"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.get_json()["error"]["code"] == "auth/email_already_registered"


def test_login_success_returns_access_token_and_updates_last_login_at():
    app, client = _create_client()

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "login-target@example.com",
            "password": "safePassword123",
            "display_name": "Login Target",
        },
    )
    assert register_response.status_code == 201

    login_response = client.post(
        "/api/auth/login",
        json={"email": "login-target@example.com", "password": "safePassword123"},
    )

    assert login_response.status_code == 200
    login_body = login_response.get_json()
    assert "access_token" in login_body
    assert login_body["user"]["email"] == "login-target@example.com"

    with app.app_context():
        user = User.query.filter_by(email="login-target@example.com").first()
        assert user is not None
        assert user.last_login_at is not None


def test_login_fails_for_invalid_credentials():
    _app, client = _create_client()

    client.post(
        "/api/auth/register",
        json={"email": "wrong-pass@example.com", "password": "safePassword123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "wrong-pass@example.com", "password": "invalidPassword"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/invalid_credentials"


def test_me_returns_authenticated_user_profile():
    _app, client = _create_client()

    register_response = client.post(
        "/api/auth/register",
        json={
            "email": "me-user@example.com",
            "password": "safePassword123",
            "display_name": "Me User",
        },
    )
    token = register_response.get_json()["access_token"]

    me_response = client.get("/api/auth/me", headers=_auth_header(token))

    assert me_response.status_code == 200
    assert me_response.get_json()["user"]["email"] == "me-user@example.com"


def test_register_fails_for_invalid_input():
    _app, client = _create_client()

    response = client.post(
        "/api/auth/register",
        json={"email": "invalid", "password": "short"},
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "auth/validation_error"


def test_dev_token_and_protected_endpoint_success():
    _app, client = _create_client()

    token_response = client.post("/api/auth/dev-token", json={"user_id": "u-123"})
    assert token_response.status_code == 200

    access_token = token_response.get_json()["access_token"]
    protected_response = client.get(
        "/api/auth/protected",
        headers=_auth_header(access_token),
    )

    assert protected_response.status_code == 200
    assert protected_response.get_json()["identity"] == "u-123"


def test_protected_endpoint_fails_without_token():
    _app, client = _create_client()

    response = client.get("/api/auth/protected")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/missing_token"


def test_protected_endpoint_fails_with_invalid_token():
    _app, client = _create_client()

    response = client.get(
        "/api/auth/protected",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/invalid_token"


def test_dev_token_endpoint_can_be_disabled():
    class DevTokenDisabledConfig(TestConfig):
        AUTH_ENABLE_DEV_TOKEN_ENDPOINT = False

    _app, client = _create_client(DevTokenDisabledConfig)
    response = client.post("/api/auth/dev-token")

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "auth/dev_token_disabled"
