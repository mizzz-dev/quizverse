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


def _register_and_token(client, email="quiz-owner@example.com", display_name="Quiz Owner"):
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


def _create_quiz(
    client,
    token,
    title,
    category=None,
    description="MVP quiz",
    questions=None,
):
    if questions is None:
        questions = [
            {
                "body": "Which language runs in the browser?",
                "choices": [
                    {"body": "Python", "is_correct": False},
                    {"body": "JavaScript", "is_correct": True},
                ],
            }
        ]

    payload = {
        "title": title,
        "description": description,
        "questions": questions,
    }
    if category is not None:
        payload["category"] = category

    return client.post(
        "/api/quizzes",
        headers=_auth_header(token),
        json=payload,
    )


def test_create_quiz_success_persists_quiz_questions_and_choices():
    app, client = _create_client()
    token = _register_and_token(client)

    response = _create_quiz(
        client,
        token,
        title="Python Basics Quiz",
        category="programming",
        description="MVP quiz creation test",
        questions=[
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
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["quiz"]["title"] == "Python Basics Quiz"
    assert body["quiz"]["category"] == "programming"
    assert body["quiz"]["question_count"] == 2

    with app.app_context():
        quiz = Quiz.query.first()
        assert quiz is not None
        assert quiz.author_user_id == int(body["quiz"]["author_user_id"])
        assert quiz.category == "programming"
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

    response = _create_quiz(
        client,
        token,
        title="Invalid quiz",
        questions=[
            {
                "body": "Pick one",
                "choices": [
                    {"body": "A", "is_correct": False},
                    {"body": "B", "is_correct": False},
                ],
            }
        ],
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"


def test_create_quiz_rejects_multiple_correct_choices_in_single_question():
    _app, client = _create_client()
    token = _register_and_token(client, email="multi-correct@example.com")

    response = _create_quiz(
        client,
        token,
        title="Invalid quiz",
        questions=[
            {
                "body": "Pick one",
                "choices": [
                    {"body": "A", "is_correct": True},
                    {"body": "B", "is_correct": True},
                ],
            }
        ],
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"


def test_create_quiz_rejects_invalid_choice_count():
    _app, client = _create_client()
    token = _register_and_token(client, email="invalid-count@example.com")

    response = _create_quiz(
        client,
        token,
        title="Invalid quiz",
        questions=[
            {
                "body": "Pick one",
                "choices": [
                    {"body": "A", "is_correct": True},
                ],
            }
        ],
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"


def test_list_quizzes_supports_q_category_and_pagination():
    _app, client = _create_client()
    token_1 = _register_and_token(client, email="owner1@example.com", display_name="Owner One")
    token_2 = _register_and_token(client, email="owner2@example.com", display_name="Owner Two")

    assert _create_quiz(
        client,
        token_1,
        title="Python Intro",
        category="programming",
        description="Learn python basics",
    ).status_code == 201
    assert _create_quiz(
        client,
        token_2,
        title="World History",
        category="history",
        description="Ancient to modern history",
    ).status_code == 201
    assert _create_quiz(
        client,
        token_1,
        title="Python Advanced",
        category="programming",
        description="Deep dive into python",
    ).status_code == 201

    response = client.get(
        "/api/quizzes",
        query_string={"q": "python", "category": "programming", "page": 1, "per_page": 1},
    )

    assert response.status_code == 200
    body = response.get_json()
    assert body["pagination"]["total"] == 2
    assert body["pagination"]["total_pages"] == 2
    assert len(body["items"]) == 1
    assert body["items"][0]["category"] == "programming"
    assert "python" in body["items"][0]["title"].lower()
    assert set(body["items"][0]["author"].keys()) == {"id", "display_name"}


def test_list_quizzes_rejects_invalid_pagination_params():
    _app, client = _create_client()

    response = client.get("/api/quizzes", query_string={"page": 0, "per_page": 10})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"

    response = client.get("/api/quizzes", query_string={"page": 1, "per_page": 51})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "quiz/validation_error"


def test_get_quiz_detail_returns_questions_and_choices_without_answers():
    _app, client = _create_client()
    token = _register_and_token(client, email="detail@example.com", display_name="Detail Owner")

    create_response = _create_quiz(
        client,
        token,
        title="Science Quiz",
        category="science",
        questions=[
            {
                "body": "Water chemical formula?",
                "choices": [
                    {"body": "CO2", "is_correct": False},
                    {"body": "H2O", "is_correct": True},
                ],
            }
        ],
    )
    quiz_id = create_response.get_json()["quiz"]["id"]

    response = client.get(f"/api/quizzes/{quiz_id}")

    assert response.status_code == 200
    body = response.get_json()["quiz"]
    assert body["id"] == quiz_id
    assert body["question_count"] == 1
    assert body["author"]["display_name"] == "Detail Owner"
    assert len(body["questions"]) == 1
    assert len(body["questions"][0]["choices"]) == 2
    assert "is_correct" not in body["questions"][0]["choices"][0]


def test_get_quiz_detail_returns_not_found_when_quiz_is_missing():
    _app, client = _create_client()

    response = client.get("/api/quizzes/9999")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "quiz/not_found"
