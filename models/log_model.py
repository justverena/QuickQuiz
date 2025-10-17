from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class Log(BaseModel):
    timestamp: datetime
    endpoint: str
    payload: Dict
    response: Dict
    status: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None