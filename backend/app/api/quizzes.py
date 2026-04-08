from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import func, or_

from ..extensions import db
from ..models import (
    AnswerResult,
    Choice,
    PlayStatus,
    Question,
    Quiz,
    QuizPlay,
    QuizPlayAnswer,
    QuizStatus,
    User,
)

quizzes_bp = Blueprint("quizzes", __name__, url_prefix="/api/quizzes")

QUIZ_TITLE_MAX_LENGTH = 120
QUIZ_DESCRIPTION_MAX_LENGTH = 2000
QUESTION_BODY_MAX_LENGTH = 2000
QUESTION_EXPLANATION_MAX_LENGTH = 4000
CHOICE_BODY_MAX_LENGTH = 1000
CATEGORY_MAX_LENGTH = 80
QUERY_MAX_LENGTH = 120
MIN_QUESTIONS = 1
MAX_QUESTIONS = 50
MIN_CHOICES_PER_QUESTION = 2
MAX_CHOICES_PER_QUESTION = 6
DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 50


def _parse_int(value, field_name: str):
    try:
        return int(value), None
    except (TypeError, ValueError):
        return None, _error_response("quiz/validation_error", f"{field_name} must be an integer.", 400)


def _validate_play_payload(payload: dict):
    answers = payload.get("answers")
    if not isinstance(answers, list):
        return None, _error_response("quiz/validation_error", "answers is required and must be an array.", 400)

    normalized_answers = []
    seen_question_ids = set()
    for index, answer in enumerate(answers, start=1):
        if not isinstance(answer, dict):
            return None, _error_response("quiz/validation_error", f"answers[{index}] must be an object.", 400)

        if "question_id" not in answer:
            return None, _error_response("quiz/validation_error", f"answers[{index}].question_id is required.", 400)

        question_id, question_err = _parse_int(answer.get("question_id"), f"answers[{index}].question_id")
        if question_err:
            return None, question_err

        if question_id in seen_question_ids:
            return None, _error_response(
                "quiz/validation_error",
                f"answers[{index}].question_id is duplicated.",
                400,
            )
        seen_question_ids.add(question_id)

        selected_choice_raw = answer.get("selected_choice_id")
        if selected_choice_raw is None:
            selected_choice_id = None
        else:
            selected_choice_id, choice_err = _parse_int(
                selected_choice_raw,
                f"answers[{index}].selected_choice_id",
            )
            if choice_err:
                return None, choice_err

        normalized_answers.append(
            {"question_id": question_id, "selected_choice_id": selected_choice_id}
        )

    return {"answers": normalized_answers}, None


def _next_quiz_play_id() -> int:
    max_id = db.session.query(func.max(QuizPlay.id)).scalar()
    return int(max_id or 0) + 1


def _next_quiz_play_answer_id() -> int:
    max_id = db.session.query(func.max(QuizPlayAnswer.id)).scalar()
    return int(max_id or 0) + 1


def _calculate_score(answer_results, questions):
    possible_score = sum(question.points for question in questions)
    score = sum(result["points_awarded"] for result in answer_results)
    correct_count = sum(1 for result in answer_results if result["result"] == AnswerResult.correct.value)
    total_questions = len(questions)
    incorrect_count = sum(1 for result in answer_results if result["result"] == AnswerResult.incorrect.value)
    skipped_count = sum(1 for result in answer_results if result["result"] == AnswerResult.skipped.value)
    score_percentage = round((score / possible_score) * 100, 2) if possible_score > 0 else 0.0

    return {
        "score": score,
        "correct_count": correct_count,
        "total_questions": total_questions,
        "incorrect_count": incorrect_count,
        "skipped_count": skipped_count,
        "score_percentage": score_percentage,
    }


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
    category = payload.get("category")
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

    if category is not None and not isinstance(category, str):
        return None, _error_response("quiz/validation_error", "category must be a string.", 400)
    normalized_category = category.strip() if isinstance(category, str) and category.strip() else None
    if normalized_category and len(normalized_category) > CATEGORY_MAX_LENGTH:
        return None, _error_response(
            "quiz/validation_error",
            f"category must be {CATEGORY_MAX_LENGTH} characters or fewer.",
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
        "category": normalized_category,
        "questions": normalized_questions,
    }, None


