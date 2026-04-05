import enum

from sqlalchemy import CheckConstraint, UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy.orm import validates

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )


class UserStatus(enum.Enum):
    active = "active"
    suspended = "suspended"
    withdrawn = "withdrawn"


class OauthProvider(enum.Enum):
    google = "google"


class OtpChannel(enum.Enum):
    email = "email"


class OtpPurpose(enum.Enum):
    login = "login"
    signup = "signup"
    password_reset = "password_reset"


class QuizStatus(enum.Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class PlayStatus(enum.Enum):
    started = "started"
    submitted = "submitted"
    abandoned = "abandoned"


class AnswerResult(enum.Enum):
    correct = "correct"
    incorrect = "incorrect"
    skipped = "skipped"


class AuditAction(enum.Enum):
    create = "create"
    update = "update"
    delete = "delete"
    login = "login"
    verify = "verify"


class User(TimestampMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    display_name = db.Column(db.String(80), nullable=False)
    status = db.Column(db.Enum(UserStatus, name="user_status"), nullable=False, default=UserStatus.active)
    avatar_url = db.Column(db.String(500), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, raw_password)

    oauth_accounts = db.relationship("UserOauthAccount", back_populates="user", cascade="all, delete-orphan")
    otp_verifications = db.relationship("OtpVerification", back_populates="user", cascade="all, delete-orphan")


class UserOauthAccount(TimestampMixin, db.Model):
    __tablename__ = "user_oauth_accounts"
    __table_args__ = (
        UniqueConstraint("provider", "provider_user_id", name="uq_user_oauth_accounts_provider_user"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    provider = db.Column(db.Enum(OauthProvider, name="oauth_provider"), nullable=False)
    provider_user_id = db.Column(db.String(255), nullable=False)
    provider_email = db.Column(db.String(255), nullable=True)

    user = db.relationship("User", back_populates="oauth_accounts")


class OtpVerification(TimestampMixin, db.Model):
    __tablename__ = "otp_verifications"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    channel = db.Column(db.Enum(OtpChannel, name="otp_channel"), nullable=False)
    purpose = db.Column(db.Enum(OtpPurpose, name="otp_purpose"), nullable=False)
    destination = db.Column(db.String(255), nullable=False)
    otp_hash = db.Column(db.String(255), nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    consumed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    attempt_count = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User", back_populates="otp_verifications")


class Quiz(TimestampMixin, db.Model):
    __tablename__ = "quizzes"

    id = db.Column(db.BigInteger, primary_key=True)
    author_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(80), nullable=True)
    status = db.Column(db.Enum(QuizStatus, name="quiz_status"), nullable=False, default=QuizStatus.draft)
    time_limit_seconds = db.Column(db.Integer, nullable=True)
    published_at = db.Column(db.DateTime(timezone=True), nullable=True)


class Question(TimestampMixin, db.Model):
    __tablename__ = "questions"

    id = db.Column(db.BigInteger, primary_key=True)
    quiz_id = db.Column(db.BigInteger, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False, default=1)


class Choice(TimestampMixin, db.Model):
    __tablename__ = "choices"
    __table_args__ = (
        CheckConstraint("sort_order > 0", name="ck_choices_sort_order_positive"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    question_id = db.Column(db.BigInteger, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    sort_order = db.Column(db.Integer, nullable=False)


class QuizPlay(TimestampMixin, db.Model):
    __tablename__ = "quiz_plays"

    id = db.Column(db.BigInteger, primary_key=True)
    quiz_id = db.Column(db.BigInteger, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    player_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    status = db.Column(db.Enum(PlayStatus, name="play_status"), nullable=False, default=PlayStatus.started)
    started_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    correct_answers = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=0)


class QuizPlayAnswer(TimestampMixin, db.Model):
    __tablename__ = "quiz_play_answers"

    id = db.Column(db.BigInteger, primary_key=True)
    quiz_play_id = db.Column(db.BigInteger, db.ForeignKey("quiz_plays.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.BigInteger, db.ForeignKey("questions.id", ondelete="RESTRICT"), nullable=False)
    selected_choice_id = db.Column(db.BigInteger, db.ForeignKey("choices.id", ondelete="SET NULL"), nullable=True)
    result = db.Column(db.Enum(AnswerResult, name="answer_result"), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False, default=0)
    answered_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)


class LeaderboardSnapshot(TimestampMixin, db.Model):
    __tablename__ = "leaderboard_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_date", "quiz_id", "user_id", name="uq_leaderboard_snapshots_date_quiz_user"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    snapshot_date = db.Column(db.Date, nullable=False)
    quiz_id = db.Column(db.BigInteger, db.ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    rank = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Integer, nullable=False)
    play_count = db.Column(db.Integer, nullable=False, default=0)

    @validates("rank")
    def validate_rank(self, _key, value):
        if value < 1:
            raise ValueError("rank must be >= 1")
        return value


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    actor_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.Enum(AuditAction, name="audit_action"), nullable=False)
    entity_type = db.Column(db.String(100), nullable=False)
    entity_id = db.Column(db.String(64), nullable=False)
    metadata_json = db.Column("metadata", db.JSON, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
