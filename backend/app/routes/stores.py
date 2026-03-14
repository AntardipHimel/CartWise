from fastapi import APIRouter
from app.services.data_loader import load_stores

router = APIRouter()


@router.get("/stores")
async def get_stores():
    stores = load_stores()
    return {"stores": [s.model_dump() for s in stores]}
