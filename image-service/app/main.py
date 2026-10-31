from fastapi import FastAPI, UploadFile, File, HTTPException
from PIL import Image, UnidentifiedImageError
from io import BytesIO

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png"
}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}

app = FastAPI(
    title="Puzzle Solver - Image Processing Service",
    version="1.0.0"
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "UP"}

@app.post("/api/v1/images/upload")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported Media Type")
    
    content = await file.read(MAX_FILE_SIZE + 1)
    content_length = len(content)

    if content_length == 0:
        raise HTTPException(status_code=400, detail="File Cannot Be Empty")

    if content_length > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File Exceeds The Maximum Allowed Size")

    try:
        with Image.open(BytesIO(content)) as image:
            
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(status_code=415, detail="Unsupported Media Type")
            
            image.verify()
            
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="Invalid Or Corrupted Image")
    
    return {
        "filename": file.filename,
        "size": content_length
    }