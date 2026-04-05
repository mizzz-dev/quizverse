from app import create_app
from app.extensions import db
from app.models import Choice, Question, Quiz


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


def _register_and_token(client, email="quiz-owner@example.com"):
    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "safePassword123",
            "display_name": "Quiz Owner",
        },
    )
    assert response.status_code == 201
    return response.get_json()["access_token"]


def test_create_quiz_success_persists_quiz_questions_and_choices():
    app, client = _create_client()
    token = _register_and_token(client)

    response = client.post(
        "/api/quizzes",
        headers=_auth_header(token),
        json={
            "title": "Python Basics Quiz",
            "description": "MVP quiz creation test",
            "questions": [
                {
                    "body": "Which type is mutable?",
                    "choices": [
                        {"body": "tuple", "is_correct": False},
                        {"body": "list", "is_correct": True},
                        {"body": "str", "is_correct": False},
                    ],
                },
                {
                    "body": "2 + 2 = ?",
                    "explanation": "Basic arithmetic",
                    "choices": [
                        {"body": "3", "is_correct": False},
                        {"body": "4", "is_correct": True},
                    ],
                },
            ],
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["quiz"]["title"] == "Python Basics Quiz"
    assert body["quiz"]["question_count"] == 2

    with app.app_context():
        quiz = Quiz.query.first()
        assert quiz is not None
        assert quiz.author_user_id == int(body["quiz"]["author_user_id"])
        questions = Question.query.order_by(Question.sort_order.asc()).all()
        assert len(questions) == 2
        assert questions[0].sort_order == 1
        assert questions[1].sort_order == 2
        for question in questions:
            choices = Choice.query.filter_by(question_id=question.id).all()
            assert len(choices) >= 2
            assert sum(1 for choice in choices if choice.is_correct) == 1


def test_create_quiz_requires_jwt():
    _app, client = _create_client()

    response = client.post(
        "/api/quizzes",
        json={
            "title": "Unauthorized quiz",
            "questions": [
                {
                    "body": "Question",
                    "choices": [
                        {"body": "A", "is_correct": True},
                        {"body": "B", "is_correct": False},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 401


def test_create_quiz_rejects_question_without_correct_choice():
    _app, client = _create_client()
    token = _register_and_token(client, email="no-correct@example.com")

    response = client.post(
        "/api/quizzes",
        headers=_auth_header(token),
        json={
            "title": "Invalid quiz",
            "questions": [
                {
                    "body": "Pick one",
                    "choices": [
                        {"body": "A", "is_correct": False},
                        {"body": "B", "is_correct": False},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"


def test_create_quiz_rejects_multiple_correct_choices_in_single_question():
    _app, client = _create_client()
    token = _register_and_token(client, email="multi-correct@example.com")

    response = client.post(
        "/api/quizzes",
        headers=_auth_header(token),
        json={
            "title": "Invalid quiz",
            "questions": [
                {
                    "body": "Pick one",
                    "choices": [
                        {"body": "A", "is_correct": True},
                        {"body": "B", "is_correct": True},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"


def test_create_quiz_rejects_invalid_choice_count():
    _app, client = _create_client()
    token = _register_and_token(client, email="invalid-count@example.com")

    response = client.post(
        "/api/quizzes",
        headers=_auth_header(token),
        json={
            "title": "Invalid quiz",
            "questions": [
                {
                    "body": "Pick one",
                    "choices": [
                        {"body": "A", "is_correct": True},
                    ],
                }
            ],
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"
