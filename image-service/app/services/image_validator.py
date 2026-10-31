from fastapi import UploadFile, HTTPException
from PIL import Image, UnidentifiedImageError
from io import BytesIO

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG"}

async def validate_image(file: UploadFile) -> bytes:
    # 1. Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported Media Type")
    
    # 2. Read file with size limit
    content = await file.read(MAX_FILE_SIZE + 1)
    content_length = len(content)

    # 3. Validate empty files
    if content_length == 0:
        raise HTTPException(status_code=400, detail="File Cannot Be Empty")

    # 4. Validate maximum file size
    if content_length > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File Exceeds The Maximum Allowed Size")

    # 5. Validate actual image format using Pillow
    try:
        with Image.open(BytesIO(content)) as image:
            
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise HTTPException(status_code=415, detail="Unsupported Media Type")
            
            image.verify()
            
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(status_code=400, detail="Invalid Or Corrupted Image")

    # 6. Return validated image content
    return content