from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..extensions import db
from ..models import PlayStatus, Quiz, QuizPlay, User

rankings_bp = Blueprint("rankings", __name__, url_prefix="/api")

DEFAULT_PAGE = 1
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 50


def _error_response(code: str, message: str, status_code: int):
    return jsonify({"error": {"code": code, "message": message}}), status_code


def _validate_pagination(query_params):
    page_raw = query_params.get("page", str(DEFAULT_PAGE))
    per_page_raw = query_params.get("per_page", str(DEFAULT_PER_PAGE))

    try:
        page = int(page_raw)
    except (TypeError, ValueError):
        return None, _error_response("ranking/validation_error", "page must be an integer.", 400)

    if page < 1:
        return None, _error_response("ranking/validation_error", "page must be 1 or greater.", 400)

    try:
        per_page = int(per_page_raw)
    except (TypeError, ValueError):
        return None, _error_response("ranking/validation_error", "per_page must be an integer.", 400)

    if per_page < 1 or per_page > MAX_PER_PAGE:
        return None, _error_response(
            "ranking/validation_error",
            f"per_page must be between 1 and {MAX_PER_PAGE}.",
            400,
        )

    return {"page": page, "per_page": per_page}, None


def _masked_display_name(user_id: int, display_name: str | None):
    if display_name and display_name.strip():
        return display_name
    return f"user-{user_id}"


def _best_quiz_play_subquery(quiz_id: int | None = None):
    play_order_subquery = (
        db.session.query(
            QuizPlay.id.label("play_id"),
            QuizPlay.quiz_id.label("quiz_id"),
            QuizPlay.player_user_id.label("user_id"),
            QuizPlay.score.label("score"),
            QuizPlay.correct_answers.label("correct_answers"),
            func.coalesce(QuizPlay.submitted_at, QuizPlay.created_at).label("played_at"),
            func.row_number()
            .over(
                partition_by=(QuizPlay.player_user_id, QuizPlay.quiz_id),
                order_by=(
                    QuizPlay.score.desc(),
                    QuizPlay.correct_answers.desc(),
                    func.coalesce(QuizPlay.submitted_at, QuizPlay.created_at).asc(),
                    QuizPlay.id.asc(),
                ),
            )
            .label("best_rank"),
        )
        .filter(QuizPlay.status == PlayStatus.submitted)
    )

    if quiz_id is not None:
        play_order_subquery = play_order_subquery.filter(QuizPlay.quiz_id == quiz_id)

    return play_order_subquery.subquery()


def _serialize_pagination(page: int, per_page: int, total: int):
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
    }


@rankings_bp.get("/quizzes/<int:quiz_id>/rankings")
def get_quiz_rankings(quiz_id: int):
    validated, validation_error = _validate_pagination(request.args)
    if validation_error:
        return validation_error

    quiz = Quiz.query.filter_by(id=quiz_id).first()
    if not quiz:
        return _error_response("quiz/not_found", "Quiz not found.", 404)

    page = validated["page"]
    per_page = validated["per_page"]
    offset = (page - 1) * per_page

    best_play_subquery = _best_quiz_play_subquery(quiz_id=quiz_id)

    ranking_query = (
        db.session.query(
            best_play_subquery.c.play_id,
            best_play_subquery.c.user_id,
            best_play_subquery.c.score,
            best_play_subquery.c.correct_answers,
            best_play_subquery.c.played_at,
            User.display_name,
            func.dense_rank()
            .over(
                order_by=(
                    best_play_subquery.c.score.desc(),
                    best_play_subquery.c.correct_answers.desc(),
                    best_play_subquery.c.played_at.asc(),
                    best_play_subquery.c.play_id.asc(),
                )
            )
            .label("rank"),
        )
        .join(User, User.id == best_play_subquery.c.user_id)
        .filter(best_play_subquery.c.best_rank == 1)
    )

    total_entries = int(
        db.session.query(func.count())
        .select_from(best_play_subquery)
        .filter(best_play_subquery.c.best_rank == 1)
        .scalar()
        or 0
    )

    rows = (
        ranking_query.order_by(
            best_play_subquery.c.score.desc(),
            best_play_subquery.c.correct_answers.desc(),
            best_play_subquery.c.played_at.asc(),
            best_play_subquery.c.play_id.asc(),
        )
        .offset(offset)
        .limit(per_page)
        .all()
    )

    items = [
        {
            "rank": int(row.rank),
            "score": int(row.score),
            "correct_count": int(row.correct_answers),
            "best_play_id": str(row.play_id),
            "played_at": row.played_at.isoformat() if row.played_at else None,
            "user": {
                "id": str(row.user_id),
                "display_name": _masked_display_name(row.user_id, row.display_name),
            },
        }
        for row in rows
    ]

    return jsonify(
        {
            "scope": "quiz",
            "ranking_type": "best_play_per_user",
            "tie_breaker": ["score_desc", "correct_count_desc", "played_at_asc", "play_id_asc"],
            "quiz": {
                "id": str(quiz.id),
                "title": quiz.title,
                "category": quiz.category,
            },
            "items": items,
            "pagination": _serialize_pagination(page, per_page, total_entries),
        }
    )


