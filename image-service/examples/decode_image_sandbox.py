import cv2
import numpy as np
from pathlib import Path
from bounding_box_utils import remove_duplicate_boxes
from row_utils import (
    group_characters_by_rows,
    filter_rows_by_length,
    filter_rows_by_spacing
)

# image_path = Path("../samples/sudoku/photo_sudoku_01.jpeg")
image_path = Path("../samples/word-search/word_search_01.jpg")

# Read the compressed image bytes
image_bytes = image_path.read_bytes()

# Convert bytes into NumPy array
image_array = np.frombuffer(image_bytes, dtype=np.uint8)

# Decode the image into pixels
image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

if image is None:
    raise ValueError("Could not decode image")

print("Type:", type(image))
print("Shape:", image.shape)
print("Data type:", image.dtype)
print("First pixel:", image[0, 0])
print("Image height:", image.shape[0])
print("Image width:", image.shape[1])
print("Number of channels:", image.shape[2])

# pasar a escala de grises
gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

print("Original shape:", image.shape)
print("Grayscale shape:", gray_image.shape)
print("Grayscale pixel:", gray_image[100, 200])

# binarizacion (thresholding) convertir a blanco/negro
threshold_value = 127

_, binary_image = cv2.threshold(
    gray_image,
    threshold_value,
    255,
    cv2.THRESH_BINARY
)

inverted_image = cv2.bitwise_not(binary_image)
kernel = cv2.getStructuringElement(
    cv2.MORPH_RECT,
    (3, 3)
)

dilated_image = cv2.dilate(
    inverted_image,
    kernel,
    iterations=1
)

cv2.imwrite(
    "examples/images/dilated_output.png",
    dilated_image
)

# Detect individual character candidates
MIN_CHARACTER_AREA = 20
MAX_CHARACTER_AREA = 500

# Contours for larger regions
region_contours, hierarchy = cv2.findContours(
    dilated_image,
    cv2.RETR_TREE,
    cv2.CHAIN_APPROX_SIMPLE
)

# Contours for individual character candidates
character_contours, _ = cv2.findContours(
    inverted_image,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

character_boxes = []

for contour in character_contours:
    x, y, w, h = cv2.boundingRect(contour)
    area = w * h

    if MIN_CHARACTER_AREA <= area <= MAX_CHARACTER_AREA:
        character_boxes.append((x, y, w, h))

print("Possible characters:", len(character_boxes))

characters_image = image.copy()

for x, y, w, h in character_boxes:
    cv2.rectangle(
        characters_image,
        (x, y),
        (x + w, y + h),
        (0, 255, 0),
        1
    )

cv2.imwrite(
    "examples/images/character_boxes_output.png",
    characters_image
)

character_centers = []

for x, y, w, h in character_boxes:
    center_x = x + w / 2
    center_y = y + h / 2

    character_centers.append((center_x, center_y))

print("Detected character centers:", len(character_centers))
print("First 10 centers:", character_centers[:10])

rows = group_characters_by_rows(character_centers, tolerance=3)

print(f"Detected rows: {len(rows)}")

filtered_by_length = filter_rows_by_length(
    rows,
    min_characters=5
)

print(f"Rows after length filter: {len(filtered_by_length)}")

filtered_by_spacing = filter_rows_by_spacing(
    filtered_by_length,
    max_cv=0.2
)

print(f"Rows after spacing filter: {len(filtered_by_spacing)}")

candidate_boxes = []

for contour in region_contours:
    x, y, w, h = cv2.boundingRect(contour)

    if w * h > 5000:
        candidate_boxes.append((x, y, w, h))

unique_boxes = remove_duplicate_boxes(candidate_boxes)

print("Candidate boxes:", len(candidate_boxes))
print("Unique boxes:", len(unique_boxes))

for contour in region_contours:
    x, y, w, h = cv2.boundingRect(contour)

    area = w * h

    if area > 5000:
        print(f"Bounding Box: x={x}, y={y}, w={w}, h={h}, area={area}")
print("Contours found:", len(region_contours))

bounding_boxes_image = image.copy()
possible_grids = []

for x, y, w, h in unique_boxes:
    aspect_ratio = w / h

    print(f"Aspect ratio: {aspect_ratio:.2f}")
    if 0.8 <= aspect_ratio <= 1.5:
        possible_grids.append((x, y, w, h))

    cv2.rectangle(
        bounding_boxes_image,
        (x, y),
        (x + w, y + h),
        (0, 0, 255),
        2
    )

print("Possible grids:", possible_grids)

cv2.imwrite(
    "examples/images/bounding_boxes_output.png",
    bounding_boxes_image
)
# Create a copy to avoid modifying the original image
contours_image = image.copy()

# Draw all detected contours in green
cv2.drawContours(
    contours_image,
    region_contours,
    -1,
    (0, 255, 0),
    1
)

cv2.imwrite(
    "examples/images/contours_output.png",
    contours_image
)

print("Binary image shape:", binary_image.shape)
print("Binary pixel:", binary_image[100, 200])

# Vamos a guardar el resultado utilizando OpenCV
output_path = Path("examples/images/binary_output.png")

success = cv2.imwrite(str(output_path), binary_image)

if not success:
    raise RuntimeError("Failed to save binary image")

print("Binary image saved:", output_path)

# Siguiente concepto: Adaptive Thresholding
adaptive_image = cv2.adaptiveThreshold(
    gray_image,
    255,
    cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
    cv2.THRESH_BINARY,
    11,
    2
)

cv2.imwrite("examples/images/adaptive_output.png", adaptive_image)

height, width = gray_image.shape

print("Height:", height)
print("Width:", width)

# Example: crop a rectangular region
grid_region = gray_image[110:475, 20:465]

cv2.imwrite("examples/images/grid_region.png", grid_region)