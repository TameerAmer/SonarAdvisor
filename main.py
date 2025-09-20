from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import os

from sonar_advisor.core.config import settings
from sonar_advisor.core.database import engine, get_db
from sonar_advisor.models.user import User
from sonar_advisor.models.analysis_request import AnalysisRequest
from sonar_advisor.models.ai_report import AIReport
from sonar_advisor.routers import auth, analysis

# Create database tables
User.metadata.create_all(bind=engine)
AnalysisRequest.metadata.create_all(bind=engine)
AIReport.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A FastAPI microservice that integrates with SonarQube and provides AI-based code analysis insights",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/web")
async def get_web_interface():
    """
    Serve the web interface HTML file
    """
    return FileResponse("web_interface.html")


@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint
    """
    try:
        # Simple database connectivity check
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "sonarqube_url": settings.sonarqube_url
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )