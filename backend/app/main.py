import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import engine, Base
import app.models  # ensure models are loaded
from app.api import api_router

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ai_voice_interviewer")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}", exc_info=True)
    yield
    logger.info("Shutting down AI Voice Interviewer API.")


app = FastAPI(
    title="AI Voice Interviewer API",
    description="Backend API for candidate resume parsing, AI question generation, voice interview, and evaluation.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"An internal server error occurred: {str(exc)}"}
    )

# Root Endpoint
@app.get("/", tags=["Root"])
def root():
    return {
        "service": "AI Voice Interviewer API",
        "status": "online",
        "docs": "/docs",
        "health": "/health"
    }

# Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "ai-voice-interviewer",
        "environment": settings.APP_ENV,
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "ai_engine": "Google Gemini" if settings.GEMINI_API_KEY else ("OpenAI" if settings.OPENAI_API_KEY else "Offline Heuristic Engine")
    }

# Include API Routers
app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

