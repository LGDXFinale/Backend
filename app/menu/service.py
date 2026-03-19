from __future__ import annotations

from datetime import datetime

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.menu.schemas import MenuLinkResponse, MenuSectionResponse, MenuSummaryResponse


class MenuSummaryService:
    def build_menu_summary(
        self,
        *,
        scenario: str = DEFAULT_DEMO_SCENARIO,
        member_id: str | None = None,
    ) -> MenuSummaryResponse:
        defaults = get_demo_scenario(scenario)
        resolved_member_id = member_id or defaults.member_id
        return MenuSummaryResponse(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            member_id=resolved_member_id,
            profile_name="LG ThinQ 사용자",
            profile_summary=f"{defaults.region} 생활권 기준 추천 사용 중",
            sections=[
                MenuSectionResponse(
                    title="내 정보",
                    items=[
                        MenuLinkResponse(
                            key="profile",
                            label="프로필",
                            route="/menu/profile",
                        ),
                        MenuLinkResponse(
                            key="devices",
                            label="내 기기",
                            route="/device",
                        ),
                    ],
                ),
                MenuSectionResponse(
                    title="설정",
                    items=[
                        MenuLinkResponse(
                            key="notifications",
                            label="알림 설정",
                            route="/menu/notifications",
                        ),
                        MenuLinkResponse(
                            key="address",
                            label="주소 관리",
                            route="/menu/address",
                        ),
                    ],
                ),
            ],
        )
