"""add mvp core schema

Revision ID: 20260401_0003
Revises: 20260401_0002
Create Date: 2026-04-01 00:30:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260401_0003"
down_revision = "20260401_0002"
branch_labels = None
depends_on = None


user_status = sa.Enum("active", "suspended", "withdrawn", name="user_status")
oauth_provider = sa.Enum("google", name="oauth_provider")
otp_channel = sa.Enum("email", name="otp_channel")
otp_purpose = sa.Enum("login", "signup", "password_reset", name="otp_purpose")
quiz_status = sa.Enum("draft", "published", "archived", name="quiz_status")
play_status = sa.Enum("started", "submitted", "abandoned", name="play_status")
answer_result = sa.Enum("correct", "incorrect", "skipped", name="answer_result")
audit_action = sa.Enum("create", "update", "delete", "login", "verify", name="audit_action")


def upgrade():
    bind = op.get_bind()
    user_status.create(bind, checkfirst=True)
    oauth_provider.create(bind, checkfirst=True)
    otp_channel.create(bind, checkfirst=True)
    otp_purpose.create(bind, checkfirst=True)
    quiz_status.create(bind, checkfirst=True)
    play_status.create(bind, checkfirst=True)
    answer_result.create(bind, checkfirst=True)
    audit_action.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("status", user_status, nullable=False),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    op.create_table(
        "user_oauth_accounts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("provider", oauth_provider, nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider", "provider_user_id", name="uq_user_oauth_accounts_provider_user"),
    )

    op.create_table(
        "otp_verifications",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("channel", otp_channel, nullable=False),
        sa.Column("purpose", otp_purpose, nullable=False),
        sa.Column("otp_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quizzes",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("author_user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", quiz_status, nullable=False),
        sa.Column("time_limit_seconds", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "questions",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "choices",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("sort_order > 0", name="ck_choices_sort_order_positive"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quiz_plays",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), nullable=False),
        sa.Column("player_user_id", sa.BigInteger(), nullable=False),
        sa.Column("status", play_status, nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("correct_answers", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_questions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["player_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quiz_play_answers",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("quiz_play_id", sa.BigInteger(), nullable=False),
        sa.Column("question_id", sa.BigInteger(), nullable=False),
        sa.Column("selected_choice_id", sa.BigInteger(), nullable=True),
        sa.Column("result", answer_result, nullable=False),
        sa.Column("points_awarded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["quiz_play_id"], ["quiz_plays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["selected_choice_id"], ["choices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "leaderboard_snapshots",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("quiz_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("play_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["quiz_id"], ["quizzes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("snapshot_date", "quiz_id", "user_id", name="uq_leaderboard_snapshots_date_quiz_user"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=64), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_otp_verifications_user_id", "otp_verifications", ["user_id"])
    op.create_index("ix_questions_quiz_id_sort_order", "questions", ["quiz_id", "sort_order"])
    op.create_index("ix_choices_question_id_sort_order", "choices", ["question_id", "sort_order"])
    op.create_index("ix_quiz_plays_quiz_id_player_user_id", "quiz_plays", ["quiz_id", "player_user_id"])
    op.create_index("ix_quiz_play_answers_quiz_play_id", "quiz_play_answers", ["quiz_play_id"])
    op.create_index("ix_leaderboard_snapshots_quiz_date_rank", "leaderboard_snapshots", ["quiz_id", "snapshot_date", "rank"])
    op.create_index("ix_audit_logs_actor_created", "audit_logs", ["actor_user_id", "created_at"])


def downgrade():
    op.drop_index("ix_audit_logs_actor_created", table_name="audit_logs")
    op.drop_index("ix_leaderboard_snapshots_quiz_date_rank", table_name="leaderboard_snapshots")
    op.drop_index("ix_quiz_play_answers_quiz_play_id", table_name="quiz_play_answers")
    op.drop_index("ix_quiz_plays_quiz_id_player_user_id", table_name="quiz_plays")
    op.drop_index("ix_choices_question_id_sort_order", table_name="choices")
    op.drop_index("ix_questions_quiz_id_sort_order", table_name="questions")
    op.drop_index("ix_otp_verifications_user_id", table_name="otp_verifications")

    op.drop_table("audit_logs")
    op.drop_table("leaderboard_snapshots")
    op.drop_table("quiz_play_answers")
    op.drop_table("quiz_plays")
    op.drop_table("choices")
    op.drop_table("questions")
    op.drop_table("quizzes")
    op.drop_table("otp_verifications")
    op.drop_table("user_oauth_accounts")
    op.drop_table("users")

    bind = op.get_bind()
    audit_action.drop(bind, checkfirst=True)
    answer_result.drop(bind, checkfirst=True)
    play_status.drop(bind, checkfirst=True)
    quiz_status.drop(bind, checkfirst=True)
    otp_purpose.drop(bind, checkfirst=True)
    otp_channel.drop(bind, checkfirst=True)
    oauth_provider.drop(bind, checkfirst=True)
    user_status.drop(bind, checkfirst=True)
