import pytest
from io import BytesIO
from PIL import Image

TEST_MAX_FILE_SIZE = 10 * 1024 * 1024

def test_upload_valid_png(client):
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


@pytest.mark.parametrize(
    "filename, content, content_type, expected_status, expected_detail",
    [
        # test_upload_empty_file
        ("empty.png", b"", "image/png", 400, "File Cannot Be Empty"),
        # test_upload_large_file
        ("large_content.png", b"A" * (TEST_MAX_FILE_SIZE + 1), "image/png", 413, "File Exceeds The Maximum Allowed Size"),
        # test_upload_unsupported_media_type
        ("document.pdf", b"Fake PDF content", "application/pdf", 415, "Unsupported Media Type"),
        # test_upload_invalid_image_content
        ("image.png", b"This is not a real PNG image", "image/png", 400, "Invalid Or Corrupted Image")
    ],
        ids=[
        "empty-file",
        "file-exceeds-size-limit",
        "unsupported-media-type",
        "invalid-image-content"
    ]
)   
def test_upload_invalid_files(
    client,
    filename,
    content,
    content_type,
    expected_status,
    expected_detail
):
    
    response = client.post(
        "/api/v1/images/upload",
        files={
            "file": (
                filename,
                content,
                content_type
            )
        }
    )
        
    assert response.status_code == expected_status
    assert response.json()["detail"] == expected_detail