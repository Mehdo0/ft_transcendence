import base64
from io import BytesIO
from PIL import Image, ImageOps
from torchvision import transforms

def base64_to_tensor(base64_string):
    if "data:image" in base64_string: #remove this part "data:image/png;base64,"
        base64_string = base64_string.split(",")[1]
    image_bytes = base64.b64decode(base64_string) #decode the base64 string
    img = Image.open(BytesIO(image_bytes)) #opense it in with pillow
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info): 
        background = Image.new('RGB', img.size, (255, 255, 255)) #create a blank canvas with white bg
        background.paste(img, mask=img.split()[3]) #paste the drawing on it
        img = background #new img = white canvas + actual drawing
    img = img.convert('L') #apply grayscale on the img
    img = img.resize((28, 28)) #resize lol
    img = ImageOps.invert(img) # invert caus' we need black bg and white drawing
    transform = transforms.ToTensor() #transform the img to tensor and transform 0-255 to 0.0-1.0 values for colors
    tensor = transform(img)
    tensor = tensor.unsqueeze(0) #add the batch size (means that the ai know that it's going to take 1 img)
    return tensor
