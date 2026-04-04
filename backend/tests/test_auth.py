from app import create_app
from app.extensions import db
from app.models import OauthProvider, User, UserOauthAccount


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-32-plus-bytes"
    AUTH_ENABLE_DEV_TOKEN_ENDPOINT = True
    GOOGLE_OAUTH_CLIENT_ID = "google-client-id.apps.googleusercontent.com"


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


def test_google_login_creates_user_and_oauth_account(monkeypatch):
    app, client = _create_client()

    def _mock_verify(_raw_id_token, _client_id):
        return {
            "iss": "https://accounts.google.com",
            "aud": TestConfig.GOOGLE_OAUTH_CLIENT_ID,
            "sub": "google-sub-1",
            "email": "google-user@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "https://example.com/avatar.png",
        }

    monkeypatch.setattr("app.api.auth._verify_google_id_token", _mock_verify)

    response = client.post("/api/auth/google", json={"id_token": "dummy"})

    assert response.status_code == 200
    body = response.get_json()
    assert body["user"]["email"] == "google-user@example.com"
    assert body["token_type"] == "Bearer"

    with app.app_context():
        user = User.query.filter_by(email="google-user@example.com").first()
        assert user is not None
        oauth_account = UserOauthAccount.query.filter_by(
            provider=OauthProvider.google,
            provider_user_id="google-sub-1",
        ).first()
        assert oauth_account is not None
        assert oauth_account.user_id == user.id


def test_google_login_links_existing_email_user(monkeypatch):
    app, client = _create_client()
    client.post(
        "/api/auth/register",
        json={
            "email": "linked@example.com",
            "password": "safePassword123",
            "display_name": "Linked User",
        },
    )

    def _mock_verify(_raw_id_token, _client_id):
        return {
            "iss": "accounts.google.com",
            "sub": "google-sub-link",
            "email": "linked@example.com",
            "email_verified": True,
        }

    monkeypatch.setattr("app.api.auth._verify_google_id_token", _mock_verify)
    response = client.post("/api/auth/google", json={"id_token": "dummy"})

    assert response.status_code == 200
    with app.app_context():
        users = User.query.filter_by(email="linked@example.com").all()
        assert len(users) == 1
        oauth_account = UserOauthAccount.query.filter_by(provider_user_id="google-sub-link").first()
        assert oauth_account is not None
        assert oauth_account.user.email == "linked@example.com"


def test_google_login_uses_existing_oauth_link(monkeypatch):
    app, client = _create_client()

    def _mock_verify_first(_raw_id_token, _client_id):
        return {
            "iss": "https://accounts.google.com",
            "sub": "google-sub-repeat",
            "email": "repeat@example.com",
            "email_verified": True,
            "name": "Repeat User",
        }

    monkeypatch.setattr("app.api.auth._verify_google_id_token", _mock_verify_first)
    first = client.post("/api/auth/google", json={"id_token": "dummy"})
    second = client.post("/api/auth/google", json={"id_token": "dummy"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.get_json()["user"]["id"] == second.get_json()["user"]["id"]

    with app.app_context():
        assert User.query.count() == 1
        assert UserOauthAccount.query.count() == 1


def test_google_login_rejects_invalid_token(monkeypatch):
    _app, client = _create_client()

    def _mock_verify(_raw_id_token, _client_id):
        raise ValueError("bad token")

    monkeypatch.setattr("app.api.auth._verify_google_id_token", _mock_verify)
    response = client.post("/api/auth/google", json={"id_token": "invalid"})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/invalid_google_token"


def test_google_login_rejects_missing_email(monkeypatch):
    _app, client = _create_client()

    def _mock_verify(_raw_id_token, _client_id):
        return {
            "iss": "https://accounts.google.com",
            "sub": "google-sub-no-email",
            "email_verified": True,
        }

    monkeypatch.setattr("app.api.auth._verify_google_id_token", _mock_verify)
    response = client.post("/api/auth/google", json={"id_token": "dummy"})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "auth/google_email_required"


def test_google_login_rejects_invalid_issuer(monkeypatch):
    _app, client = _create_client()

    def _mock_verify(_raw_id_token, _client_id):
        return {
            "iss": "https://example.com",
            "sub": "google-sub-bad-iss",
            "email": "issuer@example.com",
            "email_verified": True,
        }

    monkeypatch.setattr("app.api.auth._verify_google_id_token", _mock_verify)
    response = client.post("/api/auth/google", json={"id_token": "dummy"})

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/invalid_google_token"
