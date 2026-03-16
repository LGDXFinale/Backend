from datetime import datetime
from fastapi import APIRouter

router = APIRouter(prefix="/api/laundry-progress", tags=["laundry-progress"])


@router.get("/status")
def get_laundry_progress():
    # 기존 DB 컬럼 형태를 가정한 더미 데이터
    wash_status = {
        "wash_status_id": "WS001",
        "washer_id": "W001",
        "conta_level": "중",
        "load_status": "세탁중",
        "time_info": "2026-03-16 15:00:00"
    }

    # 기존 DB 값 사용
    washer_id = wash_status["washer_id"]
    conta_level = wash_status["conta_level"]
    load_status = wash_status["load_status"]
    expected_end_time = wash_status["time_info"]

    # 화면용 파생값 계산
    if conta_level == "상":
        cleaned_ratio = 35.0
    elif conta_level == "중":
        cleaned_ratio = 55.0
    else:
        cleaned_ratio = 75.0

    if load_status == "대기":
        progress_percent = 0
        status_image_key = "waiting"
    elif load_status == "세탁중":
        progress_percent = 45
        status_image_key = "washing"
    elif load_status == "헹굼중":
        progress_percent = 70
        status_image_key = "rinsing"
    elif load_status == "탈수중":
        progress_percent = 90
        status_image_key = "spinning"
    elif load_status == "종료":
        progress_percent = 100
        cleaned_ratio = 100.0
        status_image_key = "done"
    else:
        progress_percent = 0
        status_image_key = "unknown"

    # 남은 시간 계산
    remaining_time = None
    try:
        end_dt = datetime.strptime(expected_end_time, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        diff_minutes = int((end_dt - now).total_seconds() / 60)
        remaining_time = diff_minutes if diff_minutes > 0 else 0
    except ValueError:
        remaining_time = None

    return {
        "wash_status_id": wash_status["wash_status_id"],
        "washer_id": washer_id,
        "conta_level": conta_level,              # 원래 DB 값
        "load_status": load_status,              # 원래 DB 값
        "time_info": expected_end_time,          # 원래 DB 값
        "current_status": load_status,           # 화면용 별칭
        "remaining_time": remaining_time,        # 화면용 계산값
        "expected_end_time": expected_end_time,  # 화면용 별칭
        "progress_percent": progress_percent,    # 화면용 계산값
        "cleaned_ratio": cleaned_ratio,          # 화면용 계산값
        "status_image_key": status_image_key     # 프론트 이미지 매핑용
    }