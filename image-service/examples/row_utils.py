from spacing_utils import calculate_spacing, calculate_coefficient_of_variation
import numpy as np

def group_characters_by_rows(centers, tolerance=3):
    rows = []

    sorted_centers = sorted(centers, key=lambda center: center[1])

    # Group centers by their Y coordinates
    for center in sorted_centers:
        center_y = center[1]
        row_found = False

        # Find an existing row or create a new one
        for row in rows:
            reference_y = row[0][1]
            if abs(center_y - reference_y) <= tolerance:
                row.append(center)

                row_found = True
                break

        # If no matching row exists, create a new row
        if not row_found:
            rows.append([center])

    for row in rows:
        row.sort(key=lambda center: center[0])

    return rows

def filter_rows_by_length(rows, min_characters=5):
    filtered_rows = []

    # Keep only rows with at least min_characters
    for row in rows:
        if len(row) >= min_characters:
            filtered_rows.append(row)

    return filtered_rows

def filter_rows_by_spacing(rows, max_cv=0.2):
    filtered_rows = []

    for row in rows:
        # 1. Extract X coordinates from each row
        x_coordinates = [coordinate[0] for coordinate in row]
    
        # 2. Calculate horizontal distances
        distances = calculate_spacing(x_coordinates)

        # 3. Calculate coefficient of variation
        cv = calculate_coefficient_of_variation(distances)

        # 4. Keep rows whose CV is <= max_cv
        if cv is not None and cv <= max_cv:
            filtered_rows.append(row)

    return filtered_rows

def merge_close_centers(row, min_distance=8):
    merged_row = []

    # 1. Iterate through centers sorted by X
    sorted_row = sorted(row, key=lambda center: center[0])

    i = 0

    while i < len(sorted_row):
        current_center = sorted_row[i]
        
        # 2. Compare consecutive centers
        if i + 1 < len(sorted_row):
            next_center = sorted_row[i+1]

            current_x = current_center[0]
            next_x = next_center[0]
            if next_x - current_x < min_distance:
                current_y = current_center[1]
                next_y = next_center[1]

                # 3. Merge centers that are too close
                merged_X = (current_x + next_x) / 2
                merged_y = (current_y + next_y) / 2

                # 4. Preserve centers that are sufficiently separated
                merged_row.append((merged_X, merged_y))

                i = i + 2
                continue

        merged_row.append(current_center)
        i = i + 1

    return merged_row

def merge_close_centers_in_rows(rows, min_distance=8):
    merged_rows = []

    # Apply merge_close_centers() to every row
    for row in rows:
        merged_row = merge_close_centers(row, min_distance)
        merged_rows.append(merged_row)

    return merged_rows

def calculate_row_centers_y(rows):
    centers_y = []

    # Calculate the average Y coordinate of each row
    for row in rows:
        if not row:
            continue

        average_y = np.mean([center[1] for center in row])
        centers_y.append(float(average_y))

    return centers_y

def build_grid_matrix(rows):
    if not rows:
        raise ValueError("Cannot build a grid matrix from empty rows")
    
    # Convert rows into a NumPy array
    len_reference = len(rows[0])

    for row in rows:
        if len_reference != len(row):
            raise ValueError("All grid rows must have the same number of centers")

    grid_matrix = np.array(rows, dtype=float)

    return grid_matrix

def find_large_gaps(row, gap_multiplier=1.5):
    x_coordinates = [center[0] for center in row]

    distances = calculate_spacing(x_coordinates)

    if not distances:
        return []

    typical_spacing = np.median(distances)

    large_gaps = []

    for index, distance in enumerate(distances):
        # Determine whether distance is unusually large
        if distance > typical_spacing * gap_multiplier:
            # Append its index to large_gaps
            large_gaps.append(index)

    return large_gaps

def estimate_missing_centers(row, large_gaps):
    estimated_centers = []

    for index in large_gaps:
        left_center = row[index]
        right_center = row[index + 1]

        # Calculate the midpoint
        missing_x = (left_center[0] + right_center[0]) / 2
        missing_y = (left_center[1] + right_center[1]) / 2

        estimated_centers.append((missing_x, missing_y))

    return estimated_centers

