from fastapi import FastAPI
from routers import logs

app = FastAPI(title="Log Service")

app.include_router(logs.router)

@app.get("/")
async def root():
    return {"message": "Log service is running"}