from io import BytesIO
from fastapi.testclient import TestClient
from PIL import Image
from app.main import app

TEST_MAX_FILE_SIZE = 10 * 1024 * 1024

client = TestClient(app)

def test_upload_valid_png():
    # Arrange
    image_buffer = BytesIO()

    image = Image.new("RGB", (100, 100))
    image.save(image_buffer, format="PNG")

    image_content = image_buffer.getvalue()

    # Act
    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "test.png",
                image_content,
                "image/png"
            )
        }
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "filename": "test.png",
        "size": len(image_content)
    }

def test_upload_empty_file():
    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "empty.png",
                b"",
                "image/png"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File Cannot Be Empty"

def test_upload_large_file():

    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "large_content.png",
                b"A" * (TEST_MAX_FILE_SIZE + 1),
                "image/png"
            )
        }
    )
    assert response.status_code == 413
    assert response.json()["detail"] == "File Exceeds The Maximum Allowed Size"

def test_upload_unsupported_media_type():
    # Arrange
    file_content = b"Fake PDF content"

    # Act
    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "document.pdf",
                file_content,
                "application/pdf"
            )
        }
    )

    # Assert
    assert response.status_code == 415
    assert response.json()["detail"] == "Unsupported Media Type"

def test_upload_invalid_image_content():

    file_content = b"This is not a real PNG image"
    
    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                "image.png",
                file_content,
                "image/png"
            )
        }
    )
        
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid Or Corrupted Image"