@rankings_bp.get("/rankings")
def get_overall_rankings():
    validated, validation_error = _validate_pagination(request.args)
    if validation_error:
        return validation_error

    page = validated["page"]
    per_page = validated["per_page"]
    offset = (page - 1) * per_page

    best_play_subquery = _best_quiz_play_subquery()

    aggregate_subquery = (
        db.session.query(
            best_play_subquery.c.user_id.label("user_id"),
            func.sum(best_play_subquery.c.score).label("total_score"),
            func.sum(best_play_subquery.c.correct_answers).label("total_correct_answers"),
            func.count(best_play_subquery.c.quiz_id).label("quiz_count"),
            func.min(best_play_subquery.c.played_at).label("first_played_at"),
        )
        .filter(best_play_subquery.c.best_rank == 1)
        .group_by(best_play_subquery.c.user_id)
        .subquery()
    )

    ranking_query = (
        db.session.query(
            aggregate_subquery.c.user_id,
            aggregate_subquery.c.total_score,
            aggregate_subquery.c.total_correct_answers,
            aggregate_subquery.c.quiz_count,
            aggregate_subquery.c.first_played_at,
            User.display_name,
            func.dense_rank()
            .over(
                order_by=(
                    aggregate_subquery.c.total_score.desc(),
                    aggregate_subquery.c.total_correct_answers.desc(),
                    aggregate_subquery.c.first_played_at.asc(),
                    aggregate_subquery.c.user_id.asc(),
                )
            )
            .label("rank"),
        )
        .join(User, User.id == aggregate_subquery.c.user_id)
    )

    total_entries = int(db.session.query(func.count()).select_from(aggregate_subquery).scalar() or 0)

    rows = (
        ranking_query.order_by(
            aggregate_subquery.c.total_score.desc(),
            aggregate_subquery.c.total_correct_answers.desc(),
            aggregate_subquery.c.first_played_at.asc(),
            aggregate_subquery.c.user_id.asc(),
        )
        .offset(offset)
        .limit(per_page)
        .all()
    )

    items = [
        {
            "rank": int(row.rank),
            "total_score": int(row.total_score),
            "total_correct_count": int(row.total_correct_answers),
            "quiz_count": int(row.quiz_count),
            "first_played_at": row.first_played_at.isoformat() if row.first_played_at else None,
            "user": {
                "id": str(row.user_id),
                "display_name": _masked_display_name(row.user_id, row.display_name),
            },
        }
        for row in rows
    ]

    return jsonify(
        {
            "scope": "overall",
            "ranking_type": "sum_of_best_scores_per_quiz",
            "tie_breaker": [
                "total_score_desc",
                "total_correct_count_desc",
                "first_played_at_asc",
                "user_id_asc",
            ],
            "aggregation": "best_play_per_user_per_quiz_then_sum",
            "items": items,
            "pagination": _serialize_pagination(page, per_page, total_entries),
        }
    )
