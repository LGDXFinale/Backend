from __future__ import annotations

from datetime import datetime

from app.demo_defaults import DEFAULT_DEMO_SCENARIO, get_demo_scenario
from app.menu.schemas import MenuLinkResponse, MenuSectionResponse, MenuSummaryResponse
from app.screen_schemas import ScreenActionResponse, ScreenMetaResponse


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
            screen=ScreenMetaResponse(
                title="메뉴",
                subtitle="내 정보와 자주 쓰는 설정 모음",
                route="/menu",
                active_tab="menu",
                primary_action=ScreenActionResponse(
                    key="open_notifications",
                    label="알림 설정",
                    route="/menu/notifications",
                    style="primary",
                    badge=None,
                ),
                secondary_action=ScreenActionResponse(
                    key="open_home",
                    label="홈으로 이동",
                    route="/home",
                    style="ghost",
                    badge=None,
                ),
            ),
            profile_name="LG ThinQ 사용자",
            profile_summary=f"{defaults.region} 생활권 기준 추천 사용 중",
            quick_actions=[
                ScreenActionResponse(
                    key="manage_address",
                    label="주소 관리",
                    route="/menu/address",
                    style="secondary",
                    badge=None,
                ),
                ScreenActionResponse(
                    key="open_device",
                    label="내 기기 확인",
                    route="/device",
                    style="secondary",
                    badge=None,
                ),
            ],
            sections=[
                MenuSectionResponse(
                    key="profile",
                    title="내 정보",
                    items=[
                        MenuLinkResponse(
                            key="profile",
                            label="프로필",
                            icon_key="profile",
                            route="/menu/profile",
                            badge=None,
                        ),
                        MenuLinkResponse(
                            key="devices",
                            label="내 기기",
                            icon_key="device",
                            route="/device",
                            badge=None,
                        ),
                    ],
                ),
                MenuSectionResponse(
                    key="settings",
                    title="설정",
                    items=[
                        MenuLinkResponse(
                            key="notifications",
                            label="알림 설정",
                            icon_key="notification",
                            route="/menu/notifications",
                            badge=None,
                        ),
                        MenuLinkResponse(
                            key="address",
                            label="주소 관리",
                            icon_key="location",
                            route="/menu/address",
                            badge="필수",
                        ),
                    ],
                ),
            ],
        )
