from typing import Optional
from pydantic import BaseModel


class LaundryProgressResponse(BaseModel):
    wash_status_id: str
    washer_id: str
    conta_level: str
    wash_status: int
    time_info: str

    current_status: str
    remaining_time: Optional[int]
    expected_end_time: str
    progress_percent: int
    conta_percent: int
    status_image_key: str