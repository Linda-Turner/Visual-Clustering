import os
import random
from PIL import Image, ImageDraw, ImageFont
import textwrap



def get_image(
        cluster_img_desc: dict[list[tuple]],
        collage_outdir: str, 
        cluster_id: int, 
        draw_collage: bool
    ):
    """
    Create and save a collage containing a random selection of 15 random images from a cluster.

    Args: 
        collage_outdir (str): Directory where the generated collage will be saved.
        image_paths (list[tuple]): Paths to the images belonging to the cluster.
        cluster_id (int): Identifier of the cluster. This is used in the output filename.

    Returns:
        str: Path to the generated collage image.
    """
    current_cluster_img_desc = cluster_img_desc[str(cluster_id)]
    num_samples = 15
    available_img_desc = []
    for (img, desc) in current_cluster_img_desc:
        if os.path.exists(img):
            available_img_desc.append((img, desc))

    sample_imgs = random.sample(
        available_img_desc,
        min(len(available_img_desc), num_samples)
    )

    if draw_collage:
        images = [img for (img, _) in sample_imgs]
        images_fig = collage(images)
        images_fig = images_fig.convert('RGB')
        images_fig_file_path = os.path.join(collage_outdir, f'collage_{cluster_id}.jpg')
        images_fig.save(images_fig_file_path,format='jpeg',quality=25)
    else:
        sample_imgs = sample_imgs[:8]
        images_fig = desc_list(sample_imgs)
        images_fig = images_fig.convert('RGB')
        images_fig_file_path = os.path.join(collage_outdir, f'list_{cluster_id}.jpg')
        images_fig.save(images_fig_file_path,format='jpeg',quality=25)
    return images_fig_file_path


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
    background_width = (img_size[0] * num_columns + space * (num_columns + 1))
    background_height = (img_size[1] * num_rows + space * (num_rows + 1))
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



def desc_list(images_descriptions: list[tuple]):
    """
    Create an image containing the image-description pairs in two columns.

    Each entry consists of:
        (image_path, description)

    The image is displayed on the left and the corresponding
    description is displayed on the right.
    """
    output_width = 5060
    column_width = output_width // 2
    thumbnail_size = (1000, 800)
    space = 10
    font = ImageFont.truetype("arial.ttf", 50)

    num_imgs = len(images_descriptions)
    if num_imgs == 0:
        return Image.new('RGB', (1, 1), 'white')

    text_width = (column_width - thumbnail_size[0] - (3 * space))
    test_bbox = font.getbbox("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    average_char_width = ( test_bbox[2] - test_bbox[0]) / 26
    chars_per_line = max(10, int(text_width / average_char_width))
    left_items = images_descriptions[::2]
    right_items = images_descriptions[1::2]
    def prepare_item(item):
        image_path, description = item
        img = Image.open(image_path)
        img.thumbnail(thumbnail_size)
        lines = textwrap.wrap(str(description), width=chars_per_line)
        bbox = font.getbbox("Ag")
        line_height = bbox[3] - bbox[1] + 8
        text_height = max(line_height, len(lines) * line_height)
        height = max(thumbnail_size[1], text_height) + 2 * space
        return img, lines, height
    left_prepared = [prepare_item(item) for item in left_items]
    right_prepared = [prepare_item(item) for item in right_items]
    num_rows = max(len(left_prepared), len(right_prepared))
    row_heights = []
    for i in range(num_rows):
        heights = []
        if i < len(left_prepared):
            heights.append(left_prepared[i][2])
        if i < len(right_prepared):
            heights.append(right_prepared[i][2])
        row_heights.append(max(heights))
    output_height = (2 * space + sum(row_heights) + space * (num_rows - 1))
    result = Image.new("RGB", (output_width, output_height), "white")
    draw = ImageDraw.Draw(result)
    def draw_item(prepared, x, y, width, height):
        image, lines, item_height = prepared
        draw.rectangle([x, y, x + width, y + height], outline="lightgray", width=2)
        image_x = x + space
        image_y = y + (height - image.height) // 2
        result.paste(image, (image_x, image_y))
        text_x = (image_x + thumbnail_size[0] + space)
        text_y = y + space
        draw.multiline_text((text_x, text_y), "\n".join(lines), fill="black", font=font, spacing=8)
    y = space
    for i in range(num_rows):
        row_height = row_heights[i]
        if i < len(left_prepared):
            draw_item(left_prepared[i], space, y, column_width - space - space // 2, row_height)
        if i < len(right_prepared):
            draw_item(right_prepared[i], output_width // 2 + space // 2, y, column_width - space - space // 2, row_height)
        y += row_height + space
    return result