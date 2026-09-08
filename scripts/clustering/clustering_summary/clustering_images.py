
def do_something():
    out_dir = 'exp'
    num_samples = 16

    samples = dict()
    for cluster in images:
        if cluster == -1: continue
        sample_imgs = random.sample(images[cluster], min(len(images[cluster]),num_samples))
        samples[cluster] = []
        for img in sample_imgs:
            update_file_path = img.replace('data/','/Volumes/StorageArch/Facebook/XR-FFF/')
            update_file_path = update_file_path.replace('exctinction','extinction')
            samples[cluster].append(update_file_path)
            #print('C' + str(cluster) + ' ' + update_file_path)

    for cluster in samples:
        texts = [''] * len(samples[cluster])
        fig = collage(samples[cluster], texts)
        fig = fig.convert('RGB')
        fig.save(out_dir + '/' + str(cluster)+".jpg", format='jpeg', quality=25)

def collage(images, texts):
    from PIL import Image, ImageDraw, ImageFont
    import math
    import cv2 as cv
    font = ImageFont.truetype("Comic Sans MS.ttf", 25)
    img_size = (500,500)
    space = 30
    num_imgs = len(images)
    num_columns = math.floor(math.sqrt(num_imgs))
    num_rows = num_imgs // num_columns
    if num_imgs % num_columns:
        num_rows += 1
    
    errors = 0
    background_width = img_size[0]*num_columns + (space*num_columns)
    background_height = img_size[1]*num_rows + (space*num_rows) + space
    background = Image.new('RGBA', (background_width, background_height), (255, 255, 255, 255))
    x = 0
    y = space
    for i, image in enumerate(images):
        try:
            img = Image.open(image)
            if img.width >= img.height:
                size = (img_size[0], int(img_size[1]*img.height/img.width))
                img = img.resize(size)
            else:
                size = (int(img_size[0]*img.width/img.height), img_size[1])
                img = img.resize(size)
            
            
            x_offset = int((img_size[0] - img.width)/2)
            y_offset = int((img_size[1] - img.height)/2)
        except Exception as e:
            print("IERROR: " + str(e) + " " + image, file=sys.stderr)
            errors += 1
            continue
        
        background.paste(img, (x+x_offset, y+y_offset))
        draw = ImageDraw.Draw(background)
        draw.text((x, y-space), texts[i], (0,0,0), font=font)
        x += img_size[0] + space
        if (i+1) % num_columns == 0:
            y += img_size[1] + space
            x = 0
        img.close()
    print("Number of errors: " + str(errors), file=sys.stderr)
    return background