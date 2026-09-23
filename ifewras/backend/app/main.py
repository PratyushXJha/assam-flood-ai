"""Main FastAPI Application Entrypoint for FloodCast AI.
AI flood early warning, forecasting & rescue allocation for Assam.
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_NAME, APP_VERSION
from app.alerts.dispatcher import dispatcher
from app.api.routes_stage1 import router as stage1_router
from app.api.routes_stage2 import router as stage2_router
from app.api.routes_stage3 import router as stage3_router
from app.api.routes_simulation import router as simulation_router
from app.api.routes_alerts import router as alerts_router
from app.api.routes_assistant import router as assistant_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    dispatcher.start()  # background throttled SMS / voice senders
    yield
    await dispatcher.stop()


app = FastAPI(
    title=f"{APP_NAME} - Flood Early Warning, Forecasting & Rescue Allocation",
    description="ASDMA / SDRF multi-stage flood early warning, gauge forecasting, risk scoring, relief dispatch and throttled SMS / AI voice alert API",
    version=APP_VERSION,
    lifespan=lifespan
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
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(assistant_router, prefix="/api/v1")

# Locate static folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))

    @app.get("/receiver", include_in_schema=False)
    async def serve_receiver():
        """Resident device view: receives alerts, sounds the buzzer and plays the AI voice message."""
        return FileResponse(os.path.join(STATIC_DIR, "receiver.html"))

@app.get("/health")
async def health_check():
    return {
        "status": "HEALTHY",
        "system": APP_NAME,
        "version": APP_VERSION,
        "stage1_status": "ACTIVE",
        "stage2_status": "ACTIVE",
        "stage3_status": "ACTIVE"
    }
