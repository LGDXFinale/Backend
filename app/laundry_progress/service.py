from __future__ import annotations

from datetime import datetime, timedelta

from app.laundry_progress.schemas import LaundryProgressResponse


STATUS_MAP = {
    0: {"label": "대기", "progress_percent": 0, "status_image_key": "waiting", "remaining_minutes": 90},
    1: {"label": "세탁중", "progress_percent": 45, "status_image_key": "washing", "remaining_minutes": 35},
    2: {"label": "헹굼중", "progress_percent": 70, "status_image_key": "rinsing", "remaining_minutes": 18},
    3: {"label": "탈수중", "progress_percent": 90, "status_image_key": "spinning", "remaining_minutes": 7},
    4: {"label": "종료", "progress_percent": 100, "status_image_key": "done", "remaining_minutes": 0},
}

CONTA_PERCENT_MAP = {
    "상": 80,
    "중": 55,
    "하": 30,
}


def get_laundry_progress_status() -> LaundryProgressResponse:
    now = datetime.now()

    # ERD 기준 더미 데이터
    wash_status_data = {
        "wash_status_id": "WS001",
        "washer_id": "W001",
        "conta_level": "중",
        "wash_status": 1,
    }

    wash_status_id = wash_status_data["wash_status_id"]
    washer_id = wash_status_data["washer_id"]
    conta_level = wash_status_data["conta_level"]
    wash_status = wash_status_data["wash_status"]

    status_info = STATUS_MAP.get(
        wash_status,
        {"label": "알 수 없음", "progress_percent": 0, "status_image_key": "unknown", "remaining_minutes": 0},
    )

    remaining_time = status_info["remaining_minutes"]
    expected_end_dt = now + timedelta(minutes=remaining_time)
    time_info = now.strftime("%Y-%m-%d %H:%M:%S")
    expected_end_time = expected_end_dt.strftime("%Y-%m-%d %H:%M:%S")

    conta_percent = CONTA_PERCENT_MAP.get(conta_level, 0)
    if wash_status == 4:
        conta_percent = 100

    return LaundryProgressResponse(
        wash_status_id=wash_status_id,
        washer_id=washer_id,
        conta_level=conta_level,
        wash_status=wash_status,
        time_info=time_info,
        current_status=status_info["label"],
        remaining_time=remaining_time,
        expected_end_time=expected_end_time,
        progress_percent=status_info["progress_percent"],
        conta_percent=conta_percent,
        status_image_key=status_info["status_image_key"],
    )
