from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.drying_optimization.schemas import DryRecommendationResponse
from app.drying_optimization.service import get_dry_recommendation


router = APIRouter(prefix="/api/dry-recommendation", tags=["dry-recommendation"])


@router.get("/recommend", response_model=DryRecommendationResponse)
def recommend(
    city: str = Query("Seoul", description="날씨 조회 도시"),
    laundry_weight_kg: float = Query(3.0, gt=0, description="세탁물 무게(kg)"),
    has_delicate_items: bool = Query(False, description="민감 소재 포함 여부"),
    needs_fast_dry: bool = Query(False, description="빠른 건조 필요 여부"),
    has_outdoor_space: bool = Query(True, description="실외 건조 가능 여부"),
    humidity_override: int | None = Query(None, ge=0, le=100, description="습도 수동 입력"),
    temperature_override: float | None = Query(None, description="기온 수동 입력"),
    is_raining_override: bool | None = Query(None, description="강수 여부 수동 입력"),
) -> DryRecommendationResponse:
    try:
        return get_dry_recommendation(
            city=city,
            laundry_weight_kg=laundry_weight_kg,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
            has_outdoor_space=has_outdoor_space,
            humidity_override=humidity_override,
            temperature_override=temperature_override,
            is_raining_override=is_raining_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
