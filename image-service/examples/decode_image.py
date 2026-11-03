"""Experimental OpenCV pipeline for puzzle-page analysis.

Place this file inside image-service/examples/ alongside row_utils.py and
bounding_box_utils.py, then run it from any working directory.
"""

from pathlib import Path

import cv2
import numpy as np

from bounding_box_utils import (
    remove_duplicate_boxes,
    filter_centers_by_box,
    calculate_grid_bounding_box,
    add_grid_padding
)
from row_utils import (
    filter_rows_by_length,
    filter_rows_by_spacing,
    group_characters_by_rows,
    merge_close_centers_in_rows,
    calculate_row_centers_y,
    build_grid_matrix,
    recover_missing_centers_in_rows,
    calculate_reference_x,
    recover_missing_first_centers_in_rows
)
from spacing_utils import (
    calculate_spacing,
    calculate_coefficient_of_variation
)
from cell_utils import (
    extract_cell,
    extract_grid_cells,
    save_grid_cells
)
from ocr_utils import (
    recognize_grid,
    recognize_character
)
from ocr_evaluation_utils import (
    load_ground_truth,
    evaluate_grid_accuracy,
    find_ocr_errors,
    save_failed_cells,
    filter_errors_by_character,
    build_error_preview
)
from grid_visualization_utils import (
    build_grid_preview,
    create_error_mosaic
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent / "images"
IMAGE_PATH = PROJECT_ROOT / "samples" / "word-search" / "word_search_01.jpg"
GROUND_TRUTH_PATH = (
    Path(__file__).resolve().parent
    / "ground_truth"
    / "word_search_02.txt"
)

THRESHOLD = 127
MIN_CHARACTER_AREA = 20
MAX_CHARACTER_AREA = 500
MIN_REGION_AREA = 5000
ROW_TOLERANCE = 3
MIN_CHARACTERS_PER_ROW = 5
MAX_SPACING_CV = 0.2
MIN_GRID_ASPECT_RATIO = 0.8
MAX_GRID_ASPECT_RATIO = 1.5
MIN_DISTANCE = 8


def load_image(path):
    """Decode a JPEG/PNG image into an OpenCV BGR array."""
    image_bytes = path.read_bytes()
    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError(f"Could not decode image: {path}")

    return image


def preprocess_image(image):
    """Generate the representations used by region and character detection."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, THRESHOLD, 255, cv2.THRESH_BINARY)
    inverted = cv2.bitwise_not(binary)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    dilated = cv2.dilate(inverted, kernel, iterations=1)

    adaptive = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
    )

    return {
        "gray": gray,
        "binary": binary,
        "inverted": inverted,
        "dilated": dilated,
        "adaptive": adaptive,
    }


def detect_character_boxes(inverted_image):
    """Return bounding boxes of small external contours (character candidates)."""
    contours, _ = cv2.findContours(
        inverted_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if MIN_CHARACTER_AREA <= w * h <= MAX_CHARACTER_AREA:
            boxes.append((x, y, w, h))

    return boxes


def calculate_character_centers(boxes):
    """Map (x, y, width, height) boxes to their (center_x, center_y)."""
    return [(x + w / 2, y + h / 2) for x, y, w, h in boxes]


def analyze_character_rows(centers):
    """Group character centers, merge nearby fragments, and filter candidate rows."""
    rows = group_characters_by_rows(centers, tolerance=ROW_TOLERANCE)
    merged_rows = merge_close_centers_in_rows(rows, min_distance=MIN_DISTANCE)
    recovered_rows = recover_missing_centers_in_rows(merged_rows)
    long_rows = filter_rows_by_length(recovered_rows, min_characters=MIN_CHARACTERS_PER_ROW)
    regular_rows = filter_rows_by_spacing(long_rows, max_cv=MAX_SPACING_CV)

    return rows, merged_rows, recovered_rows, long_rows, regular_rows


def detect_region_boxes(dilated_image):
    """Detect large regions, then remove overlapping near-duplicate boxes."""
    contours, _ = cv2.findContours(
        dilated_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )

    candidates = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w * h > MIN_REGION_AREA:
            candidates.append((x, y, w, h))

    unique_boxes = remove_duplicate_boxes(candidates)
    return contours, candidates, unique_boxes


def find_possible_grids(boxes):
    """Select roughly rectangular regions as tentative grid candidates."""
    grids = []
    for x, y, w, h in boxes:
        if h == 0:
            continue
        aspect_ratio = w / h
        if MIN_GRID_ASPECT_RATIO <= aspect_ratio <= MAX_GRID_ASPECT_RATIO:
            grids.append((x, y, w, h))
    return grids


def draw_boxes(image, boxes, color, thickness=1):
    """Draw boxes on a copy, leaving the input image unchanged."""
    output = image.copy()
    for x, y, w, h in boxes:
        cv2.rectangle(output, (x, y), (x + w, y + h), color, thickness)
    return output

def draw_character_centers(image, rows, color_by_row=False):
    output_image = image.copy()

    colors = [
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 0, 255),    # Red
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
    ]

    # Draw every character center
    for row_index, row in enumerate(rows):
        color = (
            colors[row_index % len(colors)]
            if color_by_row
            else (0, 255, 0)
        )
        for center in row:
            x = round(center[0])
            y = round(center[1])
            cv2.circle(
                output_image,
                (x, y),
                3,
                color,
                -1
            )

    return output_image

def print_row_statistics(rows, max_cv=0.2):
    for index, row in enumerate(rows):
        x_coordinates = [center[0] for center in row]

        distances = calculate_spacing(x_coordinates)
        cv = calculate_coefficient_of_variation(distances)

        print(
            f"Row {index + 1}: "
            f"Characters={len(row)}, "
            f"CV={cv}"
        )
        if cv is not None and cv > max_cv and len(row) >= 5:
            print(f"  X coordinates: {x_coordinates}")
            print(f"  Distances: {distances}")

def save_debug_images(image, processed, character_boxes, region_boxes, region_contours):
    """Persist the same debugging views used in the original experiment."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    debug_images = {
        "dilated_output.png": processed["dilated"],
        "binary_output.png": processed["binary"],
        "adaptive_output.png": processed["adaptive"],
        "grid_region.png": processed["gray"][110:475, 20:465],
        "character_boxes_output.png": draw_boxes(image, character_boxes, (0, 255, 0)),
        "bounding_boxes_output.png": draw_boxes(image, region_boxes, (0, 0, 255), 2),
    }

    contours_image = image.copy()
    cv2.drawContours(contours_image, region_contours, -1, (0, 255, 0), 1)
    debug_images["contours_output.png"] = contours_image

    for filename, debug_image in debug_images.items():
        target = OUTPUT_DIR / filename
        if not cv2.imwrite(str(target), debug_image):
            raise RuntimeError(f"Failed to save image: {target}")


