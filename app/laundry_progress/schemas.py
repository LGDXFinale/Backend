from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ContaminationLevel = Literal["상", "중", "하"]


class LaundryProgressSensorSummaryResponse(BaseModel):
    current_load_kg: float = Field(..., ge=0, description="현재 세탁물 무게")
    washer_capacity_kg: float = Field(..., gt=0, description="세탁기 용량")
    load_ratio: float = Field(..., ge=0, le=100, description="현재 적재율")
    load_variation_kg: float = Field(..., description="세탁 중 감지된 부하 변화량")
    contamination_sensor_percent: int | None = Field(None, ge=0, le=100, description="센서 오염 잔량")
    final_spin_rpm: int | None = Field(None, ge=0, description="현재 또는 마지막 탈수 RPM")


class LaundryProgressResponse(BaseModel):
    generated_at: str = Field(..., description="응답 생성 시각")
    member_id: str = Field(..., description="회원 ID")
    wash_status_id: str = Field(..., description="세탁 상태 ID")
    washer_id: str = Field(..., description="세탁기 ID")
    conta_level: ContaminationLevel = Field(..., description="초기 오염도")
    wash_status: int = Field(..., ge=0, le=4, description="세탁 상태 코드")
    time_info: str = Field(..., description="현재 기준 시각")
    current_status: str = Field(..., description="현재 상태 라벨")
    remaining_time: int | None = Field(None, ge=0, description="남은 시간(분)")
    expected_end_time: str = Field(..., description="예상 종료 시각")
    progress_percent: int = Field(..., ge=0, le=100, description="전체 진행률")
    conta_percent: int = Field(..., ge=0, le=100, description="남은 오염도 퍼센트")
    status_image_key: str = Field(..., description="상태 이미지 키")
    elapsed_minutes: int = Field(..., ge=0, description="누적 진행 시간")
    base_cycle_minutes: int = Field(..., ge=1, description="기본 세탁 시간")
    dynamic_total_minutes: int = Field(..., ge=1, description="부하 변화를 반영한 총 예상 시간")
    load_variation_detected: bool = Field(..., description="부하 변화 감지 여부")
    update_reason: str = Field(..., description="시간 재계산 사유")
    stage_notes: list[str] = Field(..., description="상태별 참고 메모")
    sensor_summary: LaundryProgressSensorSummaryResponse = Field(..., description="센서 요약")
