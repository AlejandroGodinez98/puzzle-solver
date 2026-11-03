import cv2
import numpy as np


def build_grid_preview(cells, cell_size=32):
    row_images = []

    for row_cells in cells:
        normalized_cells = []

        for cell_image in row_cells:
            # Resize every cell to 32x32 pixels
            normalized_cell = cv2.resize(cell_image, (cell_size, cell_size))

            normalized_cells.append(normalized_cell)

        # Combine all cells horizontally
        row_image = np.hstack(normalized_cells)

        row_images.append(row_image)

    # Combine all rows vertically
    grid_image = np.vstack(row_images)

    return grid_image

def create_error_mosaic(error_images, columns=4):
    rows = []

    if not error_images:
        return None

    cell_height, cell_width = error_images[0].shape[:2]
    channels = error_images[0].shape[2]

    for start in range(0, len(error_images), columns):
        # 1: Select up to 4 images
        row_images = error_images[start:start + columns]
        
        while len(row_images) < columns:
            blank_image = np.full(
                (cell_height, cell_width, channels),
                255,
                dtype=np.uint8
            )
            row_images.append(blank_image)

        # 2: Join images horizontally
        row = np.hstack(row_images)
        rows.append(row)

    # 3: Join rows vertically
    mosaic = np.vstack(rows)

    return mosaic