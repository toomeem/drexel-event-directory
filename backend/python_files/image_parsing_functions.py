import time

import PIL
from PIL import Image

import boto3
import requests
from backend.python_files.helper_functions import stable_hash


def upload_file_to_s3(bucket_name, local_file_path, s3_file_path):
    bucket = boto3.resource("s3").Bucket(bucket_name)
    bucket.upload_file(local_file_path, s3_file_path, ExtraArgs={"ACL": "public-read"})


def image_in_s3(bucket_name, file_name):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix="images/event_specific_images/")

    for obj in response.get('Contents', []):
        if file_name in obj["Key"]:
            return True
    return False


def resize_image(path, max_width=600, max_height=400):
    # crop image to desired aspect ratio and resize
    # also convert to jpeg and do other stuff to reduce file size
    # returns success value

    try:
        image = Image.open(path)
    except PIL.UnidentifiedImageError:
        print(f"UnidentifiedImageError: {path}")
        return False
    desired_aspect_ratio = max_width / max_height
    actual_aspect_ratio = image.width / image.height

    if actual_aspect_ratio != desired_aspect_ratio:
        if actual_aspect_ratio < desired_aspect_ratio:
            new_height = int(image.width / desired_aspect_ratio)
            new_width = image.width
        else:
            new_height = image.height
            new_width = int(image.height * desired_aspect_ratio)
        width_difference = abs(image.width - new_width)
        height_difference = abs(image.height - new_height)
        top_x = (width_difference // 2)
        top_y = (height_difference // 2)
        bottom_x = (width_difference // 2) + new_width
        bottom_y = (height_difference // 2) + new_height
        image = image.crop((top_x, top_y, bottom_x, bottom_y))

    image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
    if image.mode in ("RGBA", "LA", "P"):  # normalize to rgb
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])  # use alpha as mask
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    save_kwargs = {"optimize": True, "quality": 80, "progressive": True}

    image.save(path, format="JPEG", **save_kwargs)
    return True


def get_image_s3_url(original_url, bucket_name):
    # check if in s3, if not, add to s3
    # either way return the link to it
    if "drexel-events-general-bucket-034584778101" in original_url:
        return original_url

    s3_base_path = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/"

    image_name = stable_hash(original_url) + ".jpg"
    local_file_path = "backend/event_image_tmp_dir/" + image_name
    s3_file_path = "images/event_specific_images/" + image_name

    if not image_in_s3(bucket_name, image_name):
        img_data = requests.get(original_url)
        with open(local_file_path, "wb") as handler:
            handler.write(img_data.content)
        if not resize_image(local_file_path):
            time.sleep(0.5)
            img_data = requests.get(original_url)
            time.sleep(2)
            with open(local_file_path, "wb") as handler:
                handler.write(img_data.content)
            time.sleep(0.5)
            if not resize_image(local_file_path):
                print(f"Error resizing image: {original_url}")
                return None
        upload_file_to_s3(bucket_name, local_file_path, s3_file_path)

    return s3_base_path + s3_file_path
