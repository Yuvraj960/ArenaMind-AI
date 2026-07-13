from fastapi import APIRouter
from app.models.schemas import BaseResponse

router = APIRouter()


@router.get("/", response_model=BaseResponse)
async def health_check():
    return BaseResponse(success=True)