def combine_centers(row, estimated_centers):
    # Combine both lists
    combined_row = row + estimated_centers

    # Sort centers by X
    combined_row.sort(key=lambda center: center[0])

    return combined_row

def recover_missing_centers(row):
    # 1. Find unusually large gaps
    large_gaps = find_large_gaps(row, 1.5)

    # 2. Estimate missing centers
    estimated_centers = estimate_missing_centers(row, large_gaps)

    # 3. Combine original and estimated centers
    recovered_row = combine_centers(row, estimated_centers)

    return recovered_row

def recover_missing_centers_in_rows(rows):
    recovered_rows = []

    for row in rows:
        recovered_row = recover_missing_centers(row)
        recovered_rows.append(recovered_row)

    return recovered_rows

def calculate_reference_x(rows):
    first_centers_x = []

    for row in rows:
        if not row:
            continue

        # Append the first center's X coordinate
        first_centers_x.append(row[0][0])

    if not first_centers_x:
        return None

    reference_x = np.median(first_centers_x)

    return float(reference_x)

def recover_missing_first_center(row, reference_x):
    if not row or reference_x is None:
        return row.copy()

    recovered_row = row.copy()

    first_x = row[0][0]

    x_coordinates = [center[0] for center in row]
    distances = calculate_spacing(x_coordinates)

    if not distances:
        return recovered_row

    typical_spacing = float(np.median(distances))

    # Determine whether the first column is missing
    if first_x - reference_x > typical_spacing * 0.5:
        # Estimate its center if necessary
        missing_x = reference_x
        missing_y = recovered_row[0][1]

        recovered_row.insert(0, (missing_x, missing_y))

    return recovered_row

def recover_missing_first_centers_in_rows(rows, reference_x):
    recovered_rows = []

    for row in rows:
        recovered_row = recover_missing_first_center(row, reference_x)
        recovered_rows.append(recovered_row)

    return recovered_rows

if __name__ == "__main__":
    centers = [
        (40, 150),
        (65, 151),
        (90, 149),
        (40, 175),
        (65, 176),
        (90, 174)
    ]

    rows = group_characters_by_rows(centers)

    for index, row in enumerate(rows):
        centers_x = [center[0] for center in row]

        distances = calculate_spacing(centers_x)

        # Calculate the coefficient of variation
        cv = calculate_coefficient_of_variation(distances)

        print(f"Row {index + 1}")
        print(f"Spacing: {distances}")
        print(f"CV: {cv}")

    test_rows = [
        [(20, 150), (45, 150), (70, 150), (95, 150), (120, 150)],
        [(20, 175), (45, 175)],
        [(20, 200), (45, 200), (70, 200), (95, 200), (120, 200), (145, 200)]
    ]

    filtered_rows = filter_rows_by_length(test_rows)

    for row in filtered_rows:
        print(f"Characters: {len(row)}")

    test_rows = [
        [(20, 100), (45, 100), (70, 100), (95, 100)],
        [(20, 125), (35, 125), (80, 125), (95, 125)]
    ]

    filtered_rows = filter_rows_by_spacing(test_rows)

    print(f"Rows before filtering: {len(test_rows)}")
    print(f"Rows after filtering: {len(filtered_rows)}")

    test_row = [
        (48.0, 200),
        (65.0, 200),
        (80.5, 200),
        (84.5, 200),
        (101.0, 200)
    ]

    merged_row = merge_close_centers(test_row)

    print("Original:", test_row)
    print("Merged:", merged_row)

    rows = [
        [(40, 150), (65, 151), (90, 149)],
        [(40, 175), (65, 176), (90, 174)]
    ]
    
    row_centers_y = calculate_row_centers_y(rows)

    print("Row center Y coordinates:", row_centers_y)
    vertical_distances = calculate_spacing(row_centers_y)

    vertical_cv = calculate_coefficient_of_variation(
        vertical_distances
    )

    print("Vertical spacing:", vertical_distances)
    print("Vertical CV:", vertical_cv)

    test_row = [
        (93, 150),
        (116, 150),
        (139, 150),
        (185, 150),
        (208, 150)
    ]

    large_gaps = find_large_gaps(test_row)
    estimated_centers = estimate_missing_centers(test_row, large_gaps)

    print("Large gaps:", large_gaps)
    print("Estimated centers:", estimated_centers)