import numpy as np
import torch


INPUT_SIZE = 4
MAX_POINTS = 128 #model trained with max 128 points
CANVAS_SIZE = 256.0
SIMPLIFY_EPSILON = 2.0
MIN_POINT_DISTANCE = 1.0


def strokes_to_tensor(strokes: list): 
    movements = strokes_to_movements(strokes)

    if len(movements) == 0:
        src = torch.zeros((1, 1, INPUT_SIZE), dtype=torch.float32)
        mask = torch.zeros((1, 1), dtype=torch.bool) 
        return src, mask, False

    movements = movements[:MAX_POINTS]
    src = torch.from_numpy(movements).unsqueeze(0) #numpy array to pytorch tensor (array that the model understands)
    mask = torch.zeros((1, len(movements)), dtype=torch.bool)

    return src, mask, True


def strokes_to_movements(strokes: list) -> np.ndarray:
    parsed_strokes = parse_frontend_strokes(strokes)
    normalized_strokes = normalize_strokes(parsed_strokes, CANVAS_SIZE) #so we can draw top left small or bottom right big -> same model guess
    cleaned_strokes = clean_strokes(normalized_strokes, SIMPLIFY_EPSILON, MIN_POINT_DISTANCE)
    return encode_strokes(cleaned_strokes) #from absolute coordinates to relative coordinates


def parse_frontend_strokes(strokes: list) -> list[np.ndarray]:
    parsed_strokes = []

    for stroke in strokes:
        points = []

        for point in stroke.get("points", []):
            x = point.get("x")
            y = point.get("y")

            if x is None or y is None:
                continue

            points.append((float(x), float(y)))

        if points:
            parsed_strokes.append(np.array(points, dtype=np.float32)) # strokes to numpy array (maths between vectors), float 32 -> lighter than 64 -> efficient

    return parsed_strokes


def normalize_strokes(strokes: list[np.ndarray], canvas_size: float) -> list[np.ndarray]:
    if not strokes:
        return []

    all_points = np.concatenate(strokes, axis=0) #concatenate the strokes arrays because they are separates, necessary to calculate max, min...
    min_xy = all_points.min(axis=0)
    max_xy = all_points.max(axis=0)
    size_xy = max_xy - min_xy
    longest_side = float(max(size_xy[0], size_xy[1]))

    if longest_side == 0:
        return [stroke - min_xy for stroke in strokes]

    scale = canvas_size / longest_side
    drawing_size = size_xy * scale
    offset = (canvas_size - drawing_size) / 2.0

    return [(stroke - min_xy) * scale + offset for stroke in strokes]


def clean_strokes(
    strokes: list[np.ndarray],
    simplify_epsilon: float,
    min_point_distance: float,
) -> list[np.ndarray]:
    cleaned_strokes = []

    for stroke in strokes:
        spaced_stroke = remove_close_points(stroke, min_point_distance)
        simplified_stroke = simplify_stroke(spaced_stroke, simplify_epsilon)

        if len(simplified_stroke) > 0:
            cleaned_strokes.append(simplified_stroke)

    return cleaned_strokes


def remove_close_points(points: np.ndarray, min_distance: float) -> np.ndarray:
    if len(points) <= 2 or min_distance <= 0:
        return points

    kept_points = [points[0]]
    min_squared_distance = min_distance * min_distance

    for point in points[1:-1]:
        distance = point - kept_points[-1]

        if float(np.dot(distance, distance)) >= min_squared_distance:
            kept_points.append(point)

    if not np.array_equal(kept_points[-1], points[-1]):
        kept_points.append(points[-1])

    return np.array(kept_points, dtype=np.float32)


def simplify_stroke(points: np.ndarray, epsilon: float) -> np.ndarray:
    if len(points) <= 2 or epsilon <= 0:
        return points

    return ramer_douglas_peucker(points, epsilon).astype(np.float32)


def ramer_douglas_peucker(points: np.ndarray, epsilon: float) -> np.ndarray:
    if len(points) <= 2:
        return points

    distances = point_line_distances(points[1:-1], points[0], points[-1])
    max_index = int(np.argmax(distances)) + 1
    max_distance = float(distances[max_index - 1])

    if max_distance <= epsilon:
        return np.vstack((points[0], points[-1]))

    left = ramer_douglas_peucker(points[: max_index + 1], epsilon)
    right = ramer_douglas_peucker(points[max_index:], epsilon)
    return np.vstack((left[:-1], right))


def point_line_distances(points: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    line = end - start
    line_length = float(np.linalg.norm(line))

    if line_length == 0:
        return np.linalg.norm(points - start, axis=1)

    shifted = points - start
    cross = np.abs(line[0] * shifted[:, 1] - line[1] * shifted[:, 0])
    return cross / line_length


def encode_strokes(strokes: list[np.ndarray]) -> np.ndarray:
    encoded_points = []
    previous_point = None

    for stroke in strokes:
        for point_index, point in enumerate(stroke):
            is_start = point_index == 0
            is_end = point_index == len(stroke) - 1

            if previous_point is None:
                dx = 0.0
                dy = 0.0
            else:
                delta = point - previous_point #getting delta -> movement from the other point
                dx = float(delta[0])
                dy = float(delta[1])

            encoded_points.append([dx, dy, float(is_end), float(is_start)])
            previous_point = point

    return np.array(encoded_points, dtype=np.float32).reshape(-1, INPUT_SIZE)
