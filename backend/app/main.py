from fastapi import FastAPI

from app.routers import reports

app = FastAPI(
    title="SafeRoute API",
    description="Anonymous security incident reporting",
    version="0.1.0",
)

app.include_router(reports)


@app.get("/")
async def root():
    return {"message": "Hello World"}
