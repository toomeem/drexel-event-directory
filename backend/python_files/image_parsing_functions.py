from io import BytesIO
import time

import PIL
import boto3
import requests
from PIL import Image

from backend.python_files.helper_functions import stable_hash

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def upload_image_to_s3(bucket_name, image_data, s3_file_path):
    boto3.client("s3").put_object(
        Bucket=bucket_name,
        Key=s3_file_path,
        Body=image_data,
        ACL="public-read",
        ContentType="image/jpeg",
    )


def image_in_s3(bucket_name, s3_file_path):
    try:
        boto3.client("s3").head_object(Bucket=bucket_name, Key=s3_file_path)
        return True
    except Exception:
        return False


def download_image(url, max_attempts=3):
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, headers=headers, timeout=30)
        except requests.RequestException:
            break

        is_last_attempt = attempt == max_attempts - 1
        if response.status_code == 429 and not is_last_attempt:
            time.sleep(10)
            continue
        elif response.status_code >= 500 and not is_last_attempt:
            time.sleep(5)
            continue
        elif response.status_code != 200:
            break

        content_type = response.headers.get("Content-Type", "").lower()
        if content_type.startswith(("image/", "application/octet-stream", "binary/octet-stream")):
            return response.content
        break

    print(f"Error downloading image: {url}")
    return None


def resize_image(image_data, max_width=600, max_height=400):
    # crop image to desired aspect ratio and resize
    # also convert to jpeg and do other stuff to reduce file size
    # returns success value

    try:
        image = Image.open(BytesIO(image_data))
    except PIL.UnidentifiedImageError:
        print("Unidentified image data")
        return None
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

    output = BytesIO()
    image.save(output, format="JPEG", **save_kwargs)
    return output.getvalue()


def get_image_s3_url(original_url, bucket_name):
    # check if in s3, if not, add to s3
    # either way return the link to it
    if "drexel-events-general-bucket-034584778101" in original_url:
        return original_url

    s3_base_path = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/"
    image_file_types = [".jpg", ".jpeg", ".png", ".webp", ".aspx", ".gif", ".pdf"]
    file_type_list = [i for i in image_file_types if i in original_url.lower()]
    if len(file_type_list) > 0:
        file_type = file_type_list[0]
    else:
        file_type = ".jpg"

    if file_type == ".pdf":
        return None  # pdfs are not supported for now
    if original_url.count(file_type) > 1:
        original_url = original_url.split(file_type)[0] + file_type
    if "wikimedia.org/wikipedia/commons/thumb" in original_url:
        original_url = original_url.replace("/thumb", "", 1).replace("%28", "(", 1).replace("%29", ")", 1)

    url_hash = stable_hash(original_url)
    s3_file_path = "images/event_specific_images/" + url_hash + ".jpg"

    if not image_in_s3(bucket_name, s3_file_path):
        image_data = download_image(original_url)
        if image_data is None:
            return None
        resized_image = resize_image(image_data)
        if resized_image is None:
            print(f"Error resizing image: {original_url}")
            return None
        upload_image_to_s3(bucket_name, resized_image, s3_file_path)

    return s3_base_path + s3_file_path
