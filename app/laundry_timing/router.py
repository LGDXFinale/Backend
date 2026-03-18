from __future__ import annotations

from fastapi import APIRouter, Query

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.laundry_timing.schemas import (
    CurrentLoadResponse,
    FutureLoadPredictionResponse,
    LaundryRecommendationResponse,
    RegionPresetResponse,
    WeeklyWeatherResponse,
)
from app.laundry_timing.service import LaundryTimingService


router = APIRouter(prefix="/api/laundry-timing", tags=["laundry-timing"])
service = LaundryTimingService()


@router.get("/weather/regions", response_model=list[RegionPresetResponse])
async def list_weather_regions() -> list[RegionPresetResponse]:
    return service.list_weather_regions()


@router.get("/weather/weekly", response_model=WeeklyWeatherResponse)
async def read_weekly_weather(
    scenario: str = Query(DEFAULT_DEMO_SCENARIO, description="Demo scenario: single_household or family4_household"),
    region: str | None = Query(None, description="Region preset name"),
    address: str | None = Query(None, description="Detailed address"),
    address_type: str = Query("auto", description="Address type: auto, road, parcel"),
    nx: int | None = Query(None, description="KMA grid X"),
    ny: int | None = Query(None, description="KMA grid Y"),
    latitude: float | None = Query(None, description="WGS84 latitude"),
    longitude: float | None = Query(None, description="WGS84 longitude"),
    mid_land_reg_id: str | None = Query(None, description="KMA mid-term land forecast code"),
    mid_ta_reg_id: str | None = Query(None, description="KMA mid-term temperature forecast code"),
) -> WeeklyWeatherResponse:
    defaults = get_demo_scenario(scenario)

    return await service.get_weekly_weather(
        region=region or defaults.region,
        address=address,
        address_type=address_type,
        nx=nx,
        ny=ny,
        latitude=latitude,
        longitude=longitude,
        mid_land_reg_id=mid_land_reg_id,
        mid_ta_reg_id=mid_ta_reg_id,
    )


@router.get("/load/current", response_model=CurrentLoadResponse)
def read_current_load(
    scenario: str = Query(DEFAULT_DEMO_SCENARIO, description="Demo scenario: single_household or family4_household"),
    member_id: str | None = Query(None, description="Member ID"),
    washer_id: str | None = Query(None, description="Washer ID"),
    current_weight: float | None = Query(None, gt=0, description="Current load weight"),
    washer_capacity: float | None = Query(None, gt=0, description="Washer capacity"),
    basket_sensor_weight_kg: float | None = Query(None, ge=0, description="Basket sensor weight"),
    manual_refresh: bool = Query(False, description="Manual refresh"),
) -> CurrentLoadResponse:
    defaults = get_demo_scenario(scenario)

    return service.get_current_load_snapshot(
        member_id=member_id or defaults.member_id,
        washer_id=washer_id or defaults.washer_id,
        current_weight=current_weight if current_weight is not None else defaults.current_load_kg,
        washer_capacity=washer_capacity if washer_capacity is not None else defaults.washer_capacity_kg,
        basket_sensor_weight_kg=basket_sensor_weight_kg if basket_sensor_weight_kg is not None else defaults.sensor_load_kg,
        manual_refresh=manual_refresh,
    )


