import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

def get_engine():
    db_url = settings.DATABASE_URL
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
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        db_path = os.path.abspath(os.path.join(base_dir, "interviewer.db"))
        fallback_url = f"sqlite:///{db_path}"
        fallback_engine = create_engine(fallback_url, connect_args={"check_same_thread": False})
        return fallback_engine

engine = get_engine()
# Automatically ensure tables exist on engine initialization
try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

