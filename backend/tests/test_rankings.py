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


def _auth_header(token: str):
    return {"Authorization": f"Bearer {token}"}


def _register_and_token(client, email, display_name):
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


def _create_quiz(client, token, title, questions):
    response = client.post(
        "/api/quizzes",
        headers=_auth_header(token),
        json={"title": title, "questions": questions},
    )
    assert response.status_code == 201
    return response.get_json()["quiz"]["id"]


def _fetch_questions(client, quiz_id):
    response = client.get(f"/api/quizzes/{quiz_id}")
    assert response.status_code == 200
    return response.get_json()["quiz"]["questions"]


def _submit_play(client, token, quiz_id, answers):
    response = client.post(
        f"/api/quizzes/{quiz_id}/play",
        headers=_auth_header(token),
        json={"answers": answers},
    )
    assert response.status_code == 201
    return response.get_json()["play"]


def test_get_quiz_rankings_uses_best_play_per_user_and_masks_no_email():
    _app, client = _create_client()
    owner_token = _register_and_token(client, "owner@example.com", "Owner")
    alice_token = _register_and_token(client, "alice@example.com", "Alice")
    bob_token = _register_and_token(client, "bob@example.com", "Bob")

    quiz_id = _create_quiz(
        client,
        owner_token,
        "Ranking Quiz",
        questions=[
            {
                "body": "Q1",
                "choices": [
                    {"body": "A", "is_correct": True},
                    {"body": "B", "is_correct": False},
                ],
            },
            {
                "body": "Q2",
                "choices": [
                    {"body": "A", "is_correct": True},
                    {"body": "B", "is_correct": False},
                ],
            },
        ],
    )
    questions = _fetch_questions(client, quiz_id)

    q1, q2 = questions
    q1_correct = q1["choices"][0]["id"]
    q2_correct = q2["choices"][0]["id"]
    q2_wrong = q2["choices"][1]["id"]

    _submit_play(
        client,
        alice_token,
        quiz_id,
        [
            {"question_id": q1["id"], "selected_choice_id": q1_correct},
            {"question_id": q2["id"], "selected_choice_id": q2_wrong},
        ],
    )
    _submit_play(
        client,
        alice_token,
        quiz_id,
        [
            {"question_id": q1["id"], "selected_choice_id": q1_correct},
            {"question_id": q2["id"], "selected_choice_id": q2_correct},
        ],
    )
    _submit_play(
        client,
        bob_token,
        quiz_id,
        [
            {"question_id": q1["id"], "selected_choice_id": q1_correct},
            {"question_id": q2["id"], "selected_choice_id": q2_wrong},
        ],
    )

    response = client.get(f"/api/quizzes/{quiz_id}/rankings")

    assert response.status_code == 200
    body = response.get_json()
    assert body["scope"] == "quiz"
    assert body["ranking_type"] == "best_play_per_user"
    assert len(body["items"]) == 2
    assert body["items"][0]["user"]["display_name"] == "Alice"
    assert body["items"][0]["score"] == 2
    assert body["items"][0]["rank"] == 1
    assert body["items"][1]["user"]["display_name"] == "Bob"
    assert body["items"][1]["score"] == 1
    assert "email" not in body["items"][0]["user"]


def test_get_overall_rankings_sums_best_scores_per_quiz_and_paginates():
    _app, client = _create_client()
    owner_token = _register_and_token(client, "owner2@example.com", "Owner2")
    alice_token = _register_and_token(client, "alice2@example.com", "Alice2")
    bob_token = _register_and_token(client, "bob2@example.com", "Bob2")

    quiz1_id = _create_quiz(
        client,
        owner_token,
        "Quiz 1",
        questions=[
            {
                "body": "Q1",
                "choices": [
                    {"body": "A", "is_correct": True},
                    {"body": "B", "is_correct": False},
                ],
            }
        ],
    )
    quiz2_id = _create_quiz(
        client,
        owner_token,
        "Quiz 2",
        questions=[
            {
                "body": "Q2",
                "choices": [
                    {"body": "A", "is_correct": True},
                    {"body": "B", "is_correct": False},
                ],
            }
        ],
    )

    quiz1_questions = _fetch_questions(client, quiz1_id)
    quiz2_questions = _fetch_questions(client, quiz2_id)

    q1 = quiz1_questions[0]
    q2 = quiz2_questions[0]
    q1_correct = q1["choices"][0]["id"]
    q1_wrong = q1["choices"][1]["id"]
    q2_correct = q2["choices"][0]["id"]

    _submit_play(
        client,
        alice_token,
        quiz1_id,
        [{"question_id": q1["id"], "selected_choice_id": q1_correct}],
    )
    _submit_play(
        client,
        alice_token,
        quiz2_id,
        [{"question_id": q2["id"], "selected_choice_id": q2_correct}],
    )

    _submit_play(
        client,
        bob_token,
        quiz1_id,
        [{"question_id": q1["id"], "selected_choice_id": q1_wrong}],
    )
    _submit_play(
        client,
        bob_token,
        quiz1_id,
        [{"question_id": q1["id"], "selected_choice_id": q1_correct}],
    )

    response = client.get("/api/rankings", query_string={"page": 1, "per_page": 1})

    assert response.status_code == 200
    body = response.get_json()
    assert body["scope"] == "overall"
    assert body["ranking_type"] == "sum_of_best_scores_per_quiz"
    assert body["pagination"]["total"] == 2
    assert body["pagination"]["total_pages"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["user"]["display_name"] == "Alice2"
    assert body["items"][0]["total_score"] == 2
    assert body["items"][0]["quiz_count"] == 2


def test_rankings_validation_and_not_found_errors():
    _app, client = _create_client()

    response = client.get("/api/rankings", query_string={"page": "a"})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "ranking/validation_error"

    response = client.get("/api/rankings", query_string={"per_page": 100})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "ranking/validation_error"

    response = client.get("/api/quizzes/9999/rankings")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "quiz/not_found"