def _validate_list_query_params(query_params):
    q = query_params.get("q")
    category = query_params.get("category")
    page_raw = query_params.get("page", str(DEFAULT_PAGE))
    per_page_raw = query_params.get("per_page", str(DEFAULT_PER_PAGE))

    if q is not None:
        if not isinstance(q, str):
            return None, _error_response("quiz/validation_error", "q must be a string.", 400)
        q = q.strip()
        if len(q) > QUERY_MAX_LENGTH:
            return None, _error_response(
                "quiz/validation_error",
                f"q must be {QUERY_MAX_LENGTH} characters or fewer.",
                400,
            )
        if not q:
            q = None

    if category is not None:
        if not isinstance(category, str):
            return None, _error_response("quiz/validation_error", "category must be a string.", 400)
        category = category.strip()
        if len(category) > CATEGORY_MAX_LENGTH:
            return None, _error_response(
                "quiz/validation_error",
                f"category must be {CATEGORY_MAX_LENGTH} characters or fewer.",
                400,
            )
        if not category:
            category = None

    try:
        page = int(page_raw)
    except (TypeError, ValueError):
        return None, _error_response("quiz/validation_error", "page must be an integer.", 400)
    if page < 1:
        return None, _error_response("quiz/validation_error", "page must be 1 or greater.", 400)

    try:
        per_page = int(per_page_raw)
    except (TypeError, ValueError):
        return None, _error_response("quiz/validation_error", "per_page must be an integer.", 400)
    if per_page < 1 or per_page > MAX_PER_PAGE:
        return None, _error_response(
            "quiz/validation_error",
            f"per_page must be between 1 and {MAX_PER_PAGE}.",
            400,
        )

    return {"q": q, "category": category, "page": page, "per_page": per_page}, None


def _description_summary(description: str | None, max_length: int = 160):
    if description is None:
        return None
    if len(description) <= max_length:
        return description
    return f"{description[: max_length - 1]}…"


def _serialize_quiz_list_item(quiz: Quiz, author_display_name: str | None, question_count: int):
    return {
        "id": str(quiz.id),
        "title": quiz.title,
        "description_summary": _description_summary(quiz.description),
        "category": quiz.category,
        "question_count": int(question_count),
        "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
        "author": {
            "id": str(quiz.author_user_id),
            "display_name": author_display_name,
        },
    }


def _serialize_quiz_detail(quiz: Quiz, author_display_name: str | None, questions_with_choices):
    return {
        "id": str(quiz.id),
        "title": quiz.title,
        "description": quiz.description,
        "category": quiz.category,
        "status": quiz.status.value,
        "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
        "author": {
            "id": str(quiz.author_user_id),
            "display_name": author_display_name,
        },
        "question_count": len(questions_with_choices),
        "questions": questions_with_choices,
    }


