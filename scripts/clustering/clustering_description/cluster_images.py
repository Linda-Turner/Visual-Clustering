import os,sys
import pandas as pd
import random
from PIL import Image, ImageDraw

def get_image(
        collage_outdir: str, 
        image_paths: list[str], 
        cluster_id: int
    ):
    """
    Create and save a collage containing a random selection of 15 random images from a cluster.

    Args: 
        collage_outdir (str): Directory where the generated collage will be saved.
        image_paths (list[str]): Paths to the images belonging to the cluster.
        cluster_id (int): Identifier of the cluster. This is used in the output filename.

    Returns:
        str: Path to the generated collage image.
    """
    num_samples = 15
    samples = image_paths
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
    file_path = os.path.join(collage_outdir, f'collage_{cluster_id}.jpg')
    fig.save(file_path,format='jpeg',quality=25)
    return file_path


def collage(images: list[str]):
    """
    Create a grid collage from a collection of images. 
    Images are resized to fit within a fixed 1000x800 pixel area and arranged in five columns. 

    Args:
        images (list[str]): Paths to the images that should be included in the collage.

    Returns
        PIL.Image.Image: A PIL Image containing the generated collage.
    """

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
    for i, image_path in enumerate(images):
        img = Image.open(image_path)
        img.thumbnail(img_size)
        column = i % num_columns
        row = i // num_columns
        x = (space + column * (img_size[0] + space) + (img_size[0] - img.width) // 2)
        y = (space + row * (img_size[1] + space) + (img_size[1] - img.height) // 2)
        background.paste(img, (x, y))
        img.close()
    return background