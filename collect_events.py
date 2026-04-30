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
    return dict(response.json())["value"]


def create_drexel_events_url(page=1):
    return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="


def collect_drexel_events(count=100):
    results = []
    for i in range(count // 10):
        response = requests.get(create_drexel_events_url(i + 1))
        results.extend(dict(response.json())["results"])

    return results


def create_drexel_athletics_url(days_out=30):
    now = datetime.now(ZoneInfo("America/New_York"))
    start_date = now.strftime("%m-%d-%Y")
    end_date = (now + timedelta(days=days_out)).strftime("%m-%d-%Y")
    return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"


def create_drexel_athletics_events():
    url = create_drexel_athletics_url()
    response = requests.get(url)

    response_json = list(response.json())
    events_json = []

    for day in response_json:
        if day["events"] is None:
            continue
        for event in day["events"]:
            events_json.append(event)

    return events_json


def collect_all_events():
    events = []
    events.extend([Event.from_dragonlink_json(event_json) for event_json in collect_dragonlink_events()])
    events.extend([Event.from_drexel_events_json(event_json) for event_json in collect_drexel_events()])
    events.extend([Event.from_drexel_athletics_json(event_json) for event_json in create_drexel_athletics_events()])
    return [i for i in events if i is not None]


def save_events(events):
    with open("events.json", "w") as f:
        json.dump([event.to_json() for event in events], f, indent=4)


def main():
    events = collect_all_events()
    print(f"Events: {len(events)}")
    save_events(events)


if __name__ == "__main__":
    main()