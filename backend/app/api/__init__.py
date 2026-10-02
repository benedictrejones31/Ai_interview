from fastapi import APIRouter
from app.api.routes_resumes import router as resumes_router
from app.api.routes_interviews import router as interviews_router
from app.api.routes_realtime import router as realtime_router
from app.api.routes_admin import router as admin_router

api_router = APIRouter()
api_router.include_router(resumes_router)
api_router.include_router(interviews_router)
api_router.include_router(realtime_router)
api_router.include_router(admin_router)

__all__ = ["api_router"]

