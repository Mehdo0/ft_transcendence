from PIL import Image, ImageOps
import torch
import math

MAX_MOVEMENTS = 150

def strokes_to_movements(strokes: list):
    movements = []

    for stroke in strokes:
        raw_points = stroke.get("points", [])
        points = clean_points(raw_points)

        for index, point in enumerate(points):
            x, y = point

            if index == 0:
                dx = 0.0
                dy = 0.0
            else:
                previous_x, previous_y = points[index - 1]
                dx = x - previous_x
                dy = y - previous_y
            
            if index == len(points) - 1:
                p_end = 1.0
            else:
                p_end = 0.0

            movements.append([dx, dy, p_end])
            if len(movements) >= MAX_MOVEMENTS:
                return movements
    return movements

def strokes_to_tensor(strokes: list):
    movements = strokes_to_movements(strokes)

    if not movements:
        movements = [[0.0, 0.0, 1.0]]
        has_drawing = False
    else:
        has_drawing = True

    src = torch.tensor([movements], dtype=torch.float32)
    mask = torch.zeros(1, len(movements), dtype=torch.bool)

    return src, mask, has_drawing

def clean_points(points: list):
    cleaned_points = []
    last_point = None
    for point in points:
        x = point["x"] * 255
        y = point["y"] * 255

        if last_point is not None:
            distance = math.hypot(x - last_point[0], y - last_point[1])

            if (distance < 4.0):
                continue
        
        cleaned_points.append((x, y))
        last_point = (x, y)
    
    return cleaned_points
