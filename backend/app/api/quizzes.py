from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func

from ..extensions import db
from ..models import Choice, Question, Quiz, QuizStatus

quizzes_bp = Blueprint("quizzes", __name__, url_prefix="/api/quizzes")

QUIZ_TITLE_MAX_LENGTH = 120
QUIZ_DESCRIPTION_MAX_LENGTH = 2000
QUESTION_BODY_MAX_LENGTH = 2000
QUESTION_EXPLANATION_MAX_LENGTH = 4000
CHOICE_BODY_MAX_LENGTH = 1000
MIN_QUESTIONS = 1
MAX_QUESTIONS = 50
MIN_CHOICES_PER_QUESTION = 2
MAX_CHOICES_PER_QUESTION = 6


def _error_response(code: str, message: str, status_code: int, detail: str | None = None):
    error = {"code": code, "message": message}
    if detail:
        error["detail"] = detail
    return jsonify({"error": error}), status_code


def _next_quiz_id() -> int:
    max_id = db.session.query(func.max(Quiz.id)).scalar()
    return int(max_id or 0) + 1


def _next_question_id() -> int:
    max_id = db.session.query(func.max(Question.id)).scalar()
    return int(max_id or 0) + 1


def _next_choice_id() -> int:
    max_id = db.session.query(func.max(Choice.id)).scalar()
    return int(max_id or 0) + 1


def _validate_create_quiz_payload(payload: dict):
    title = payload.get("title")
    description = payload.get("description")
    questions = payload.get("questions")

    if not isinstance(title, str) or not title.strip():
        return None, _error_response("quiz/validation_error", "title is required.", 400)
    normalized_title = title.strip()
    if len(normalized_title) > QUIZ_TITLE_MAX_LENGTH:
        return None, _error_response(
            "quiz/validation_error",
            f"title must be {QUIZ_TITLE_MAX_LENGTH} characters or fewer.",
            400,
        )

    if description is not None and not isinstance(description, str):
        return None, _error_response("quiz/validation_error", "description must be a string.", 400)
    normalized_description = description.strip() if isinstance(description, str) and description.strip() else None
    if normalized_description and len(normalized_description) > QUIZ_DESCRIPTION_MAX_LENGTH:
        return None, _error_response(
            "quiz/validation_error",
            f"description must be {QUIZ_DESCRIPTION_MAX_LENGTH} characters or fewer.",
            400,
        )

    if not isinstance(questions, list) or not questions:
        return None, _error_response("quiz/validation_error", "questions is required and must be a non-empty array.", 400)
    if len(questions) < MIN_QUESTIONS or len(questions) > MAX_QUESTIONS:
        return None, _error_response(
            "quiz/validation_error",
            f"questions must contain between {MIN_QUESTIONS} and {MAX_QUESTIONS} items.",
            400,
        )

    normalized_questions = []
    for q_idx, question in enumerate(questions, start=1):
        if not isinstance(question, dict):
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}] must be an object.",
                400,
            )

        body = question.get("body")
        explanation = question.get("explanation")
        choices = question.get("choices")

        if not isinstance(body, str) or not body.strip():
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}].body is required.",
                400,
            )
        normalized_body = body.strip()
        if len(normalized_body) > QUESTION_BODY_MAX_LENGTH:
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}].body must be {QUESTION_BODY_MAX_LENGTH} characters or fewer.",
                400,
            )

        if explanation is not None and not isinstance(explanation, str):
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}].explanation must be a string.",
                400,
            )
        normalized_explanation = explanation.strip() if isinstance(explanation, str) and explanation.strip() else None
        if normalized_explanation and len(normalized_explanation) > QUESTION_EXPLANATION_MAX_LENGTH:
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}].explanation must be {QUESTION_EXPLANATION_MAX_LENGTH} characters or fewer.",
                400,
            )

        if not isinstance(choices, list):
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}].choices is required and must be an array.",
                400,
            )
        if len(choices) < MIN_CHOICES_PER_QUESTION or len(choices) > MAX_CHOICES_PER_QUESTION:
            return None, _error_response(
                "quiz/validation_error",
                (
                    f"questions[{q_idx}].choices must contain between "
                    f"{MIN_CHOICES_PER_QUESTION} and {MAX_CHOICES_PER_QUESTION} items."
                ),
                400,
            )

        normalized_choices = []
        correct_count = 0
        for c_idx, choice in enumerate(choices, start=1):
            if not isinstance(choice, dict):
                return None, _error_response(
                    "quiz/validation_error",
                    f"questions[{q_idx}].choices[{c_idx}] must be an object.",
                    400,
                )

            choice_body = choice.get("body")
            is_correct = choice.get("is_correct")

            if not isinstance(choice_body, str) or not choice_body.strip():
                return None, _error_response(
                    "quiz/validation_error",
                    f"questions[{q_idx}].choices[{c_idx}].body is required.",
                    400,
                )
            normalized_choice_body = choice_body.strip()
            if len(normalized_choice_body) > CHOICE_BODY_MAX_LENGTH:
                return None, _error_response(
                    "quiz/validation_error",
                    (
                        f"questions[{q_idx}].choices[{c_idx}].body must be "
                        f"{CHOICE_BODY_MAX_LENGTH} characters or fewer."
                    ),
                    400,
                )

            if not isinstance(is_correct, bool):
                return None, _error_response(
                    "quiz/validation_error",
                    f"questions[{q_idx}].choices[{c_idx}].is_correct must be boolean.",
                    400,
                )

            if is_correct:
                correct_count += 1

            normalized_choices.append(
                {
                    "body": normalized_choice_body,
                    "is_correct": is_correct,
                    "sort_order": c_idx,
                }
            )

        if correct_count != 1:
            return None, _error_response(
                "quiz/validation_error",
                f"questions[{q_idx}] must include exactly one correct choice.",
                400,
            )

        normalized_questions.append(
            {
                "body": normalized_body,
                "explanation": normalized_explanation,
                "sort_order": q_idx,
                "choices": normalized_choices,
            }
        )

    return {
        "title": normalized_title,
        "description": normalized_description,
        "questions": normalized_questions,
    }, None


