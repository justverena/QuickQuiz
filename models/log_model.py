from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class LogEntry(BaseModel):
    service: str
    level: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    message: Optional[str] = None
    timestamp: Optional[str] = None