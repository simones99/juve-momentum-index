from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, brief, health, matches, momentum, push, travel
from app.config import get_settings

settings = get_settings()

app = FastAPI(title="Juve Momentum Index API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(matches.router, prefix="/api/v1")
app.include_router(momentum.router, prefix="/api/v1")
app.include_router(brief.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(travel.router, prefix="/api/v1")
app.include_router(push.router, prefix="/api/v1")
