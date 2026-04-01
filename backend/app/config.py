import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-default")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "unsafe-jwt-default")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///quizverse.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
