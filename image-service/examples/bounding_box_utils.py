import numpy as np

def calculate_iou(box_a, box_b):
    x1_a, y1_a, w_a, h_a = box_a
    x1_b, y1_b, w_b, h_b = box_b

    # Calculate intersection coordinates
    x2_a = x1_a + w_a
    y2_a = y1_a + h_a

    x2_b = x1_b + w_b
    y2_b = y1_b + h_b

    # Calculate intersection area
    intersection_x1 = max(x1_a, x1_b)
    intersection_y1 = max(y1_a, y1_b)

    intersection_x2 = min(x2_a, x2_b)
    intersection_y2 = min(y2_a, y2_b)

    intersection_width = max(0, intersection_x2 - intersection_x1)
    intersection_height = max(0, intersection_y2 - intersection_y1)

    intersection_area = intersection_width * intersection_height

    # Calculate union area
    area_a = w_a * h_a
    area_b = w_b * h_b

    union_area = area_a + area_b - intersection_area

    # Return IoU
    return 0.0 if union_area == 0 else intersection_area / union_area

def remove_duplicate_boxes(boxes, threshold=0.9):
    unique_boxes = []

    # Compare boxes using calculate_iou()
    for box in boxes:
        is_duplicate = False

        for existing_box in unique_boxes:
            iou = calculate_iou(box, existing_box)

            # Detect duplicate
            if iou >= threshold:
                is_duplicate = True
                break
        
        # Append only if not duplicate
        if not is_duplicate:
            unique_boxes.append(box)

    return unique_boxes

def calculate_spacing(centers):
    distances = []

    # Calculate distances between consecutive centers
    for i in range(len(centers)-1):
        distances.append(centers[i+1] - centers[i])

    return distances

def filter_centers_by_box(centers, box):
    filtered_centers = []

    x, y, w, h = box

    # Keep only centers inside the bounding box
    for center in centers:
        center_x = center[0]
        center_y = center[1]
        if x <= center_x <= x + w and y <= center_y <= y + h:
            filtered_centers.append(center)

    return filtered_centers

def calculate_grid_bounding_box(grid_matrix):
    x_coordinates = grid_matrix[:, :, 0]
    y_coordinates = grid_matrix[:, :, 1]

    min_x = np.min(x_coordinates)
    max_x = np.max(x_coordinates)
    min_y = np.min(y_coordinates)
    max_y = np.max(y_coordinates)

    width = max_x - min_x
    height = max_y - min_y

    return (min_x, min_y, width, height)

def add_grid_padding(grid_box, rows, columns):
    if rows < 2 or columns < 2:
        raise ValueError("Grid must have at least 2 rows and 2 columns")
    
    x, y, width, height = grid_box

    # 1: Calculate horizontal spacing
    horizontal_spacing = width / (rows - 1)

    # 2: Calculate vertical spacing
    vertical_spacing = height / (columns - 1)

    # 3: Calculate half-cell padding
    padding_x = horizontal_spacing / 2
    padding_y = vertical_spacing / 2

    new_x = x - padding_x
    new_y = y - padding_y

    new_width = width + 2 * padding_x
    new_height = height + 2 * padding_y

    # 4: Return expanded bounding box
    return (new_x, new_y, new_width, new_height)

if __name__ == "__main__":
    # Your test code here
    box_a = (22, 113, 443, 360)
    box_b = (25, 116, 437, 354)

    iou = calculate_iou(box_a, box_b)

    print(f"IoU: {iou:.4f}")

    boxes = [
        (22, 113, 443, 360),  # Grid exterior
        (25, 116, 437, 354),  # Grid interior
        (22, 499, 221, 105),  # Word list left
        (245, 499, 221, 105), # Word list right
        (287, 36, 142, 65)    # Illustration
    ]

    result = remove_duplicate_boxes(boxes)

    for box in result:
        print(box)

    grid_distances = [25, 25, 25, 25]
    word_distances = [12, 13, 40, 11]

    print("Grid STD:", np.std(grid_distances))
    print("Words STD:", np.std(word_distances))

    centers = [
        (40, 150),
        (90, 200),
        (300, 550),
        (15, 200)
    ]

    box = (22, 113, 443, 360)

    filtered = filter_centers_by_box(centers, box)

    print(filtered)