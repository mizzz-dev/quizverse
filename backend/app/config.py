import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-default")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "unsafe-jwt-default")
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_SECONDS", "3600"))
    )
    AUTH_ENABLE_DEV_TOKEN_ENDPOINT = (
        os.getenv("AUTH_ENABLE_DEV_TOKEN_ENDPOINT", "true").lower() == "true"
    )
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///quizverse.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
