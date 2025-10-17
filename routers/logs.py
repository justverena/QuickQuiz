from fastapi import APIRouter, HTTPException
from models.log_model import Log
from db import logs_collection

router = APIRouter()

@router.post("/logs")
async def create_log(log: Log):
    log_dict = log.model_dump()
    result = await logs_collection.insert_one(log_dict)
    if result.inserted_id:
        return {"message": "Log saved", "id": str(result.inserted_id)}
    raise HTTPException(status_code=500, detail="Failed to save log")