import os

basedir = os.path.abspath(os.path.dirname(__file__))


def _resolve_database_uri():
    url = (
        os.environ.get("SUPABASE_DATABASE_URL")
        or os.environ.get("POSTGRES_URL")
        or os.environ.get("DATABASE_URL")
    )
    if url:
        # SQLAlchemy 1.4+ requires the "postgresql://" scheme; some providers
        # (Heroku-style) still hand out "postgres://".
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return "sqlite:///" + os.path.join(basedir, "instance", "expat_review.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
