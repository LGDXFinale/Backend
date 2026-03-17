from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DryRecommendLevel = Literal["low", "medium", "high"]


class DryWeatherInfoResponse(BaseModel):
    source: str = Field(..., description="날씨 데이터 출처")
    city: str = Field(..., description="조회 도시")
    weather_main: str | None = Field(None, description="대표 날씨 상태")
    weather_description: str | None = Field(None, description="상세 날씨 설명")
    is_raining: bool = Field(..., description="강수 여부")
    humidity: int = Field(..., ge=0, le=100, description="습도")
    temperature: float = Field(..., description="기온")
    wind_speed_mps: float | None = Field(None, description="풍속")
    weather_error: str | None = Field(None, description="날씨 조회 실패 메시지")


class DryingConsiderationResponse(BaseModel):
    category: str = Field(..., description="판단 요소 이름")
    score: int = Field(..., ge=0, le=100, description="판단 점수")
    summary: str = Field(..., description="핵심 요약")
    details: list[str] = Field(..., description="상세 설명")


class DryRecommendationResponse(BaseModel):
    generated_at: str = Field(..., description="추천 생성 시각")
    dry_rec_id: str = Field(..., description="건조 추천 ID")
    dry_rec_time: int = Field(..., ge=0, description="예상 건조 시간(분)")
    dry_rec_method: int = Field(..., ge=1, le=3, description="건조 방식 코드")
    dry_rec_method_name: str = Field(..., description="건조 방식 이름")
    recommendation: str = Field(..., description="추천 문구")
    reason: str = Field(..., description="추천 이유")
    recommend_level: DryRecommendLevel = Field(..., description="추천 강도")
    status_image_key: str = Field(..., description="상태 이미지 키")
    caution: str = Field(..., description="주의사항")
    energy_tip: str = Field(..., description="에너지 절약 팁")
    weather_info: DryWeatherInfoResponse = Field(..., description="날씨 정보")
    top_considerations: list[DryingConsiderationResponse] = Field(
        ...,
        description="주요 판단 요소",
    )
    action_items: list[str] = Field(..., description="즉시 실행 팁")
