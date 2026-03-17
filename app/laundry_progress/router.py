from fastapi import APIRouter
from app.laundry_progress.service import get_laundry_progress_status
from app.laundry_progress.schemas import LaundryProgressResponse

router = APIRouter(prefix="/api/laundry-progress", tags=["laundry-progress"])


@router.get("/status", response_model=LaundryProgressResponse)
def get_laundry_progress():
    return get_laundry_progress_status()