from __future__ import annotations

from fastapi import APIRouter, Query

from app.demo_defaults import (
    DEMO_CURRENT_LOAD_KG,
    DEMO_HOUSEHOLD_SIZE,
    DEMO_HOURS_SINCE_LAST_WASH,
    DEMO_MEMBER_ID,
    DEMO_REGION,
    DEMO_SENSOR_LOAD_KG,
    DEMO_URGENT_CLOTHING_COUNT,
    DEMO_WASHER_CAPACITY_KG,
    DEMO_WASHER_ID,
    DEMO_WEIGHT_INCREASE_KG,
)
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
    region: str | None = Query(None, description="미리 정의된 지역 이름 또는 별칭"),
    address: str | None = Query(None, description="동/읍/면까지 포함한 실제 주소"),
    address_type: str = Query("auto", description="주소 유형: auto, road, parcel"),
    nx: int | None = Query(None, description="단기예보 격자 X 좌표"),
    ny: int | None = Query(None, description="단기예보 격자 Y 좌표"),
    latitude: float | None = Query(None, description="WGS84 위도"),
    longitude: float | None = Query(None, description="WGS84 경도"),
    mid_land_reg_id: str | None = Query(None, description="중기육상예보 지역 코드"),
    mid_ta_reg_id: str | None = Query(None, description="중기기온예보 지역 코드"),
) -> WeeklyWeatherResponse:
    return await service.get_weekly_weather(
        region=region,
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
    member_id: str = Query(DEMO_MEMBER_ID, description="회원 ID"),
    washer_id: str = Query(DEMO_WASHER_ID, description="세탁기 ID"),
    current_weight: float = Query(DEMO_CURRENT_LOAD_KG, gt=0, description="현재 적재량(kg)"),
    washer_capacity: float = Query(DEMO_WASHER_CAPACITY_KG, gt=0, description="세탁기 용량(kg)"),
    basket_sensor_weight_kg: float | None = Query(DEMO_SENSOR_LOAD_KG, ge=0, description="스마트 바구니 센서 무게(kg)"),
    manual_refresh: bool = Query(False, description="수동 새로고침 여부"),
) -> CurrentLoadResponse:
    return service.get_current_load_snapshot(
        member_id=member_id,
        washer_id=washer_id,
        current_weight=current_weight,
        washer_capacity=washer_capacity,
        basket_sensor_weight_kg=basket_sensor_weight_kg,
        manual_refresh=manual_refresh,
    )


@router.get("/load/predict", response_model=FutureLoadPredictionResponse)
async def predict_future_load(
    member_id: str = Query(DEMO_MEMBER_ID, description="회원 ID"),
    washer_id: str = Query(DEMO_WASHER_ID, description="세탁기 ID"),
    current_weight: float = Query(DEMO_CURRENT_LOAD_KG, gt=0, description="현재 적재량(kg)"),
    washer_capacity: float = Query(DEMO_WASHER_CAPACITY_KG, gt=0, description="세탁기 용량(kg)"),
    household_size: int = Query(DEMO_HOUSEHOLD_SIZE, ge=1, description="가구원 수"),
    hours_ahead: int = Query(48, ge=1, le=168, description="예측 시간 범위"),
    weight_increase: float = Query(DEMO_WEIGHT_INCREASE_KG, ge=0, description="최근 증가한 세탁물 무게(kg)"),
    urgent_clothing_count: int = Query(DEMO_URGENT_CLOTHING_COUNT, ge=0, description="긴급 세탁 의류 수"),
    basket_sensor_weight_kg: float | None = Query(DEMO_SENSOR_LOAD_KG, ge=0, description="스마트 바구니 센서 무게(kg)"),
    region: str | None = Query(DEMO_REGION, description="대표 지역 이름 또는 별칭"),
    address: str | None = Query(None, description="상세 주소"),
    address_type: str = Query("auto", description="주소 유형: auto, road, parcel"),
    nx: int | None = Query(None, description="단기예보 격자 X 좌표"),
    ny: int | None = Query(None, description="단기예보 격자 Y 좌표"),
    latitude: float | None = Query(None, description="WGS84 위도"),
    longitude: float | None = Query(None, description="WGS84 경도"),
    mid_land_reg_id: str | None = Query(None, description="중기육상예보 지역 코드"),
    mid_ta_reg_id: str | None = Query(None, description="중기기온예보 지역 코드"),
) -> FutureLoadPredictionResponse:
    return await service.predict_future_load(
        member_id=member_id,
        washer_id=washer_id,
        current_weight=current_weight,
        washer_capacity=washer_capacity,
        household_size=household_size,
        hours_ahead=hours_ahead,
        weight_increase=weight_increase,
        urgent_clothing_count=urgent_clothing_count,
        basket_sensor_weight_kg=basket_sensor_weight_kg,
        region=region,
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
    member_id: str = Query(DEMO_MEMBER_ID, description="회원 ID"),
    washer_id: str = Query(DEMO_WASHER_ID, description="세탁기 ID"),
    current_weight: float = Query(DEMO_CURRENT_LOAD_KG, gt=0, description="현재 적재량(kg)"),
    washer_capacity: float = Query(DEMO_WASHER_CAPACITY_KG, gt=0, description="세탁기 용량(kg)"),
    hours_since_last_wash: float = Query(DEMO_HOURS_SINCE_LAST_WASH, ge=0, description="마지막 세탁 후 경과 시간"),
    weight_increase: float = Query(DEMO_WEIGHT_INCREASE_KG, ge=0, description="최근 증가한 세탁물 무게(kg)"),
    household_size: int = Query(DEMO_HOUSEHOLD_SIZE, ge=1, description="가구원 수"),
    urgent_clothing_count: int = Query(DEMO_URGENT_CLOTHING_COUNT, ge=0, description="긴급 세탁 의류 수"),
    basket_sensor_weight_kg: float | None = Query(DEMO_SENSOR_LOAD_KG, ge=0, description="스마트 바구니 센서 무게(kg)"),
    manual_refresh: bool = Query(False, description="수동 새로고침 여부"),
    forecast_hours: int = Query(48, ge=1, le=168, description="미래 적재량 예측 범위"),
    region: str | None = Query(DEMO_REGION, description="대표 지역 이름 또는 별칭"),
    address: str | None = Query(None, description="상세 주소"),
    address_type: str = Query("auto", description="주소 유형: auto, road, parcel"),
    nx: int | None = Query(None, description="단기예보 격자 X 좌표"),
    ny: int | None = Query(None, description="단기예보 격자 Y 좌표"),
    latitude: float | None = Query(None, description="WGS84 위도"),
    longitude: float | None = Query(None, description="WGS84 경도"),
    mid_land_reg_id: str | None = Query(None, description="중기육상예보 지역 코드"),
    mid_ta_reg_id: str | None = Query(None, description="중기기온예보 지역 코드"),
) -> LaundryRecommendationResponse:
    return await service.build_laundry_recommendation(
        member_id=member_id,
        washer_id=washer_id,
        current_weight=current_weight,
        washer_capacity=washer_capacity,
        hours_since_last_wash=hours_since_last_wash,
        weight_increase=weight_increase,
        household_size=household_size,
        urgent_clothing_count=urgent_clothing_count,
        basket_sensor_weight_kg=basket_sensor_weight_kg,
        manual_refresh=manual_refresh,
        forecast_hours=forecast_hours,
        region=region,
        address=address,
        address_type=address_type,
        nx=nx,
        ny=ny,
        latitude=latitude,
        longitude=longitude,
        mid_land_reg_id=mid_land_reg_id,
        mid_ta_reg_id=mid_ta_reg_id,
    )
