import os
import time
from pprint import pprint

import requests
from PIL import Image


def test_eventbrite():
    url = "https://www.eventbrite.com/d/pa--philadelphia/free--events/"
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br, zstd", "Accept-Language": "en-US,en;q=0.9",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"}
    # url = "https://www.eventbrite.com/api/v3/promoted/events"
    response = requests.get(url, headers=headers)
    print(response.status_code, response.text)


def test_lambda():
    url = os.getenv("LAMBDA_ENDPOINT")
    response = requests.get(url, params={"page": 2})

    pprint(response.json())


def event_id_hash(hash_str):
    return hex(abs(hash(hash_str)))[2:]


def resize_image(path):
    image = Image.open(path)
    aspect_ratio = image.width / image.height

    resized_image = image.resize((600, 400))

    resized_image.save(path.replace("1", ""))


if __name__ == "__main__":
    # load_dotenv()
    start = time.time()

    resize_image("rush-building1.jpg")

    end = time.time()  # print(f"Time taken: {round(end - start, 2)} seconds")
