from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.drying_optimization.schemas import DryRecommendationResponse
from app.drying_optimization.service import get_dry_recommendation


router = APIRouter(prefix="/api/dry-recommendation", tags=["dry-recommendation"])


@router.get("/recommend", response_model=DryRecommendationResponse)
async def recommend(
    scenario: str = Query(DEFAULT_DEMO_SCENARIO, description="Demo scenario: single_household or family4_household"),
    member_id: str | None = Query(None, description="Member id"),
    washer_id: str | None = Query(None, description="Washer id"),
    region: str | None = Query(None, description="Region preset name"),
    address: str | None = Query(None, description="Road or parcel address"),
    address_type: str = Query("auto", description="Address type: auto, road, parcel"),
    nx: int | None = Query(None, description="KMA short-term forecast grid x"),
    ny: int | None = Query(None, description="KMA short-term forecast grid y"),
    latitude: float | None = Query(None, description="WGS84 latitude"),
    longitude: float | None = Query(None, description="WGS84 longitude"),
    mid_land_reg_id: str | None = Query(None, description="KMA mid-term land forecast code"),
    mid_ta_reg_id: str | None = Query(None, description="KMA mid-term temperature forecast code"),
    laundry_weight_kg: float | None = Query(None, gt=0, description="Laundry weight in kg"),
    has_delicate_items: bool | None = Query(None, description="Whether delicate items are included"),
    needs_fast_dry: bool | None = Query(None, description="Whether fast drying is needed"),
    has_outdoor_space: bool | None = Query(None, description="Whether outdoor drying space exists"),
    has_dryer: bool | None = Query(None, description="Whether a dryer is available"),
    odor_sensitive: bool | None = Query(None, description="Whether odor is a concern"),
    indoor_humidity: int | None = Query(None, ge=0, le=100, description="Indoor humidity"),
    indoor_temperature: float | None = Query(None, description="Indoor temperature"),
    airflow_level: int | None = Query(None, ge=0, le=100, description="Indoor airflow level"),
    dehumidifier_on: bool | None = Query(None, description="Whether a dehumidifier is on"),
    final_spin_rpm: int | None = Query(None, ge=0, description="Final spin RPM"),
    pre_spin_weight_kg: float | None = Query(None, ge=0, description="Pre-spin laundry weight"),
    post_spin_weight_kg: float | None = Query(None, ge=0, description="Post-spin laundry weight"),
) -> DryRecommendationResponse:
    defaults = get_demo_scenario(scenario)

    try:
        return await get_dry_recommendation(
            member_id=member_id or defaults.member_id,
            washer_id=washer_id or defaults.washer_id,
            region=region or defaults.region,
            address=address,
            address_type=address_type,
            nx=nx,
            ny=ny,
            latitude=latitude,
            longitude=longitude,
            mid_land_reg_id=mid_land_reg_id,
            mid_ta_reg_id=mid_ta_reg_id,
            laundry_weight_kg=laundry_weight_kg if laundry_weight_kg is not None else defaults.dry_laundry_weight_kg,
            has_delicate_items=has_delicate_items if has_delicate_items is not None else defaults.has_delicate_items,
            needs_fast_dry=needs_fast_dry if needs_fast_dry is not None else defaults.needs_fast_dry,
            has_outdoor_space=has_outdoor_space if has_outdoor_space is not None else defaults.has_outdoor_space,
            has_dryer=has_dryer if has_dryer is not None else defaults.has_dryer,
            odor_sensitive=odor_sensitive if odor_sensitive is not None else defaults.odor_sensitive,
            indoor_humidity=indoor_humidity if indoor_humidity is not None else defaults.indoor_humidity,
            indoor_temperature=indoor_temperature if indoor_temperature is not None else defaults.indoor_temperature,
            airflow_level=airflow_level if airflow_level is not None else defaults.airflow_level,
            dehumidifier_on=dehumidifier_on if dehumidifier_on is not None else defaults.dehumidifier_on,
            final_spin_rpm=final_spin_rpm if final_spin_rpm is not None else defaults.final_spin_rpm,
            pre_spin_weight_kg=pre_spin_weight_kg,
            post_spin_weight_kg=post_spin_weight_kg,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
