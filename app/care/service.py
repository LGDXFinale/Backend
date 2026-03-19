from __future__ import annotations

from datetime import datetime

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.care.schemas import (
    CareChecklistItemResponse,
    CareContentCardResponse,
    CareSummaryResponse,
)


class CareSummaryService:
    def build_care_summary(
        self,
        *,
        scenario: str = DEFAULT_DEMO_SCENARIO,
        member_id: str | None = None,
    ) -> CareSummaryResponse:
        defaults = get_demo_scenario(scenario)
        resolved_member_id = member_id or defaults.member_id
        now = datetime.now().isoformat(timespec="seconds")
        return CareSummaryResponse(
            generated_at=now,
            member_id=resolved_member_id,
            headline="오늘의 홈케어 요약",
            reward_points=5600,
            checklist=[
                CareChecklistItemResponse(label="세탁통 상태 확인", done=True),
                CareChecklistItemResponse(label="필터 점검", done=False),
                CareChecklistItemResponse(label="건조기 환기 확인", done=False),
            ],
            featured_cards=[
                CareContentCardResponse(
                    key="washer_cleaning",
                    title="세탁통 관리 팁",
                    summary="세탁조 냄새를 줄이는 주간 관리 루틴입니다.",
                    route="/care/washer-cleaning",
                ),
                CareContentCardResponse(
                    key="fabric_tips",
                    title="옷감별 케어 가이드",
                    summary="자주 입는 의류를 오래 쓰는 세탁 팁을 모았습니다.",
                    route="/care/fabric-guide",
                ),
            ],
        )
