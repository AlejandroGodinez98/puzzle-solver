from pathlib import Path
import cv2

GROUND_TRUTH_PATH = (
    Path(__file__).resolve().parent
    / "ground_truth"
    / "word_search_02.txt"
)

def evaluate_character_accuracy(predicted, expected):
    if len(predicted) == 0 or len(expected) == 0:
        raise ValueError("Lists cannot be empty")

    if len(predicted) != len(expected):
        raise ValueError("Predicted and expected must have the same length")
    
    correct = 0
    total = len(expected)

    # Compare both matrices
    for predicted_char, expected_char in zip(predicted, expected):
        # Compare characters
        if predicted_char == expected_char:
            correct += 1

    # Calculate accuracy
    return correct, total

def load_ground_truth(file_path):
    expected_matrix = []

    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # 1: Remove newline characters
            row = line.strip()

            # 2: Convert the string to a list
            characters = list(row)

            if  len(characters) != 16:
                raise ValueError(
                    f"Invalid row length: expected 16, got {len(characters)}"
                )
            
            # 3: Add characters to expected_matrix
            expected_matrix.append(characters)

    # Validate number of rows
    if len(expected_matrix) != 16:
        raise ValueError(
            f"Invalid row count: expected 16, got {len(expected_matrix)}"
        )

    return expected_matrix

def evaluate_grid_accuracy(predicted_matrix, expected_matrix):
    # 1: Validate matrix row counts
    if len(predicted_matrix) != len(expected_matrix) or len(predicted_matrix) == 0 or len(expected_matrix) == 0:
        raise ValueError(
            "Matrices must have the same number of rows and cannot be empty"
        )    

    total_correct = 0
    total_characters = 0

    # 2: Iterate through both matrices
    for predicted_row, expected_row in zip(predicted_matrix, expected_matrix):
        # 3: Reuse evaluate_character_accuracy()
        correct, total = evaluate_character_accuracy(predicted_row, expected_row)

        # 4: Accumulate correct and total characters
        total_correct += correct
        total_characters += total

    return total_correct, total_characters

def find_ocr_errors(predicted_matrix, expected_matrix):
    evaluate_grid_accuracy(predicted_matrix, expected_matrix)
    errors = []

    # Iterate through rows
    for row_index in range(len(predicted_matrix)):
        # Iterate through columns
        for column_index in range(len(predicted_matrix[row_index])):
            # Compare predicted and expected characters
            predicted = predicted_matrix[row_index][column_index]
            expected = expected_matrix[row_index][column_index]

            # Store mismatches
            if predicted != expected:
                errors.append((row_index, column_index, expected, predicted))

    return errors

def save_failed_cells(cells, errors, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    for row_index, column_index, expected, predicted in errors:
        # 1: Get the failed cell image
        cell_image = cells[row_index][column_index]

        # 2: Build a descriptive filename
        filename = f"row_{row_index:02d}_col_{column_index:02d}_expected_{expected}.png"

        # Build output path
        file_path = output_dir / filename

        # 3: Save the image
        saved = cv2.imwrite(str(file_path), cell_image)

        if not saved:
            raise OSError(f"Failed to save image: {file_path}")

def filter_errors_by_character(errors, target_character):
    filtered_errors = []

    for error in errors:
        _, _, expected, _ = error

        # Filter errors by expected character
        if expected == target_character:
            filtered_errors.append(error)

    return filtered_errors

def build_error_preview(cells, errors, cell_size=64):
    error_images = []

    for row_index, column_index, expected, predicted in errors:
        # 1: Retrieve the original cell
        cell_image = cells[row_index][column_index]

        # 2: Resize it to cell_size × cell_size
        normalized_image = cv2.resize(
            cell_image,
            (cell_size, cell_size)
        )

        # 3: Add it to error_images
        error_images.append(normalized_image)

    return error_images

if __name__ == "__main__":
    predicted = ["B", "P", "A", "N", "T", "E", "?", "A"]
    expected =  ["B", "P", "A", "N", "T", "E", "R", "A"]

    correct, total = evaluate_character_accuracy(predicted, expected)

    accuracy = correct / total * 100

    print(f"Character accuracy: {accuracy:.2f}%")

    predicted = [
        ["A", "B", "C"],
        ["D", "?", "F"],
        ["G", "H", "I"]
    ]

    expected = [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "X"]
    ]

    total_correct, total_characters = evaluate_grid_accuracy(predicted, expected)
    accuracy = total_correct / total_characters * 100

    print(f"Grid accuracy: {accuracy:.2f}%")

    expected_matrix = load_ground_truth(GROUND_TRUTH_PATH)

    print("Rows:", len(expected_matrix))
    print("Columns:", len(expected_matrix[0]))