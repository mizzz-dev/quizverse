from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test"
    JWT_SECRET_KEY = "test-jwt-secret-key-with-32-plus-bytes"


def _create_client(config=TestConfig):
    app = create_app(config)
    with app.app_context():
        db.create_all()
    return app, app.test_client()


def _register(client, email, display_name):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "safePassword123",
            "display_name": display_name,
        },
    )
    assert response.status_code == 201
    return response.get_json()["access_token"]


def _create_quiz(client, token, title, category=None):
    payload = {
        "title": title,
        "description": "admin test quiz",
        "questions": [
            {
                "body": "Question",
                "choices": [
                    {"body": "A", "is_correct": True},
                    {"body": "B", "is_correct": False},
                ],
            }
        ],
    }
    if category:
        payload["category"] = category

    response = client.post(
        "/api/quizzes",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == 201


def test_admin_overview_users_and_quizzes_endpoints():
    _app, client = _create_client()

    token = _register(client, "admin-view-1@example.com", "Admin View 1")
    _register(client, "admin-view-2@example.com", "Admin View 2")
    _create_quiz(client, token, "Admin quiz 1", category="ops")

    overview = client.get("/api/admin/overview")
    assert overview.status_code == 200
    overview_json = overview.get_json()
    assert overview_json["summary"]["users"] == 2
    assert overview_json["summary"]["quizzes"] == 1
    assert overview_json["services"]["api"]["status"] == "ok"

    users_response = client.get("/api/admin/users", query_string={"page": 1, "per_page": 10})
    assert users_response.status_code == 200
    users_json = users_response.get_json()
    assert users_json["pagination"]["total"] == 2
    assert len(users_json["items"]) == 2
    assert "email_masked" in users_json["items"][0]

    quizzes_response = client.get("/api/admin/quizzes", query_string={"page": 1, "per_page": 10})
    assert quizzes_response.status_code == 200
    quizzes_json = quizzes_response.get_json()
    assert quizzes_json["pagination"]["total"] == 1
    assert quizzes_json["items"][0]["title"] == "Admin quiz 1"


def test_admin_endpoints_validate_pagination():
    _app, client = _create_client()

    response = client.get("/api/admin/users", query_string={"page": 0, "per_page": 10})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "admin/validation_error"

    response = client.get("/api/admin/quizzes", query_string={"page": 1, "per_page": 99})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "admin/validation_error"


def test_admin_email_settings_requires_admin_header():
    _app, client = _create_client()

    response = client.get("/api/admin/email-settings")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "admin/forbidden"


def test_admin_email_settings_put_and_get_masked_password():
    _app, client = _create_client()
    headers = {"X-Admin-Mode": "true"}

    response = client.put(
        "/api/admin/email-settings",
        headers=headers,
        json={
            "sender_name": "QuizVerse通知",
            "sender_email": "notify@example.com",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "top-secret",
            "use_tls": True,
            "use_ssl": False,
        },
    )
    assert response.status_code == 200
    saved_json = response.get_json()
    assert saved_json["email_settings"]["has_smtp_password"] is True
    assert saved_json["email_settings"]["smtp_password_masked"] == "********"

    get_response = client.get("/api/admin/email-settings", headers=headers)
    assert get_response.status_code == 200
    get_json = get_response.get_json()
    assert get_json["email_settings"]["sender_email"] == "notify@example.com"
    assert get_json["email_settings"]["smtp_password_masked"] == "********"
    assert "smtp_password" not in get_json["email_settings"]


def test_admin_email_settings_validation():
    _app, client = _create_client()
    headers = {"X-Admin-Mode": "true"}

    response = client.put(
        "/api/admin/email-settings",
        headers=headers,
        json={
            "sender_name": "QuizVerse通知",
            "sender_email": "invalid-email",
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "smtp-user",
            "smtp_password": "",
            "use_tls": True,
            "use_ssl": True,
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "admin/validation_error"