def main():
    image = load_image(IMAGE_PATH)
    processed = preprocess_image(image)

    character_boxes = detect_character_boxes(processed["inverted"])
    character_centers = calculate_character_centers(character_boxes)
    page_rows, page_merged_rows, page_recovered_rows, page_long_rows, page_regular_rows = (
        analyze_character_rows(character_centers)
    )

    region_contours, candidate_boxes, unique_boxes = detect_region_boxes(
        processed["dilated"]
    )

    contour_areas = []

    for contour in region_contours:
        x, y, w, h = cv2.boundingRect(contour)
        contour_areas.append((w * h, x, y, w, h))

    contour_areas.sort(reverse=True)

    print("\n--- Largest detected contours ---")

    for area, x, y, w, h in contour_areas[:10]:
        print(
            f"Area={area}, "
            f"x={x}, y={y}, w={w}, h={h}"
        )

    possible_grids = find_possible_grids(unique_boxes)

    save_debug_images(
        image, processed, character_boxes, unique_boxes, region_contours
    )

    # Diagnose row detection across the entire page
    print("\n--- Full page row statistics ---")

    print_row_statistics(page_merged_rows)

    cv2.imwrite(
        str(OUTPUT_DIR / "page_colored_rows.png"),
        draw_character_centers(
            image,
            page_regular_rows,
            color_by_row=True
        )
    )
    print("Image shape:", image.shape)
    print("Possible characters:", len(character_boxes))
    print("Detected character centers:", len(character_centers))
    print("Detected rows:", len(page_rows))
    print("Rows after length filter:", len(page_long_rows))
    print("Rows after spacing filter:", len(page_regular_rows))
    print("Candidate boxes:", len(candidate_boxes))
    print("Unique boxes:", len(unique_boxes))
    print("Possible grids:", possible_grids)
    print("Debug images saved to:", OUTPUT_DIR)

    print("\n--- Recovered row lengths ---")

    for index, row in enumerate(page_regular_rows, start=1):
        print(f"Row {index}: {len(row)} centers")

    print("\n--- Row 14 diagnosis ---")

    row_14 = page_regular_rows[13]

    x_coordinates = [center[0] for center in row_14]

    print("X coordinates:", x_coordinates)
    print("Horizontal distances:", calculate_spacing(x_coordinates))

    print("\n--- Horizontal grid reference ---")

    reference_x = calculate_reference_x(page_regular_rows)

    print("Reference X:", reference_x)
    print("Row 14 first X:", page_regular_rows[13][0][0])

    reference_x = calculate_reference_x(page_regular_rows)
    recovered_rows = recover_missing_first_centers_in_rows(
        page_regular_rows,
        reference_x
    )

    print("\n--- Recovered row lengths after first-column recovery ---")
    for index, row in enumerate(recovered_rows, start=1):
        print(f"Row {index}: {len(row)} centers")


    grid_matrix = build_grid_matrix(recovered_rows)
    print("Grid matrix shape:", grid_matrix.shape)

    grid_box = calculate_grid_bounding_box(grid_matrix)
    print("Calculated grid box:", grid_box)
    calculated_box_image = image.copy()

    x, y, w, h = grid_box

    cv2.rectangle(
        calculated_box_image,
        (round(x), round(y)),
        (round(x + w), round(y + h)),
        (255, 0, 0),
        2
    )

    cv2.imwrite(
        str(OUTPUT_DIR / "calculated_grid_box.png"),
        calculated_box_image
    )

    grid_box = calculate_grid_bounding_box(grid_matrix)

    rows, columns = grid_matrix.shape[:2]

    padded_grid_box = add_grid_padding(
        grid_box,
        rows,
        columns
    )

    print("Original grid box:", grid_box)
    print("Padded grid box:", padded_grid_box)

    comparison_image = draw_boxes(
        image,
        [tuple(map(round, grid_box))],
        (255, 0, 0),  # Blue
        2
    )

    comparison_image = draw_boxes(
        comparison_image,
        [tuple(map(round, padded_grid_box))],
        (0, 255, 0),  # Green
        2
    )

    cv2.imwrite(
        str(OUTPUT_DIR / "grid_padding_comparison.png"),
        comparison_image
    )

    center = grid_matrix[0, 0]

    rows, columns = grid_matrix.shape[:2]

    cell_width = grid_box[2] / (columns - 1)
    cell_height = grid_box[3] / (rows - 1)

    cell_image = extract_cell(
        image,
        center,
        cell_width,
        cell_height
    )

    cv2.imwrite(
        str(OUTPUT_DIR / "first_cell.png"),
        cell_image
    )

    print("First cell shape:", cell_image.shape)

    cells = extract_grid_cells(
        image,
        grid_matrix,
        cell_width,
        cell_height
    )

    print("Number of rows:", len(cells))
    print("Number of columns:", len(cells[0]))
    print("Total cells:", sum(len(row) for row in cells))
    print("First cell shape:", cells[0][0].shape)

    save_grid_cells(cells, OUTPUT_DIR / "grid_cells")

    cells_dir = OUTPUT_DIR / "grid_cells"

    saved_files = list(cells_dir.glob("*.png"))

    print("Saved cells:", len(saved_files))

    grid_preview = build_grid_preview(cells)

    print("Grid preview shape:", grid_preview.shape)

    cv2.imwrite(
        str(OUTPUT_DIR / "grid_preview.png"),
        grid_preview
    )

    problem_cell = cells[0][10]

    psm_modes = [10, 8, 13]

    for psm in psm_modes:
        character = recognize_character(
            problem_cell,
            psm=psm,
            use_whitelist=False,
            debug=True
        )
        print(f"PSM {psm}: {repr(character)}")

    character_matrix = recognize_grid(cells, use_fallback=True)
    expected_matrix = load_ground_truth(GROUND_TRUTH_PATH)

    correct, total = evaluate_grid_accuracy(
        character_matrix,  # Predicted matrix
        expected_matrix    # Expected matrix
    )

    accuracy = correct / total * 100

    print("\n--- OCR Accuracy ---")
    print("Correct characters:", correct)
    print("Incorrect characters:", total - correct)
    print(f"Character accuracy: {accuracy:.2f}%")

    errors = find_ocr_errors(
        character_matrix,
        expected_matrix
    )

    unrecognized_errors = []

    for error in errors:
        row_index, column_index, expected, predicted = error

        # Add the error only if OCR returned "?"
        if predicted == "?":
            unrecognized_errors.append(error)


    unrecognized_images = build_error_preview(
        cells,
        unrecognized_errors
    )

    mosaic = create_error_mosaic(
        unrecognized_images,
        columns=4
    )

    if mosaic is not None:
        cv2.imwrite(
            str(OUTPUT_DIR / "unrecognized_errors.png"),
            mosaic
        )

    save_failed_cells(
        cells,
        errors,
        OUTPUT_DIR / "ocr_errors"
    )

    errors_dir = OUTPUT_DIR / "ocr_errors"

    saved_files = list(errors_dir.glob("*.png"))

    o_errors = filter_errors_by_character(errors, "O")
    o_error_images = build_error_preview(cells, o_errors)
    o_mosaic = create_error_mosaic(o_error_images, columns=4)

    if o_mosaic is not None:
        cv2.imwrite(str(OUTPUT_DIR / "o_errors_mosaic.png"), o_mosaic)

    # Filter errors involving the letter C
    c_errors = filter_errors_by_character(errors, "C")

    # Extract images for visualization
    c_error_images = build_error_preview(cells, c_errors)

    # Build a mosaic with 3 columns
    c_mosaic = create_error_mosaic(c_error_images, columns=3)

    if c_mosaic is not None:
        cv2.imwrite(
            str(OUTPUT_DIR / "c_errors_mosaic.png"),
            c_mosaic
        )

    c_positions = [
        (7, 0),
        (14, 0),
        (15, 2)
    ]

    for row, col in c_positions:
        cell_image = cells[row][col]

        print(f"\nTesting C at ({row}, {col})")

        for scale in [1, 2]:
            result = recognize_character(
                cell_image,
                psm=10,
                use_whitelist=True,
                scale_factor=scale
            )

            print(f"Scale {scale}x: {repr(result)}")

    print("Errors involving O:", len(o_errors))
    print("Preview images:", len(o_error_images))
    if o_error_images:
        print("First image shape:", o_error_images[0].shape)

    print("OCR errors detected:", len(errors))
    print("Error images saved:", len(saved_files))

    test_cells = [
        ("Y", cells[3][0]),
        ("C", cells[7][0])
    ]

    for expected, cell_image in test_cells:
        print(f"\n--- Testing character: {expected} ---")

        for use_threshold in [False, True]:
            character = recognize_character(
                cell_image,
                psm=10,
                use_whitelist=True,
                use_threshold=use_threshold
            )

            print(
                f"Threshold: {use_threshold} "
                f"| Recognized: {repr(character)}"
            )

    print("\n--- OCR Errors ---")

    for row_index, column_index, expected, predicted in errors:
        # Print error details
        print(
            f"Row {row_index + 1}, Column {column_index + 1} "
            f"| Expected: {expected} | Predicted: {predicted}"
        )

    print("Character matrix dimensions:", len(character_matrix), len(character_matrix[0]))

    for row in character_matrix:
        print(" ".join(row))

    first_cell = cells[0][0]

    recognized_character = recognize_character(first_cell)

    print("Expected character: B")
    print("Recognized character:", repr(recognized_character))

    total_cells = sum(len(row) for row in character_matrix)

    failed_cells = 0

    for row in character_matrix:
        for character in row:
            # Count failed recognitions
            if character == "?":
                failed_cells += 1

    recognized_cells = total_cells - failed_cells

    recognition_rate = (recognized_cells / total_cells) * 100

    print("\n--- OCR Statistics ---")
    print("Total cells:", total_cells)
    print("Recognized cells:", recognized_cells)
    print("Failed cells:", failed_cells)
    print(f"Recognition rate: {recognition_rate:.2f}%")

    if possible_grids:
        grid_box = possible_grids[0]

        grid_centers = filter_centers_by_box(
            character_centers,
            grid_box
        )

        grid_rows, grid_merged_rows, grid_recovered_rows, grid_long_rows, grid_regular_rows = (
            analyze_character_rows(grid_centers)
        )

        print(f"Original centers: {len(character_centers)}")
        print(f"Centers inside grid: {len(grid_centers)}")
        print(f"Detected grid rows: {len(grid_rows)}")
        print(f"Rows after length filter: {len(grid_long_rows)}")
        print(f"Rows after spacing filter: {len(grid_regular_rows)}")

        cv2.imwrite(
            str(OUTPUT_DIR / "grid_all_centers.png"),
            draw_character_centers(image, grid_rows)
        )

        # Centers surviving length and spacing filters
        cv2.imwrite(
            str(OUTPUT_DIR / "grid_colored_rows.png"),
            draw_character_centers(
                image,
                grid_regular_rows,
                color_by_row=True
            )
        )

        grid_row_centers_y = calculate_row_centers_y(grid_regular_rows)

        vertical_distances = calculate_spacing(grid_row_centers_y)

        vertical_cv = calculate_coefficient_of_variation(
            vertical_distances
        )

        print("\n--- Vertical grid analysis ---")
        print("Candidate rows:", len(grid_regular_rows))
        print("Row centers Y:", grid_row_centers_y)
        print("Vertical distances:", vertical_distances)
        print("Vertical spacing CV:", vertical_cv)

        print("\n--- Grid row statistics ---")
        print_row_statistics(grid_rows)

        print("\n--- Grid merging statistics ---")

        print("Centers before merging:", sum(len(row) for row in grid_rows))
        print("Centers after merging:", sum(len(row) for row in grid_merged_rows))

        print("Rows after length filter:", len(grid_long_rows))
        print("Rows after spacing filter:", len(grid_regular_rows))

        grid_matrix = build_grid_matrix(grid_regular_rows)

        print("Grid matrix shape:", grid_matrix.shape)
        print("Top-left character center:", grid_matrix[0, 0])
        print("Bottom-right character center:", grid_matrix[-1, -1])

        print("\n--- CV comparison ---")

        for index, (original_row, merged_row) in enumerate(
            zip(grid_rows, grid_merged_rows),
            start=1
        ):
            original_x = [center[0] for center in original_row]
            merged_x = [center[0] for center in merged_row]

            original_cv = calculate_coefficient_of_variation(
                calculate_spacing(original_x)
            )

            merged_cv = calculate_coefficient_of_variation(
                calculate_spacing(merged_x)
            )

            print(
                f"Row {index}: "
                f"Centers {len(original_row)} -> {len(merged_row)}, "
                f"CV {original_cv} -> {merged_cv}"
            )

    else:
        print("No candidate grid detected")


if __name__ == "__main__":
    main()
