from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


MaterialType = Literal[
    "cotton",
    "linen",
    "wool",
    "silk",
    "knit",
    "denim",
    "polyester",
    "nylon",
    "spandex",
    "towel",
    "down",
    "functional",
]

ColorGroup = Literal["white", "light", "dark", "vivid", "black", "denim"]
ContaminationLevel = Literal["low", "medium", "high"]
SensorType = Literal["weight", "humidity", "fabric", "contamination", "vibration"]
SpinLevel = Literal["low", "medium", "high"]


class ClothingItemInput(BaseModel):
    cloth_id: str | None = Field(None, description="세탁물 식별자")
    name: str = Field(..., description="세탁물 이름")
    material_type: MaterialType = Field(..., description="소재 유형")
    color_group: ColorGroup = Field(..., description="색상 그룹")
    weight_g: float = Field(..., gt=0, description="세탁물 무게(g)")
    contamination_level: ContaminationLevel = Field("low", description="오염도")
    has_print: bool = Field(False, description="프린팅 여부")
    has_zipper: bool = Field(False, description="지퍼/금속 부자재 포함 여부")
    is_new_clothing: bool = Field(False, description="새 옷 여부")


class SensorReadingInput(BaseModel):
    sensor_id: str | None = Field(None, description="센서 데이터 식별자")
    sensor_type: SensorType = Field(..., description="센서 종류")
    measured_value: float | str = Field(..., description="센서 측정값")
    unit: str = Field(..., description="측정 단위")
    measured_at: datetime | None = Field(None, description="측정 시간")


class WashStatusInput(BaseModel):
    contamination_level: ContaminationLevel | None = Field(None, description="세탁조 오염도")
    load_status_percent: int | None = Field(None, ge=0, le=100, description="세탁기 적재율(%)")


class FabricDamageSolutionRequest(BaseModel):
    member_id: str | None = Field(None, description="회원 ID")
    washer_id: str | None = Field(None, description="세탁기 ID")
    wash_id: str | None = Field(None, description="세탁 세션 ID")
    washer_capacity_kg: float = Field(12.0, gt=0, description="세탁기 용량(kg)")
    items: list[ClothingItemInput] = Field(..., min_length=1, description="세탁물 목록")
    sensor_data: list[SensorReadingInput] = Field(
        default_factory=list,
        description="센서 데이터 목록",
    )
    wash_status: WashStatusInput | None = Field(None, description="세탁 상태 입력")

    @field_validator("items")
    @classmethod
    def validate_items(cls, items: list[ClothingItemInput]) -> list[ClothingItemInput]:
        if not items:
            raise ValueError("세탁물은 최소 1개 이상이어야 합니다.")
        return items


class DetectedItemResponse(BaseModel):
    name: str
    material_type: MaterialType
    color_group: ColorGroup
    weight_g: float
    contamination_level: ContaminationLevel
    care_labels: list[str]


class SensorAnalysisResponse(BaseModel):
    total_weight_g: float
    sensor_weight_g: float | None
    estimated_load_percent: int
    dominant_contamination_level: ContaminationLevel
    notes: list[str]


class RiskItemResponse(BaseModel):
    category: str
    score: int = Field(..., ge=0, le=100)
    reasons: list[str]
    caution_items: list[str]


class RiskAssessmentResponse(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    summary: str
    top_risks: list[RiskItemResponse]
    separate_wash_required: bool


class WashRecommendationResponse(BaseModel):
    course: str
    water_temperature_celsius: int
    spin_level: SpinLevel
    detergent_type: str
    drying_tip: str
    immediate_actions: list[str]
    separating_groups: list[list[str]]


class FabricDamageSolutionResponse(BaseModel):
    wash_id: str | None
    member_id: str | None
    washer_id: str | None
    analyzed_items: list[DetectedItemResponse]
    sensor_analysis: SensorAnalysisResponse
    risk_assessment: RiskAssessmentResponse
    recommendation: WashRecommendationResponse
