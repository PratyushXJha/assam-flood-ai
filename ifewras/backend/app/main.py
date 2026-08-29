"""Main FastAPI Application Entrypoint for IFEWRAS.
Integrated Flood Early Warning + Rescue Allocation System (Smart India Hackathon 2026)
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes_stage1 import router as stage1_router
from app.api.routes_stage2 import router as stage2_router
from app.api.routes_stage3 import router as stage3_router
from app.api.routes_simulation import router as simulation_router

app = FastAPI(
    title="IFEWRAS - Integrated Flood Early Warning + Rescue Allocation System",
    description="ASDMA / SDRF Multi-Stage Flood Early Warning, Gauge Forecasting, Risk Scoring & Relief Dispatch API",
    version="1.0.0"
)

# Enable CORS for local dev and embedded widgets
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API subrouters
app.include_router(stage1_router, prefix="/api/v1")
app.include_router(stage2_router, prefix="/api/v1")
app.include_router(stage3_router, prefix="/api/v1")
app.include_router(simulation_router, prefix="/api/v1")

# Locate static folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "system": "IFEWRAS",
        "stage1_status": "ACTIVE",
        "stage2_status": "ACTIVE",
        "stage3_status": "ACTIVE"
    }
