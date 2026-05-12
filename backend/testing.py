import os
import time
from pprint import pprint

from openai import OpenAI

import requests
from dotenv import load_dotenv


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


def test_aws_bedrock():
    client = OpenAI(api_key=os.getenv("AWS_BEDROCK_API_KEY"), base_url=os.getenv("AWS_BEDROCK_BASE_URL"), )

    response = client.responses.create(model="openai.gpt-oss-120b",
                                       input=[{"role": "user",
                                               "content": "Tell me about events hosted by the the drexel gaming association."}])
    print(response.output_text)


if __name__ == "__main__":
    load_dotenv()
    start = time.time()

    test_aws_bedrock()

    end = time.time()
    # print(f"Time taken: {round(end - start, 2)} seconds")
