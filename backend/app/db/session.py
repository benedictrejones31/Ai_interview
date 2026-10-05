import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
    # If on Render or production and db_url is default localhost, use SQLite directly without error
    if ("localhost" in db_url or "127.0.0.1" in db_url) and (os.getenv("RENDER") or settings.APP_ENV == "production"):
        logger.info("Using embedded SQLite database for deployment resilience.")
        return create_engine("sqlite:///./interviewer.db", connect_args={"check_same_thread": False})

    try:
        # Check if database is PostgreSQL
        if "postgresql" in db_url:
            test_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 3}
            )
            # Try a quick test connection
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Connected to PostgreSQL successfully.")
            return test_engine
        else:
            return create_engine(
                db_url,
                connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
            )
    except Exception as e:
        logger.warning(
            f"PostgreSQL connection to {db_url} failed: {e}. Falling back to SQLite for local session resilience."
        )
        # Fallback to local SQLite database so developer is never blocked if Docker is not running
        fallback_url = "sqlite:///./interviewer.db"
        return create_engine(fallback_url, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

