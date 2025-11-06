from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
import os
from typing import Optional, List, Dict

app = FastAPI(title="Log Service")

LOG_FILE = "logs.json"

class LogEntry(BaseModel):
    service: str
    level: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    message: Optional[str] = None
    response: Optional[Dict] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[str] = None
    
def read_logs() -> List[dict]:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []
        
def write_logs(logs: List[dict]):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, indent=4, ensure_ascii=False)
        
@app.post("/logs/")
async def create_log(entry: LogEntry):
    logs = read_logs()
    entry.timestamp = datetime.utcnow().isoformat()
    logs.append(entry.dict())
    write_logs(logs)
    return {"status": "success", "message": "Log entry saved"}

@app.get("/logs/")
async def get_logs(service: Optional[str] = None, level: Optional[str] = None):
    logs = read_logs()
    if service:
        logs = [log for log in logs if log["service"] == service ]
    if level:
        logs = [log for log in logs if log["level"].upper() == level.upper()]
        
@app.get("/")
async def root():
    return {"message": "JSON log service is running"}