@quizzes_bp.post("")
@jwt_required()
def create_quiz():
    payload = request.get_json(silent=True) or {}
    validated, validation_error = _validate_create_quiz_payload(payload)
    if validation_error:
        return validation_error

    user_id = get_jwt_identity()

    try:
        quiz = Quiz(
            id=_next_quiz_id(),
            author_user_id=int(user_id),
            title=validated["title"],
            description=validated["description"],
            status=QuizStatus.draft,
        )
        db.session.add(quiz)

        next_question_id = _next_question_id()
        next_choice_id = _next_choice_id()
        for question_payload in validated["questions"]:
            question = Question(
                id=next_question_id,
                quiz_id=quiz.id,
                body=question_payload["body"],
                explanation=question_payload["explanation"],
                sort_order=question_payload["sort_order"],
                points=1,
            )
            next_question_id += 1
            db.session.add(question)

            for choice_payload in question_payload["choices"]:
                choice = Choice(
                    id=next_choice_id,
                    question_id=question.id,
                    body=choice_payload["body"],
                    is_correct=choice_payload["is_correct"],
                    sort_order=choice_payload["sort_order"],
                )
                next_choice_id += 1
                db.session.add(choice)

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error_response(
            "quiz/create_failed",
            "Failed to create quiz.",
            500,
        )

    return (
        jsonify(
            {
                "quiz": {
                    "id": str(quiz.id),
                    "title": quiz.title,
                    "description": quiz.description,
                    "status": quiz.status.value,
                    "author_user_id": str(quiz.author_user_id),
                    "question_count": len(validated["questions"]),
                }
            }
        ),
        201,
    )
