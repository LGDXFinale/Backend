from __future__ import annotations

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.care import router as care_router
from app.device import router as device_router
from app.fabric_damage import router as fabric_damage_router
from app.home import router as home_router
from app.laundry_timing import router as laundry_timing_router
from app.laundry_progress import router as laundry_progress_router
from app.menu import router as menu_router
from app.drying_optimization.router import router as drying_optimization_router


app = FastAPI(
    title="Laundry Backend",
    version="0.1.0",
    description="Docs-driven FastAPI backend for laundry recommendation features.",
)


def _load_cors_allowed_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


cors_allowed_origins = _load_cors_allowed_origins()
if cors_allowed_origins:
    allow_all = "*" in cors_allowed_origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if allow_all else cors_allowed_origins,
        allow_credentials=not allow_all,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(fabric_damage_router)
app.include_router(home_router)
app.include_router(device_router)
app.include_router(care_router)
app.include_router(menu_router)
app.include_router(laundry_timing_router)
app.include_router(laundry_progress_router)
app.include_router(drying_optimization_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "message": "Laundry backend is running.",
        "docs": "/docs",
        "features": [
            "home",
            "device",
            "care",
            "menu",
            "laundry_timing",
            "fabric_damage",
            "laundry_progress",
            "drying_optimization",
        ],
    }


if __name__ == "__main__":
    # 파일 직접 실행보다는 모듈 실행이 안전하지만, 실수로 실행해도 서버가 뜨도록 둔다.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