@quizzes_bp.get("")
def list_quizzes():
    validated, validation_error = _validate_list_query_params(request.args)
    if validation_error:
        return validation_error

    page = validated["page"]
    per_page = validated["per_page"]
    offset = (page - 1) * per_page

    base_query = (
        db.session.query(
            Quiz,
            User.display_name,
            func.count(Question.id).label("question_count"),
        )
        .join(User, User.id == Quiz.author_user_id)
        .outerjoin(Question, Question.quiz_id == Quiz.id)
        .group_by(Quiz.id, User.display_name)
    )

    if validated["q"]:
        pattern = f"%{validated['q']}%"
        base_query = base_query.filter(
            or_(
                Quiz.title.ilike(pattern),
                Quiz.description.ilike(pattern),
            )
        )
    if validated["category"]:
        base_query = base_query.filter(Quiz.category == validated["category"])

    total = (
        db.session.query(func.count(Quiz.id))
        .select_from(Quiz)
        .join(User, User.id == Quiz.author_user_id)
    )
    if validated["q"]:
        pattern = f"%{validated['q']}%"
        total = total.filter(
            or_(
                Quiz.title.ilike(pattern),
                Quiz.description.ilike(pattern),
            )
        )
    if validated["category"]:
        total = total.filter(Quiz.category == validated["category"])
    total_count = int(total.scalar() or 0)

    quizzes = (
        base_query.order_by(Quiz.created_at.desc(), Quiz.id.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    items = [
        _serialize_quiz_list_item(quiz, author_display_name, question_count)
        for quiz, author_display_name, question_count in quizzes
    ]

    return jsonify(
        {
            "items": items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total_count,
                "total_pages": (total_count + per_page - 1) // per_page if total_count else 0,
            },
            "filters": {
                "q": validated["q"],
                "category": validated["category"],
            },
        }
    )


@quizzes_bp.get("/<int:quiz_id>")
def get_quiz_detail(quiz_id: int):
    quiz_with_author = (
        db.session.query(Quiz, User.display_name)
        .join(User, User.id == Quiz.author_user_id)
        .filter(Quiz.id == quiz_id)
        .first()
    )
    if not quiz_with_author:
        return _error_response("quiz/not_found", "Quiz not found.", 404)

    quiz, author_display_name = quiz_with_author

    questions = (
        Question.query.filter_by(quiz_id=quiz.id)
        .order_by(Question.sort_order.asc(), Question.id.asc())
        .all()
    )
    question_ids = [question.id for question in questions]
    choices = (
        Choice.query.filter(Choice.question_id.in_(question_ids))
        .order_by(Choice.sort_order.asc(), Choice.id.asc())
        .all()
        if question_ids
        else []
    )

    choices_by_question_id = {}
    for choice in choices:
        choices_by_question_id.setdefault(choice.question_id, []).append(choice)

    questions_with_choices = [
        {
            "id": str(question.id),
            "body": question.body,
            "explanation": question.explanation,
            "sort_order": question.sort_order,
            "choices": [
                {
                    "id": str(choice.id),
                    "body": choice.body,
                    "sort_order": choice.sort_order,
                }
                for choice in choices_by_question_id.get(question.id, [])
            ],
        }
        for question in questions
    ]

    return jsonify({"quiz": _serialize_quiz_detail(quiz, author_display_name, questions_with_choices)})


@quizzes_bp.post("/<int:quiz_id>/play")
@jwt_required()
def submit_quiz_play(quiz_id: int):
    payload = request.get_json(silent=True) or {}
    validated, validation_error = _validate_play_payload(payload)
    if validation_error:
        return validation_error

    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        return _error_response("quiz/not_found", "Quiz not found.", 404)

    questions = (
        Question.query.filter_by(quiz_id=quiz.id)
        .order_by(Question.sort_order.asc(), Question.id.asc())
        .all()
    )
    if not questions:
        return _error_response("quiz/invalid_state", "Quiz has no questions.", 409)

    questions_by_id = {question.id: question for question in questions}
    answer_by_question_id = {answer["question_id"]: answer["selected_choice_id"] for answer in validated["answers"]}

    unknown_question_ids = sorted(set(answer_by_question_id.keys()) - set(questions_by_id.keys()))
    if unknown_question_ids:
        return _error_response(
            "quiz/invalid_answer",
            "answers contains question_id that does not belong to this quiz.",
            400,
            detail=f"question_ids={unknown_question_ids}",
        )

    all_choices = (
        Choice.query.filter(Choice.question_id.in_(questions_by_id.keys()))
        .order_by(Choice.id.asc())
        .all()
    )
    choices_by_id = {choice.id: choice for choice in all_choices}

    submitted_choice_ids = {
        selected_choice_id
        for selected_choice_id in answer_by_question_id.values()
        if selected_choice_id is not None
    }
    unknown_choice_ids = sorted(choice_id for choice_id in submitted_choice_ids if choice_id not in choices_by_id)
    if unknown_choice_ids:
        return _error_response(
            "quiz/invalid_answer",
            "answers contains selected_choice_id that does not belong to this quiz.",
            400,
            detail=f"choice_ids={unknown_choice_ids}",
        )

    answer_results = []
    for question in questions:
        selected_choice_id = answer_by_question_id.get(question.id)
        if selected_choice_id is None:
            result = AnswerResult.skipped.value
            points_awarded = 0
        else:
            selected_choice = choices_by_id[selected_choice_id]
            if selected_choice.question_id != question.id:
                return _error_response(
                    "quiz/invalid_answer",
                    "selected_choice_id does not match the provided question_id.",
                    400,
                    detail=(
                        f"question_id={question.id}, selected_choice_id={selected_choice_id}, "
                        f"choice_question_id={selected_choice.question_id}"
                    ),
                )
            if selected_choice.is_correct:
                result = AnswerResult.correct.value
                points_awarded = question.points
            else:
                result = AnswerResult.incorrect.value
                points_awarded = 0

        answer_results.append(
            {
                "question_id": question.id,
                "selected_choice_id": selected_choice_id,
                "result": result,
                "points_awarded": points_awarded,
            }
        )

    score_summary = _calculate_score(answer_results, questions)
    user_id = int(get_jwt_identity())

    try:
        now = datetime.now(timezone.utc)
        quiz_play = QuizPlay(
            id=_next_quiz_play_id(),
            quiz_id=quiz.id,
            player_user_id=user_id,
            status=PlayStatus.submitted,
            started_at=now,
            submitted_at=now,
            score=score_summary["score"],
            correct_answers=score_summary["correct_count"],
            total_questions=score_summary["total_questions"],
        )
        db.session.add(quiz_play)

        next_answer_id = _next_quiz_play_answer_id()
        for answer_result in answer_results:
            play_answer = QuizPlayAnswer(
                id=next_answer_id,
                quiz_play_id=quiz_play.id,
                question_id=answer_result["question_id"],
                selected_choice_id=answer_result["selected_choice_id"],
                result=AnswerResult(answer_result["result"]),
                points_awarded=answer_result["points_awarded"],
                answered_at=now,
            )
            db.session.add(play_answer)
            next_answer_id += 1

        db.session.commit()
    except Exception:
        db.session.rollback()
        return _error_response("quiz/play_submit_failed", "Failed to submit quiz play.", 500)

    return (
        jsonify(
            {
                "play": {
                    "id": str(quiz_play.id),
                    "quiz_id": str(quiz.id),
                    "player_user_id": str(user_id),
                    "status": quiz_play.status.value,
                    "correct_count": score_summary["correct_count"],
                    "incorrect_count": score_summary["incorrect_count"],
                    "skipped_count": score_summary["skipped_count"],
                    "total_questions": score_summary["total_questions"],
                    "score": score_summary["score"],
                    "score_percentage": score_summary["score_percentage"],
                    "submitted_at": quiz_play.submitted_at.isoformat() if quiz_play.submitted_at else None,
                    "answers": [
                        {
                            "question_id": str(answer_result["question_id"]),
                            "selected_choice_id": (
                                str(answer_result["selected_choice_id"])
                                if answer_result["selected_choice_id"] is not None
                                else None
                            ),
                            "result": answer_result["result"],
                            "points_awarded": answer_result["points_awarded"],
                        }
                        for answer_result in answer_results
                    ],
                }
            }
        ),
        201,
    )


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
            category=validated["category"],
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
                    "category": quiz.category,
                    "status": quiz.status.value,
                    "author_user_id": str(quiz.author_user_id),
                    "question_count": len(validated["questions"]),
                }
            }
        ),
        201,
    )
