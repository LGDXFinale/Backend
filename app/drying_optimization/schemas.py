from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


DryRecommendLevel = Literal["low", "medium", "high"]
OdorRiskLevel = Literal["low", "medium", "high"]


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


class IndoorEnvironmentResponse(BaseModel):
    indoor_humidity: int = Field(..., ge=0, le=100, description="실내 습도")
    indoor_temperature: float = Field(..., description="실내 온도")
    airflow_level: int = Field(..., ge=0, le=100, description="실내 공기 흐름 수준")
    dehumidifier_on: bool = Field(..., description="제습기 사용 여부")


class MoistureEstimationResponse(BaseModel):
    estimated_moisture_percent: int = Field(..., ge=0, le=100, description="추정 수분도")
    residual_water_kg: float = Field(..., ge=0, description="남은 수분 무게")
    weight_change_kg: float | None = Field(None, description="탈수 전후 무게 차이")
    final_spin_rpm: int = Field(..., ge=0, description="최종 탈수 RPM")
    odor_risk_level: OdorRiskLevel = Field(..., description="냄새 발생 위험도")


class DryEnvironmentAnalysisResponse(BaseModel):
    indoor_score: int = Field(..., ge=0, le=100, description="실내 건조 적합도")
    outdoor_score: int = Field(..., ge=0, le=100, description="실외 건조 적합도")
    preferred_environment: str = Field(..., description="우선 추천 환경")
    summary: str = Field(..., description="환경 비교 요약")


class DryingConsiderationResponse(BaseModel):
    category: str = Field(..., description="판단 요소 이름")
    score: int = Field(..., ge=0, le=100, description="판단 점수")
    summary: str = Field(..., description="핵심 요약")
    details: list[str] = Field(..., description="상세 설명")


class DryRecommendationResponse(BaseModel):
    generated_at: str = Field(..., description="추천 생성 시각")
    member_id: str = Field(..., description="회원 ID")
    washer_id: str = Field(..., description="세탁기 ID")
    dry_rec_id: str = Field(..., description="건조 추천 ID")
    dry_rec_time: int = Field(..., ge=0, description="예상 건조 시간(분)")
    dry_rec_method: int = Field(..., ge=1, le=4, description="건조 방식 코드")
    dry_rec_method_name: str = Field(..., description="건조 방식 이름")
    recommendation: str = Field(..., description="추천 문구")
    reason: str = Field(..., description="추천 이유")
    recommend_level: DryRecommendLevel = Field(..., description="추천 강도")
    status_image_key: str = Field(..., description="상태 이미지 키")
    caution: str = Field(..., description="주의사항")
    energy_tip: str = Field(..., description="에너지 절약 팁")
    weather_info: DryWeatherInfoResponse = Field(..., description="실외 날씨 정보")
    indoor_environment: IndoorEnvironmentResponse = Field(..., description="실내 건조 환경")
    moisture_estimation: MoistureEstimationResponse = Field(..., description="수분도 추정 결과")
    environment_analysis: DryEnvironmentAnalysisResponse = Field(..., description="실내외 환경 비교")
    top_considerations: list[DryingConsiderationResponse] = Field(
        ...,
        description="주요 판단 요소",
    )
    action_items: list[str] = Field(..., description="즉시 실행 팁")
