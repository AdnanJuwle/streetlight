"""
FastAPI main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from contextlib import asynccontextmanager

from routes import devices, alerts
from models.database import init_db
from schemas import HealthResponse

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        init_db()
        print("Database initialized")
    except Exception as e:
        print(f"Warning: Database initialization failed: {e}")
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Smart Streetlight System API",
    description="AI-powered smart streetlight monitoring and management system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(devices.router)
app.include_router(alerts.router)

# Import ML routes
try:
    from routes import ml
    app.include_router(ml.router)
except ImportError:
    pass  # ML routes optional if models not available

# Import analytics routes
try:
    from routes import analytics
    app.include_router(analytics.router)
except ImportError:
    pass


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from models.database import create_engine_instance
    try:
        engine = create_engine_instance()
        with engine.connect() as conn:
            db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        database=db_status
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Streetlight System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

