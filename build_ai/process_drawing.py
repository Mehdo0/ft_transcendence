import numpy as np

from config import DRAWING_CONFIG


def process_drawing(
    raw_drawing: list,
    canvas_size: float = DRAWING_CONFIG.canvas_size,
    simplify_epsilon: float = DRAWING_CONFIG.simplify_epsilon,
    min_point_distance: float = DRAWING_CONFIG.min_point_distance,
) -> np.ndarray:
    strokes = parse_strokes(raw_drawing)
    normalized_strokes = normalize_strokes(strokes, canvas_size)
    cleaned_strokes = clean_strokes(normalized_strokes, simplify_epsilon, min_point_distance)
    return encode_strokes(cleaned_strokes)


def parse_strokes(raw_drawing: list) -> list[np.ndarray]:
    strokes = []

    for raw_stroke in raw_drawing:
        if len(raw_stroke) < 2:
            continue

        x_coords = raw_stroke[0]
        y_coords = raw_stroke[1]
        point_count = min(len(x_coords), len(y_coords))

        if point_count == 0:
            continue

        points = np.column_stack((x_coords[:point_count], y_coords[:point_count])).astype(np.float32)
        strokes.append(points)

    return strokes


def normalize_strokes(strokes: list[np.ndarray], canvas_size: float) -> list[np.ndarray]:
    if not strokes:
        return []

    all_points = np.concatenate(strokes, axis=0)
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
                delta = point - previous_point
                dx = float(delta[0])
                dy = float(delta[1])

            encoded_points.append([dx, dy, float(is_end), float(is_start)])
            previous_point = point

    return np.array(encoded_points, dtype=np.float32).reshape(-1, DRAWING_CONFIG.input_size)
