import time

import requests

import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
from event_class import Event


def normalize_time(source, time_str):
    timezone = ZoneInfo("America/New_York")
    if not time_str:
        return None
    match source:
        case "drexel_events":
            dt = datetime.fromisoformat(time_str).replace(tzinfo=timezone)
            return dt
        case "drexel_athletics":
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone)
        case _:
            return datetime.fromisoformat(time_str).astimezone(timezone)


def create_event_object(source, event_json):
    dragonlink_image_url = "https://drexel.campuslabs.com/engage/image/"
    drexel_athletics_default_image_url = "https://drexeldragons.com/images/sng_2023/footer_reccenter.png"
    kwargs = {"event_id": None,
              "source": source,
              "name": None,
              "org_name": None,
              "location": None,
              "start_time": None,
              "end_time": None,
              "image_url": None
              }

    match source:
        case "dragonlink":
            kwargs["event_id"] = event_json["id"]
            kwargs["name"] = event_json["name"]
            kwargs["org_name"] = event_json["organizationName"]
            kwargs["location"] = event_json["location"]
            kwargs["start_time"] = normalize_time(source, event_json["startsOn"])
            kwargs["end_time"] = normalize_time(source, event_json["endsOn"])
            if event_json["imagePath"]:
                kwargs["image_url"] = dragonlink_image_url + event_json["imagePath"]
        case "drexel_events":
            if "deadline" in str(event_json["typeNames"]).lower() or event_json["allDay"]:
                return None
            department_names = event_json.get("departmentNames")
            kwargs["event_id"] = event_json["id"]
            kwargs["name"] = event_json["title"]
            kwargs["org_name"] = department_names[0] if department_names else "Drexel University"
            kwargs["location"] = event_json["address"]
            kwargs["start_time"] = normalize_time(source, event_json["startDate"])
            kwargs["end_time"] = normalize_time(source, event_json["endDate"])
            kwargs["image_url"] = event_json["image"]
        case "drexel_athletics":
            at_vs = event_json["atVs"]
            opponent = event_json["opponent"]["title"]
            kwargs["event_id"] = event_json["id"]
            kwargs["name"] = " ".join(["DREX", at_vs, opponent])
            kwargs["org_name"] = f"Drexel {event_json['sport']['title']}"
            kwargs["location"] = event_json["location"]
            kwargs["start_time"] = normalize_time(source, event_json["dateUtc"])
            kwargs["end_time"] = normalize_time(source, event_json["endDateUtc"])
            kwargs["image_url"] = drexel_athletics_default_image_url  # TODO: get images for each sport
        case _:
            return None
    return Event(**kwargs)


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
        time.sleep(.1)
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
    events.extend([create_event_object("dragonlink", event_json) for event_json in collect_dragonlink_events()])
    events.extend([create_event_object("drexel_events", event_json) for event_json in collect_drexel_events()])
    events.extend(
        [create_event_object("drexel_athletics", event_json) for event_json in create_drexel_athletics_events()])

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
