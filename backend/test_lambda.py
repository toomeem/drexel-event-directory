import os
import time
from pprint import pprint

import requests
from dotenv import load_dotenv


def test_lambda():
    load_dotenv()
    url = os.getenv("LAMBDA_ENDPOINT")
    response = requests.get(url, params={"page": 2})

    pprint(response.json())


if __name__ == "__main__":
    test_lambda()
