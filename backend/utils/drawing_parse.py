import base64
from io import BytesIO

from PIL import Image, ImageOps
# from torchvision import transforms
import torch
import math


# def base64_to_tensor(base64_string):
#     if "data:image" in base64_string:  # remove this part "data:image/png;base64,"
#         base64_string = base64_string.split(",")[1]
#     image_bytes = base64.b64decode(base64_string)  # decode the base64 string
#     img = Image.open(BytesIO(image_bytes))  # opense it in with pillow
#     if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
#         background = Image.new(
#             "RGB", img.size, (255, 255, 255)
#         )  # create a blank canvas with white bg
#         background.paste(img, mask=img.split()[3])  # paste the drawing on it
#         img = background  # new img = white canvas + actual drawing
#     img = img.convert("L")  # apply grayscale on the img
#     img = img.resize((28, 28))  # resize lol
#     img = ImageOps.invert(img)  # invert caus' we need black bg and white drawing
#     transform = (
#         transforms.ToTensor()
#     )  # transform the img to tensor and transform 0-255 to 0.0-1.0 values for colors
#     tensor = transform(img)
#     tensor = tensor.unsqueeze(
#         0
#     )  # add the batch size (means that the ai know that it's going to take 1 img)
#     return tensor

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
