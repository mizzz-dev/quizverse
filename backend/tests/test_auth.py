from app import create_app


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-32-plus-bytes"
    AUTH_ENABLE_DEV_TOKEN_ENDPOINT = True


def test_dev_token_and_protected_endpoint_success():
    app = create_app(TestConfig)
    client = app.test_client()

    token_response = client.post("/api/auth/dev-token", json={"user_id": "u-123"})
    assert token_response.status_code == 200

    access_token = token_response.get_json()["access_token"]
    protected_response = client.get(
        "/api/auth/protected",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert protected_response.status_code == 200
    assert protected_response.get_json()["identity"] == "u-123"


def test_protected_endpoint_fails_without_token():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/api/auth/protected")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/missing_token"


def test_protected_endpoint_fails_with_invalid_token():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get(
        "/api/auth/protected",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "auth/invalid_token"


def test_dev_token_endpoint_can_be_disabled():
    class DevTokenDisabledConfig(TestConfig):
        AUTH_ENABLE_DEV_TOKEN_ENDPOINT = False

    app = create_app(DevTokenDisabledConfig)
    client = app.test_client()

    response = client.post("/api/auth/dev-token")

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "auth/dev_token_disabled"
