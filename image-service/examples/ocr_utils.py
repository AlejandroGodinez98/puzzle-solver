import cv2
import pytesseract

ALLOWED_CHARACTERS = set(
    "ABCDEFGHIJKLMNÑOPQRSTUVWXYZÁÉÍÓÚÜ"
)

def recognize_character(cell_image, psm=10, use_whitelist=True, debug=False, use_threshold=False, scale_factor=1):
    # Convert image to grayscale
    gray_image = cv2.cvtColor(cell_image, cv2.COLOR_BGR2GRAY)

    if scale_factor != 1:
        height, width = gray_image.shape

        gray_image = cv2.resize(
            gray_image,
            (
                int(width * scale_factor),
                int(height * scale_factor)
            ),
            interpolation=cv2.INTER_CUBIC
        )
    
    if use_threshold:
        # Apply binary thresholding
        _, gray_image = cv2.threshold(
            gray_image,
            127.0,
            255,
            cv2.THRESH_BINARY
        )

    # Configure Tesseract for a single character
    config = f"--psm {psm}"

    if use_whitelist:
        config += (
            " -c tessedit_char_whitelist="
            "ABCDEFGHIJKLMNÑOPQRSTUVWXYZÁÉÍÓÚÜ"
        )

    # Add a 10-pixel white border
    padded_image = cv2.copyMakeBorder(
        gray_image,
        10,  # top
        10,  # bottom
        10,  # left
        10,  # right
        cv2.BORDER_CONSTANT, # border type
        value=255
    )

    # Recognize the character
    character = pytesseract.image_to_string(
        padded_image,
        lang="spa",
        config=config
    )

    if debug:
        print(f"PSM {psm} raw output: {repr(character)}")

    character = character.strip().upper()

    if len(character) != 1:
        # Return a placeholder indicating OCR failure
        character = "?"

    return character

def recognize_grid(cells, use_fallback=False):
    character_matrix = []

    for row_cells in cells:
        character_row = []

        for cell_image in row_cells:
            # Recognize one character
            if use_fallback:
                character = recognize_character_with_fallback(cell_image)
            else:
                character = recognize_character(cell_image, psm=10, use_whitelist=True)

            # Add character to character_row
            character_row.append(character)

        # Add character_row to character_matrix
        character_matrix.append(character_row)

    return character_matrix

def recognize_character_with_fallback(cell_image):
    
    primary_result = recognize_character(
        cell_image,
        psm=10,
        use_whitelist=True
    )

    # 1: Return primary result if valid
    if primary_result in ALLOWED_CHARACTERS:
        return primary_result

    fallback_result = recognize_character(
        cell_image,
        psm=10,
        use_whitelist=False
    )

    # 2: Validate fallback result
    if fallback_result in ALLOWED_CHARACTERS:
        return fallback_result

    threshold_result = recognize_character(
        cell_image,
        psm=10,
        use_whitelist=True,
        debug=True,
        use_threshold=True
    )

    if threshold_result in ALLOWED_CHARACTERS:
        return threshold_result

    scaled_result = recognize_character(
        cell_image,
        psm=10,
        use_whitelist=True,
        scale_factor=2
    )

    if scaled_result in ALLOWED_CHARACTERS:
        return scaled_result

    return "?"