import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1.gap_analysis import router as gap_analysis_router
from app.api.v1.ingestion import router as ingestion_router
from app.db.supabase_client import db_manager

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("skills-mapping-api")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-powered Labour Market Intelligence & Skills Gap Analysis Engine (ESCO Edition)"
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(gap_analysis_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.APP_NAME,
        "version": "1.0.0",
        "ai_provider": settings.AI_PROVIDER,
        "supabase_connected": db_manager.is_connected,
        "documentation": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "occupations_loaded": len(db_manager.get_all_occupations()),
        "skills_loaded": len(db_manager.get_all_skills_flat()),
        "supabase_connected": db_manager.is_connected
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
