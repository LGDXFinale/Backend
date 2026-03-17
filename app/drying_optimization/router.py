from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.demo_defaults import (
    DEMO_AIRFLOW_LEVEL,
    DEMO_CITY,
    DEMO_DEHUMIDIFIER_ON,
    DEMO_DRY_LAUNDRY_WEIGHT_KG,
    DEMO_FINAL_SPIN_RPM,
    DEMO_HAS_DELICATE_ITEMS,
    DEMO_HAS_DRYER,
    DEMO_HAS_OUTDOOR_SPACE,
    DEMO_INDOOR_HUMIDITY,
    DEMO_INDOOR_TEMPERATURE,
    DEMO_MEMBER_ID,
    DEMO_NEEDS_FAST_DRY,
    DEMO_ODOR_SENSITIVE,
    DEMO_WASHER_ID,
)
from app.drying_optimization.schemas import DryRecommendationResponse
from app.drying_optimization.service import get_dry_recommendation


router = APIRouter(prefix="/api/dry-recommendation", tags=["dry-recommendation"])


@router.get("/recommend", response_model=DryRecommendationResponse)
def recommend(
    member_id: str = Query(DEMO_MEMBER_ID, description="회원 ID"),
    washer_id: str = Query(DEMO_WASHER_ID, description="세탁기 ID"),
    city: str = Query(DEMO_CITY, description="날씨 조회 도시"),
    laundry_weight_kg: float = Query(DEMO_DRY_LAUNDRY_WEIGHT_KG, gt=0, description="세탁물 무게(kg)"),
    has_delicate_items: bool = Query(DEMO_HAS_DELICATE_ITEMS, description="민감 소재 포함 여부"),
    needs_fast_dry: bool = Query(DEMO_NEEDS_FAST_DRY, description="빠른 건조 필요 여부"),
    has_outdoor_space: bool = Query(DEMO_HAS_OUTDOOR_SPACE, description="실외 건조 가능 여부"),
    has_dryer: bool = Query(DEMO_HAS_DRYER, description="건조기 보유 여부"),
    odor_sensitive: bool = Query(DEMO_ODOR_SENSITIVE, description="냄새에 민감한 의류 여부"),
    indoor_humidity: int = Query(DEMO_INDOOR_HUMIDITY, ge=0, le=100, description="실내 습도"),
    indoor_temperature: float = Query(DEMO_INDOOR_TEMPERATURE, description="실내 온도"),
    airflow_level: int = Query(DEMO_AIRFLOW_LEVEL, ge=0, le=100, description="실내 공기 흐름 수준"),
    dehumidifier_on: bool = Query(DEMO_DEHUMIDIFIER_ON, description="제습기 사용 여부"),
    final_spin_rpm: int = Query(DEMO_FINAL_SPIN_RPM, ge=0, description="최종 탈수 RPM"),
    pre_spin_weight_kg: float | None = Query(None, ge=0, description="탈수 전 무게"),
    post_spin_weight_kg: float | None = Query(None, ge=0, description="탈수 후 무게"),
    humidity_override: int | None = Query(None, ge=0, le=100, description="실외 습도 수동 입력"),
    temperature_override: float | None = Query(None, description="실외 기온 수동 입력"),
    is_raining_override: bool | None = Query(None, description="강수 여부 수동 입력"),
) -> DryRecommendationResponse:
    try:
        return get_dry_recommendation(
            member_id=member_id,
            washer_id=washer_id,
            city=city,
            laundry_weight_kg=laundry_weight_kg,
            has_delicate_items=has_delicate_items,
            needs_fast_dry=needs_fast_dry,
            has_outdoor_space=has_outdoor_space,
            has_dryer=has_dryer,
            odor_sensitive=odor_sensitive,
            indoor_humidity=indoor_humidity,
            indoor_temperature=indoor_temperature,
            airflow_level=airflow_level,
            dehumidifier_on=dehumidifier_on,
            final_spin_rpm=final_spin_rpm,
            pre_spin_weight_kg=pre_spin_weight_kg,
            post_spin_weight_kg=post_spin_weight_kg,
            humidity_override=humidity_override,
            temperature_override=temperature_override,
            is_raining_override=is_raining_override,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
