import numpy as np

def calculate_coefficient_of_variation(distances):
    if not distances:
        return None
    
    mean = np.mean(distances)
    std = np.std(distances)

    if mean == 0:
        return None

    return std / mean

def calculate_spacing(centers):
    distances = []

    # Calculate distances between consecutive centers
    for i in range(len(centers)-1):
        distances.append(centers[i+1] - centers[i])

    return distances

if __name__ == "__main__":
    grid_a = [10, 10, 10, 11]
    grid_b = [40, 40, 40, 44]

    print("Grid A CV:", calculate_coefficient_of_variation(grid_a))
    print("Grid B CV:", calculate_coefficient_of_variation(grid_b))