import time

import requests

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
from event_class import Event


def create_dragonlink_url(count=15):
    base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
    timestamp = quote(datetime.now(ZoneInfo("America/New_York")).replace(microsecond=0).isoformat(), safe="")
    base_filters = "&orderByField=endsOn&orderByDirection=ascending&status=Approved&take="
    return base_url + "?endsAfter=" + timestamp + base_filters + str(count)


def collect_dragonlink_events(count=100):
    response = requests.get(create_dragonlink_url(count))

    events_json = dict(response.json())["value"]

    with open("json_examples/dragonlink_response.json", "w") as f:
        json.dump(events_json, f)


def create_drexel_events_url(page=1):
    return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="


def collect_drexel_events(count=100):
    results = []
    for i in range(count // 10):
        response = requests.get(create_drexel_events_url(i + 1))
        events_json = dict(response.json())["results"]
        results.extend(events_json)
        time.sleep(.5)

    with open("json_examples/drexel_events_response.json", "w") as f:
        json.dump(results, f)


def create_drexel_athletics_url(days_out=30):
    now = datetime.now(ZoneInfo("America/New_York"))
    start_date = now.strftime("%m-%d-%Y")
    end_date = (now + timedelta(days=days_out)).strftime("%m-%d-%Y")
    return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"


def create_drexel_athletics_events():
    url = create_drexel_athletics_url()
    response = requests.get(url)

    events_json = list(response.json())

    with open("json_examples/drexel_athletics_response.json", "w") as f:
        json.dump(events_json, f)


def main():
    create_drexel_athletics_events()


if __name__ == "__main__":
    main()
    # pprint(quote(datetime.now(ZoneInfo("America/New_York")).replace(microsecond=0).isoformat(), safe=""))