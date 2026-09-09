import os,sys
import pandas as pd
import random
from PIL import Image, ImageDraw


def get_image(round_output_dir, image_paths):
    num_samples = 15
    samples = []
    for img in image_paths:
        update_file_path = img.replace(
            'data/',
            'sample_images/'
        )
        samples.append(update_file_path)
    available_imgs = []
    for img in samples:
        if os.path.exists(img):
            available_imgs.append(img)
    
    sample_imgs = random.sample(
        available_imgs,
        min(len(available_imgs), num_samples)
    )
    fig = collage(sample_imgs)
    fig = fig.convert('RGB')
    file_path = os.path.join(round_output_dir, 'collage.jpg')
    fig.save(file_path,format='jpeg',quality=25)
    return file_path


def collage(images):
    img_size = (1000, 800)
    space = 10
    num_columns = 5
    num_imgs = len(images)
    if num_imgs == 0:
        return Image.new('RGB', (1, 1), 'white')
    num_rows = (num_imgs + num_columns - 1) // num_columns
    background_width = (img_size[0] * num_columns +space * (num_columns + 1))
    background_height = (img_size[1] * num_rows +space * (num_rows + 1))
    background = Image.new('RGB',(background_width, background_height),'white')
    errors = 0
    for i, image_path in enumerate(images):
        # try:
        img = Image.open(image_path)
        img.thumbnail(img_size)
        column = i % num_columns
        row = i // num_columns
        x = (space + column * (img_size[0] + space) + (img_size[0] - img.width) // 2)
        y = (space + row * (img_size[1] + space) + (img_size[1] - img.height) // 2)
        background.paste(img, (x, y))
        img.close()
    return background