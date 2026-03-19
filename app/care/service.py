from __future__ import annotations

from datetime import datetime

from app.care.schemas import (
    CareChecklistItemResponse,
    CareContentCardResponse,
    CareSummaryResponse,
)
from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.screen_schemas import ScreenActionResponse, ScreenMetaResponse


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
            screen=ScreenMetaResponse(
                title="케어",
                subtitle="세탁기 관리와 의류 관리 팁",
                route="/care",
                active_tab="care",
                primary_action=ScreenActionResponse(
                    key="open_washer_cleaning",
                    label="세탁통 관리 보기",
                    route="/care/washer-cleaning",
                    style="primary",
                    badge=None,
                ),
                secondary_action=ScreenActionResponse(
                    key="open_device",
                    label="디바이스 확인",
                    route="/device",
                    style="secondary",
                    badge=None,
                ),
            ),
            headline="오늘의 홈케어 요약",
            summary="체크리스트와 추천 가이드를 한 화면에서 볼 수 있도록 정리했습니다.",
            reward_points=5600,
            checklist=[
                CareChecklistItemResponse(label="세탁통 상태 확인", done=True, priority="high"),
                CareChecklistItemResponse(label="필터 점검", done=False, priority="medium"),
                CareChecklistItemResponse(label="건조기 환기 확인", done=False, priority="medium"),
            ],
            featured_cards=[
                CareContentCardResponse(
                    key="washer_cleaning",
                    category="세탁기 관리",
                    image_key="washer_cleaning",
                    title="세탁통 관리 팁",
                    summary="세탁조 냄새를 줄이는 주간 관리 루틴입니다.",
                    route="/care/washer-cleaning",
                    cta_label="가이드 보기",
                ),
                CareContentCardResponse(
                    key="fabric_tips",
                    category="의류 관리",
                    image_key="fabric_guide",
                    title="옷감별 케어 가이드",
                    summary="자주 입는 의류를 오래 쓰는 세탁 팁을 모았습니다.",
                    route="/care/fabric-guide",
                    cta_label="팁 보기",
                ),
            ],
        )
