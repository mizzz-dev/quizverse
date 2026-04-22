from flask import Blueprint, jsonify, request
from sqlalchemy import func

from ..extensions import db
from ..models import PlayStatus, Quiz, QuizPlay, User

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")

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
        return None, _error_response("admin/validation_error", "page must be an integer.", 400)

    if page < 1:
        return None, _error_response("admin/validation_error", "page must be 1 or greater.", 400)

    try:
        per_page = int(per_page_raw)
    except (TypeError, ValueError):
        return None, _error_response("admin/validation_error", "per_page must be an integer.", 400)

    if per_page < 1 or per_page > MAX_PER_PAGE:
        return None, _error_response("admin/validation_error", f"per_page must be between 1 and {MAX_PER_PAGE}.", 400)

    return {"page": page, "per_page": per_page}, None


def _serialize_pagination(page: int, per_page: int, total: int):
    return {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": (total + per_page - 1) // per_page if total else 0,
    }


def _mask_email(email: str):
    local, _, domain = email.partition("@")
    if not local or not domain:
        return "***"
    if len(local) <= 2:
        return f"{local[0]}***@{domain}"
    return f"{local[:2]}***@{domain}"


@admin_bp.get("/overview")
def get_admin_overview():
    user_count = int(db.session.query(func.count(User.id)).scalar() or 0)
    quiz_count = int(db.session.query(func.count(Quiz.id)).scalar() or 0)
    play_count = int(db.session.query(func.count(QuizPlay.id)).scalar() or 0)
    submitted_play_count = int(
        db.session.query(func.count(QuizPlay.id)).filter(QuizPlay.status == PlayStatus.submitted).scalar() or 0
    )

    health_check = {"status": "ok", "latency_ms": 20}
    try:
        db.session.execute(db.text("SELECT 1"))
        database_check = {"status": "ok", "latency_ms": 12}
    except Exception:
        database_check = {"status": "error", "latency_ms": None}

    return jsonify(
        {
            "summary": {
                "users": user_count,
                "quizzes": quiz_count,
                "plays": play_count,
                "ranking_entries": submitted_play_count,
            },
            "services": {
                "api": health_check,
                "database": database_check,
                "mail_delivery": {
                    "status": "warning",
                    "latency_ms": None,
                    "note": "MVPではメール到達確認は未実装",
                },
            },
            "permission": {
                "mode": "provisional",
                "note": "admin判定はフロントエンドの仮導線。RBACは次Issueで設計予定",
            },
        }
    )


@admin_bp.get("/users")
def get_admin_users():
    validated, validation_error = _validate_pagination(request.args)
    if validation_error:
        return validation_error

    page = validated["page"]
    per_page = validated["per_page"]
    offset = (page - 1) * per_page

    total = int(db.session.query(func.count(User.id)).scalar() or 0)
    users = User.query.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(per_page).all()

    items = [
        {
            "id": str(user.id),
            "display_name": user.display_name,
            "email_masked": _mask_email(user.email),
            "status": user.status.value,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
        for user in users
    ]

    return jsonify({"items": items, "pagination": _serialize_pagination(page, per_page, total)})


@admin_bp.get("/quizzes")
def get_admin_quizzes():
    validated, validation_error = _validate_pagination(request.args)
    if validation_error:
        return validation_error

    page = validated["page"]
    per_page = validated["per_page"]
    offset = (page - 1) * per_page

    base_query = (
        db.session.query(Quiz, User.display_name, func.count(QuizPlay.id).label("play_count"))
        .join(User, User.id == Quiz.author_user_id)
        .outerjoin(QuizPlay, QuizPlay.quiz_id == Quiz.id)
        .group_by(Quiz.id, User.display_name)
    )
    total = int(db.session.query(func.count(Quiz.id)).scalar() or 0)
    rows = base_query.order_by(Quiz.created_at.desc(), Quiz.id.desc()).offset(offset).limit(per_page).all()

    items = [
        {
            "id": str(quiz.id),
            "title": quiz.title,
            "category": quiz.category,
            "status": quiz.status.value,
            "author": {"id": str(quiz.author_user_id), "display_name": author_name},
            "play_count": int(play_count),
            "created_at": quiz.created_at.isoformat() if quiz.created_at else None,
        }
        for quiz, author_name, play_count in rows
    ]

    return jsonify({"items": items, "pagination": _serialize_pagination(page, per_page, total)})
