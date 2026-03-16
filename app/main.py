from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.fabric_damage import router as fabric_damage_router
from app.laundry_timing import router as laundry_timing_router
from app.laundry_progress import router as laundry_progress_router


app = FastAPI(
    title="Laundry Backend",
    version="0.1.0",
    description="Docs-driven FastAPI backend for laundry recommendation features.",
)

app.include_router(fabric_damage_router)
app.include_router(laundry_timing_router)
app.include_router(laundry_progress_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
async def root() -> dict[str, object]:
    return {
        "message": "Laundry backend is running.",
        "docs": "/docs",
        "features": [
            "laundry_timing",
            "fabric_damage",
            "laundry_progress",
            "drying_optimization",
        ],
    }


if __name__ == "__main__":
    # 파일 직접 실행보다는 모듈 실행이 안전하지만, 실수로 실행해도 서버가 뜨도록 둔다.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
