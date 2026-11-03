import cv2

def extract_cell(image, center, cell_width, cell_height):
    center_x, center_y = center

    height, width = image.shape[:2]

    # Calculate top-left corner
    x1 = max(0, round(center_x - cell_width / 2))
    y1 = max(0, round(center_y - cell_height / 2))

    # Calculate bottom-right corner
    x2 = min(width, round(center_x + cell_width / 2))
    y2 = min(height, round(center_y + cell_height / 2))

    # Crop image using NumPy slicing
    cell_image = image[y1:y2, x1:x2]

    return cell_image

def extract_grid_cells(image, grid_matrix, cell_width, cell_height):
    cells = []

    rows, columns = grid_matrix.shape[:2]
    # Iterate through rows
    for row in range(rows):
        row_cells = []

        # Iterate through columns
        for column in range(columns):
            # Extract each cell
            center = grid_matrix[row, column]
            cell_image = extract_cell(image, center, cell_width, cell_height)

            row_cells.append(cell_image)

        # Preserve the grid structure
        cells.append(row_cells)
            
    return cells

def save_grid_cells(cells, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    for row_index, row_cells in enumerate(cells):
        for column_index, cell_image in enumerate(row_cells):

            # Build filename
            filename = f"row_{row_index:02d}_col_{column_index:02d}.png"
            file_path = output_dir / filename

            # Save image using cv2.imwrite()
            saved = cv2.imwrite(str(file_path), cell_image)

            if not saved:
                raise OSError(f"Failed to save image: {file_path}") 