@router.get("/load/predict", response_model=FutureLoadPredictionResponse)
async def predict_future_load(
    scenario: str = Query(DEFAULT_DEMO_SCENARIO, description="Demo scenario: single_household or family4_household"),
    member_id: str | None = Query(None, description="Member ID"),
    washer_id: str | None = Query(None, description="Washer ID"),
    current_weight: float | None = Query(None, gt=0, description="Current load weight"),
    washer_capacity: float | None = Query(None, gt=0, description="Washer capacity"),
    household_size: int | None = Query(None, ge=1, description="Household size"),
    hours_ahead: int = Query(48, ge=1, le=168, description="Forecast window"),
    weight_increase: float | None = Query(None, ge=0, description="Recent laundry increase"),
    urgent_clothing_count: int | None = Query(None, ge=0, description="Urgent clothing count"),
    basket_sensor_weight_kg: float | None = Query(None, ge=0, description="Basket sensor weight"),
    region: str | None = Query(None, description="Region preset name"),
    address: str | None = Query(None, description="Detailed address"),
    address_type: str = Query("auto", description="Address type: auto, road, parcel"),
    nx: int | None = Query(None, description="KMA grid X"),
    ny: int | None = Query(None, description="KMA grid Y"),
    latitude: float | None = Query(None, description="WGS84 latitude"),
    longitude: float | None = Query(None, description="WGS84 longitude"),
    mid_land_reg_id: str | None = Query(None, description="KMA mid-term land forecast code"),
    mid_ta_reg_id: str | None = Query(None, description="KMA mid-term temperature forecast code"),
) -> FutureLoadPredictionResponse:
    defaults = get_demo_scenario(scenario)

    return await service.predict_future_load(
        member_id=member_id or defaults.member_id,
        washer_id=washer_id or defaults.washer_id,
        current_weight=current_weight if current_weight is not None else defaults.current_load_kg,
        washer_capacity=washer_capacity if washer_capacity is not None else defaults.washer_capacity_kg,
        household_size=household_size if household_size is not None else defaults.household_size,
        hours_ahead=hours_ahead,
        weight_increase=weight_increase if weight_increase is not None else defaults.weight_increase_kg,
        urgent_clothing_count=urgent_clothing_count if urgent_clothing_count is not None else defaults.urgent_clothing_count,
        basket_sensor_weight_kg=basket_sensor_weight_kg if basket_sensor_weight_kg is not None else defaults.sensor_load_kg,
        region=region or defaults.region,
        address=address,
        address_type=address_type,
        nx=nx,
        ny=ny,
        latitude=latitude,
        longitude=longitude,
        mid_land_reg_id=mid_land_reg_id,
        mid_ta_reg_id=mid_ta_reg_id,
    )


@router.get("/recommend", response_model=LaundryRecommendationResponse)
async def recommend_laundry_timing(
    scenario: str = Query(DEFAULT_DEMO_SCENARIO, description="Demo scenario: single_household or family4_household"),
    member_id: str | None = Query(None, description="Member ID"),
    washer_id: str | None = Query(None, description="Washer ID"),
    current_weight: float | None = Query(None, gt=0, description="Current load weight"),
    washer_capacity: float | None = Query(None, gt=0, description="Washer capacity"),
    hours_since_last_wash: float | None = Query(None, ge=0, description="Hours since last wash"),
    weight_increase: float | None = Query(None, ge=0, description="Recent laundry increase"),
    household_size: int | None = Query(None, ge=1, description="Household size"),
    urgent_clothing_count: int | None = Query(None, ge=0, description="Urgent clothing count"),
    basket_sensor_weight_kg: float | None = Query(None, ge=0, description="Basket sensor weight"),
    manual_refresh: bool = Query(False, description="Manual refresh"),
    forecast_hours: int = Query(48, ge=1, le=168, description="Forecast hours"),
    region: str | None = Query(None, description="Region preset name"),
    address: str | None = Query(None, description="Detailed address"),
    address_type: str = Query("auto", description="Address type: auto, road, parcel"),
    nx: int | None = Query(None, description="KMA grid X"),
    ny: int | None = Query(None, description="KMA grid Y"),
    latitude: float | None = Query(None, description="WGS84 latitude"),
    longitude: float | None = Query(None, description="WGS84 longitude"),
    mid_land_reg_id: str | None = Query(None, description="KMA mid-term land forecast code"),
    mid_ta_reg_id: str | None = Query(None, description="KMA mid-term temperature forecast code"),
) -> LaundryRecommendationResponse:
    defaults = get_demo_scenario(scenario)

    return await service.build_laundry_recommendation(
        member_id=member_id or defaults.member_id,
        washer_id=washer_id or defaults.washer_id,
        current_weight=current_weight if current_weight is not None else defaults.current_load_kg,
        washer_capacity=washer_capacity if washer_capacity is not None else defaults.washer_capacity_kg,
        hours_since_last_wash=hours_since_last_wash if hours_since_last_wash is not None else defaults.hours_since_last_wash,
        weight_increase=weight_increase if weight_increase is not None else defaults.weight_increase_kg,
        household_size=household_size if household_size is not None else defaults.household_size,
        urgent_clothing_count=urgent_clothing_count if urgent_clothing_count is not None else defaults.urgent_clothing_count,
        basket_sensor_weight_kg=basket_sensor_weight_kg if basket_sensor_weight_kg is not None else defaults.sensor_load_kg,
        manual_refresh=manual_refresh,
        forecast_hours=forecast_hours,
        region=region or defaults.region,
        address=address,
        address_type=address_type,
        nx=nx,
        ny=ny,
        latitude=latitude,
        longitude=longitude,
        mid_land_reg_id=mid_land_reg_id,
        mid_ta_reg_id=mid_ta_reg_id,
    )
