from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


RecommendationLevel = Literal["low", "medium", "high"]


class WeatherDayResponse(BaseModel):
    date: str = Field(..., description="예보 날짜")
    source: str = Field(..., description="예보 출처")
    min_temp: float | None = Field(None, description="최저 기온")
    max_temp: float | None = Field(None, description="최고 기온")
    precipitation_probability: int | None = Field(None, description="강수 확률")
    relative_humidity: int | None = Field(None, description="상대 습도")
    feels_like_temp: float | None = Field(None, description="체감 온도")
    summary: str | None = Field(None, description="예보 요약")


class AirQualityResponse(BaseModel):
    station_name: str = Field(..., description="측정소 이름")
    station_address: str | None = Field(None, description="측정소 주소")
    measured_at: str | None = Field(None, description="측정 시각")
    pm10: int | None = Field(None, description="미세먼지 농도")
    pm10_grade: str | None = Field(None, description="미세먼지 등급")
    pm25: int | None = Field(None, description="초미세먼지 농도")
    pm25_grade: str | None = Field(None, description="초미세먼지 등급")
    source: str = Field(..., description="데이터 출처")


class WeeklyWeatherResponse(BaseModel):
    generated_at: str = Field(..., description="응답 생성 시각")
    location: dict[str, str | int] = Field(..., description="조회에 사용된 위치 정보")
    sources: dict[str, str] = Field(..., description="예보 소스 기준 시각")
    current_air_quality: AirQualityResponse | None = Field(
        None,
        description="현재 대기질 정보",
    )
    current_air_quality_error: str | None = Field(
        None,
        description="대기질 조회 실패 메시지",
    )
    days: list[WeatherDayResponse] = Field(..., description="주간 예보 목록")


class RegionPresetResponse(BaseModel):
    name: str = Field(..., description="대표 지역 이름")
    aliases: list[str] = Field(..., description="검색 가능한 별칭")
    latitude: float = Field(..., description="대표 위도")
    longitude: float = Field(..., description="대표 경도")
    nx: int = Field(..., description="기상청 격자 X 좌표")
    ny: int = Field(..., description="기상청 격자 Y 좌표")
    mid_land_reg_id: str = Field(..., description="중기육상예보 코드")
    mid_ta_reg_id: str = Field(..., description="중기기온예보 코드")
    description: str = Field(..., description="지역 설명")


class LaundryTimingConsiderationResponse(BaseModel):
    category: str = Field(..., description="판단 요소 이름")
    score: int = Field(..., ge=0, le=100, description="판단 점수")
    summary: str = Field(..., description="핵심 요약")
    details: list[str] = Field(..., description="상세 근거")


class LaundryTimingWeatherSnapshotResponse(BaseModel):
    source: str = Field(..., description="날씨 데이터 출처")
    location_label: str | None = Field(None, description="판단에 사용한 위치 라벨")
    days_considered: int = Field(..., ge=0, description="판단에 사용한 예보 일수")
    rain_expected: bool = Field(..., description="가까운 시일 내 비 예보 여부")
    high_humidity: bool = Field(..., description="가까운 시일 내 고습도 여부")
    outdoor_drying_friendly: bool = Field(..., description="자연 건조에 유리한 날 존재 여부")
    weather_summary: str = Field(..., description="날씨 요약")
    weather_error: str | None = Field(None, description="날씨 조회 실패 메시지")


class LaundryRecommendationResponse(BaseModel):
    generated_at: str = Field(..., description="추천 생성 시각")
    current_weight: float = Field(..., gt=0, description="현재 세탁물 무게(kg)")
    washer_capacity: float = Field(..., gt=0, description="세탁기 용량(kg)")
    load_ratio: float = Field(..., ge=0, le=100, description="세탁기 적재율(%)")
    weight_increase: float = Field(..., ge=0, description="최근 증가한 세탁물 무게(kg)")
    hours_since_last_wash: float = Field(..., ge=0, description="마지막 세탁 후 경과 시간")
    rain_expected: bool = Field(..., description="가까운 시일 내 비 예보 여부")
    high_humidity: bool = Field(..., description="가까운 시일 내 고습도 여부")
    weather_summary: str = Field(..., description="날씨 요약")
    recommendation: str = Field(..., description="세탁 타이밍 추천 문구")
    reason: str = Field(..., description="추천 이유")
    recommend_level: RecommendationLevel = Field(..., description="추천 강도")
    status_image_key: str = Field(..., description="상태 이미지 키")
    execution_window: str = Field(..., description="권장 실행 시점")
    timing_score: int = Field(..., ge=0, le=100, description="세탁 필요도 종합 점수")
    weather: LaundryTimingWeatherSnapshotResponse = Field(..., description="날씨 판단 스냅샷")
    top_considerations: list[LaundryTimingConsiderationResponse] = Field(
        ...,
        description="주요 판단 요소",
    )
    action_items: list[str] = Field(..., description="즉시 실행 팁")
