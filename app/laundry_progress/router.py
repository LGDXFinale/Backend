from datetime import datetime
from fastapi import APIRouter

router = APIRouter(prefix="/api/laundry-progress", tags=["laundry-progress"])


@router.get("/status")
def get_laundry_progress():
    # ERD 기준 더미 데이터
    wash_status_data = {
        "wash_status_id": "WS001",
        "washer_id": "W001",
        "conta_level": "중",                 # ERD 원본값 유지
        "wash_status": 1,                   # NUMBER (예: 0=대기, 1=세탁중, 2=헹굼중, 3=탈수중, 4=종료)
        "time_info": "2026-03-16 15:00:00"  # DATETIME
    }

    # ERD 원본값
    wash_status_id = wash_status_data["wash_status_id"]
    washer_id = wash_status_data["washer_id"]
    conta_level = wash_status_data["conta_level"]
    wash_status = wash_status_data["wash_status"]
    time_info = wash_status_data["time_info"]

    # 오염도 -> 퍼센트 변환 (화면용 파생값)
    conta_percent_map = {
        "상": 80,
        "중": 55,
        "하": 30
    }
    conta_percent = conta_percent_map.get(conta_level, 0)

    # 세탁 상태 변환
    status_map = {
        0: {"label": "대기", "progress_percent": 0, "status_image_key": "waiting"},
        1: {"label": "세탁중", "progress_percent": 45, "status_image_key": "washing"},
        2: {"label": "헹굼중", "progress_percent": 70, "status_image_key": "rinsing"},
        3: {"label": "탈수중", "progress_percent": 90, "status_image_key": "spinning"},
        4: {"label": "종료", "progress_percent": 100, "status_image_key": "done"},
    }

    status_info = status_map.get(
        wash_status,
        {"label": "알 수 없음", "progress_percent": 0, "status_image_key": "unknown"}
    )

    current_status = status_info["label"]
    progress_percent = status_info["progress_percent"]
    status_image_key = status_info["status_image_key"]

    # 종료 시 세탁 진행률 100%
    if wash_status == 4:
        conta_percent = 100

    # 남은 시간 계산
    remaining_time = None
    try:
        end_dt = datetime.strptime(time_info, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff_minutes = int((end_dt - now).total_seconds() / 60)
        remaining_time = diff_minutes if diff_minutes > 0 else 0
    except ValueError:
        remaining_time = None

    return {
        # ERD 원본값
        "wash_status_id": wash_status_id,
        "washer_id": washer_id,
        "conta_level": conta_level,
        "wash_status": wash_status,
        "time_info": time_info,

        # 화면용 파생값
        "current_status": current_status,
        "remaining_time": remaining_time,
        "expected_end_time": time_info,
        "progress_percent": progress_percent,
        "conta_percent": conta_percent,
        "status_image_key": status_image_key
    }