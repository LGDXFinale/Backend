from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.laundry_timing.schemas import AirQualityResponse, RegionPresetResponse, WeeklyWeatherResponse
from app.utils import (
    AirQualityError,
    PublicDataWeatherError,
    VWorldGeocoderError,
    find_nearest_region_preset,
    geocode_address,
    get_current_air_quality,
    get_region_presets,
    get_weekly_weather,
    latlon_to_grid,
    resolve_region_preset,
)


router = APIRouter(prefix="/api/laundry-timing", tags=["laundry-timing"])


@router.get("/weather/regions", response_model=list[RegionPresetResponse])
async def list_weather_regions() -> list[RegionPresetResponse]:
    responses: list[RegionPresetResponse] = []

    for preset in get_region_presets():
        nx, ny = latlon_to_grid(preset.latitude, preset.longitude)
        responses.append(
            RegionPresetResponse(
                name=preset.name,
                aliases=list(preset.aliases),
                latitude=preset.latitude,
                longitude=preset.longitude,
                nx=nx,
                ny=ny,
                mid_land_reg_id=preset.mid_land_reg_id,
                mid_ta_reg_id=preset.mid_ta_reg_id,
                description=preset.description,
            )
        )

    return responses


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
    preset = None
    resolved_latitude = latitude
    resolved_longitude = longitude
    address_hint = address

    if region:
        preset = resolve_region_preset(region)
        if preset is None:
            raise HTTPException(
                status_code=404,
                detail=f"지원하지 않는 지역입니다: {region}",
            )

    if address and (resolved_latitude is None or resolved_longitude is None):
        if address_type not in {"auto", "road", "parcel"}:
            raise HTTPException(
                status_code=422,
                detail="address_type은 auto, road, parcel 중 하나여야 합니다.",
            )

        try:
            geocoded = await geocode_address(
                address=address,
                address_type=address_type,  # type: ignore[arg-type]
            )
        except VWorldGeocoderError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

        resolved_latitude = geocoded.latitude
        resolved_longitude = geocoded.longitude
        address_hint = geocoded.refined_text or geocoded.address

    if preset is None and resolved_latitude is not None and resolved_longitude is not None:
        # 중기예보는 권역 단위이므로 가장 가까운 대표 권역으로 매핑한다.
        preset = find_nearest_region_preset(resolved_latitude, resolved_longitude)
        if address_hint is None:
            address_hint = preset.name

    resolved_mid_land_reg_id = mid_land_reg_id or (preset.mid_land_reg_id if preset else None)
    resolved_mid_ta_reg_id = mid_ta_reg_id or (preset.mid_ta_reg_id if preset else None)

    if resolved_mid_land_reg_id is None or resolved_mid_ta_reg_id is None:
        raise HTTPException(
            status_code=422,
            detail=(
                "mid_land_reg_id와 mid_ta_reg_id를 직접 주거나 "
                "region, latitude/longitude, address 중 하나를 사용해야 합니다."
            ),
        )

    if nx is None or ny is None:
        if resolved_latitude is not None and resolved_longitude is not None:
            nx, ny = latlon_to_grid(resolved_latitude, resolved_longitude)
        elif preset is not None:
            nx, ny = latlon_to_grid(preset.latitude, preset.longitude)
        else:
            raise HTTPException(
                status_code=422,
                detail=(
                    "nx, ny를 직접 주거나 latitude, longitude, address "
                    "또는 region 프리셋을 사용해야 합니다."
                ),
            )

    try:
        weather = await get_weekly_weather(
            nx=nx,
            ny=ny,
            mid_land_reg_id=resolved_mid_land_reg_id,
            mid_ta_reg_id=resolved_mid_ta_reg_id,
        )
    except PublicDataWeatherError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    current_air_quality = None
    current_air_quality_error = None
    if resolved_latitude is not None and resolved_longitude is not None and address_hint:
        try:
            air_quality = await get_current_air_quality(
                latitude=resolved_latitude,
                longitude=resolved_longitude,
                address_hint=_build_air_quality_address_hint(address_hint),
            )
        except AirQualityError as exc:
            # 날씨 예보 자체는 계속 제공하고, 대기질만 비운다.
            current_air_quality_error = str(exc)
            air_quality = None

        if air_quality is not None:
            current_air_quality = AirQualityResponse.model_validate(air_quality.__dict__)

    weather["current_air_quality"] = current_air_quality
    weather["current_air_quality_error"] = current_air_quality_error
    return WeeklyWeatherResponse.model_validate(weather)


def _build_air_quality_address_hint(address: str) -> str:
    # 측정소 검색은 주소 일부만 넣는 편이 결과가 더 안정적인 경우가 많다.
    tokens = [token for token in address.split() if token]
    if len(tokens) >= 2:
        return " ".join(tokens[:2])
    return address
