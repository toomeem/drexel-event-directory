from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from backend.python_files.helper_functions import stable_hash


def get_bbj_events():
    response = requests.get("https://blackbottomjazz.org/")
    soup = BeautifulSoup(response.text, "html.parser")
    event_cards = soup.find_all("div", class_="event-card")
    return event_cards


def bbj_event_parsing(event_data, kwargs, existing_event_ids):
    source = "bbj"
    kwargs["_id"] = stable_hash(source + str(event_data.get("data-num")))
    if kwargs["_id"] in existing_event_ids:
        return None

    kwargs["name"] = event_data.find("h2").text
    kwargs["org_name"] = "The Black Bottom Lives On!"
    kwargs["location"] = event_data.find("p", class_="event-location").text.strip()
    kwargs[
        "image_url"] = "https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/images/default_images/bbj.jpeg"
    kwargs["event_link"] = "https://blackbottomjazz.org/"
    kwargs["event_status"] = "in-person"
    kwargs["theme"] = "cultural"
    kwargs["recurring"] = True

    date_str = event_data.find("p", class_="event-date-line").text.strip()
    date = datetime.strptime(date_str.split("•")[0].strip(), "%A, %B %d").replace(year=2026)
    time_range = date_str.split("•")[1].strip().split("–")
    try:
        start_time = datetime.strptime(time_range[0].strip(), "%I:%M %p")
        end_time = datetime.strptime(time_range[1].strip(), "%I:%M %p")
    except ValueError:
        start_time = datetime.strptime(time_range[0].strip(), "%I:%M") + timedelta(hours=12)
        end_time = datetime.strptime(time_range[1].strip(), "%I:%M %p")
    kwargs["start_time"] = datetime.combine(date.date(), start_time.time())
    kwargs["end_time"] = datetime.combine(date.date(), end_time.time())

    return kwargs
