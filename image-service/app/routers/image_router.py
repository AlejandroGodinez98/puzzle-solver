from fastapi import APIRouter, UploadFile, File
from app.services.image_validator import validate_image


router = APIRouter(prefix="/api/v1/images")

@router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    
    content = await validate_image(file)
    
    return {
        "filename": file.filename,
        "size": len(content)
    }