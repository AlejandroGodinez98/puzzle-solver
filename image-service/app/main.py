from fastapi import FastAPI
from app.routers.image_router import router as image_router

app = FastAPI(
    title="Puzzle Solver - Image Processing Service",
    version="1.0.0"
)

app.include_router(image_router)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "UP"}
