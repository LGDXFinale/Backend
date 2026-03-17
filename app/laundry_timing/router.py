from __future__ import annotations

from fastapi import APIRouter, Query

from app.laundry_timing.schemas import (
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


@router.get("/recommend", response_model=LaundryRecommendationResponse)
async def recommend_laundry_timing(
    current_weight: float = Query(3.5, gt=0, description="현재 세탁물 무게(kg)"),
    washer_capacity: float = Query(8.0, gt=0, description="세탁기 용량(kg)"),
    hours_since_last_wash: float = Query(48.0, ge=0, description="마지막 세탁 후 경과 시간"),
    weight_increase: float = Query(0.7, ge=0, description="최근 증가한 세탁물 무게(kg)"),
    region: str | None = Query("서울", description="대표 지역 이름 또는 별칭"),
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
        current_weight=current_weight,
        washer_capacity=washer_capacity,
        hours_since_last_wash=hours_since_last_wash,
        weight_increase=weight_increase,
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
