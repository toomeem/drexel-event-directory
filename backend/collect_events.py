import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import quote

import psycopg2
from dotenv import load_dotenv

import requests
from event_class import Event


def normalize_time(source, time_str):
    timezone = timedelta(hours=-4)
    if not time_str:
        return None
    match source:
        case "drexel_events":
            dt = datetime.fromisoformat(time_str) + timezone
            return dt
        case "drexel_athletics":
            dt = datetime.fromisoformat(time_str.replace("Z", "+00:00")) + timezone
            return dt
        case _:
            return datetime.fromisoformat(time_str) + timezone


def simplify_location(location):
    suffixes = [",", " - Classroom", " - Classroom w/ 14 PCs"]
    replace_list = [(" Street", " St"), ("\n", " "), ("  ", " "), ("  ", " ")]
    remove_list = ["\r", ", PA 19104", "Philadelphia"]
    location = location.strip()
    for suffix in suffixes:
        location = location.removesuffix(suffix)
    for old, new in replace_list:
        location = location.replace(old, new)
    for old in remove_list:
        location = location.replace(old, "")
    return location.strip()


def create_event_object(source, event_json):
    dragonlink_image_url = "https://drexel.campuslabs.com/engage/image/"
    drexel_athletics_default_image_url = "https://drexeldragons.com/images/sng_2023/footer_reccenter.png"
    drexel_default_image = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/home/where-dragons-soar/lancasterwalk-area-lawn-3200x1600_16x9/lancasterwalk-area-lawn-3200x1600_16x9_16x9.jpg"
    kwargs = {"_id": None,
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
            kwargs["name"] = event_json["name"]
            kwargs["org_name"] = event_json["organizationName"]
            kwargs["location"] = event_json["location"]
            kwargs["start_time"] = normalize_time(source, event_json["startsOn"])
            kwargs["end_time"] = normalize_time(source, event_json["endsOn"])
            if event_json["imagePath"]:
                kwargs["image_url"] = dragonlink_image_url + event_json["imagePath"]
            elif event_json["organizationProfilePicture"]:
                kwargs["image_url"] = dragonlink_image_url + event_json["organizationProfilePicture"]
            else:
                kwargs["image_url"] = drexel_default_image
        case "drexel_events":
            if "deadline" in str(event_json["typeNames"]).lower() or event_json["allDay"]:
                return None
            department_names = event_json.get("departmentNames")

            kwargs["name"] = event_json["title"]
            kwargs["org_name"] = department_names[0] if department_names else "Drexel University"
            kwargs["location"] = event_json["address"]
            kwargs["start_time"] = normalize_time(source, event_json["startDate"])
            kwargs["end_time"] = normalize_time(source, event_json["endDate"])
            if event_json["image"]:
                kwargs["image_url"] = event_json["image"]
            else:
                kwargs["image_url"] = drexel_default_image
        case "drexel_athletics":
            at_vs = event_json["atVs"]
            opponent = event_json["opponent"]["title"]

            kwargs["name"] = " ".join(["DREX", at_vs, opponent])
            kwargs["org_name"] = f"Drexel {event_json['sport']['title']}"
            kwargs["location"] = event_json["location"]
            kwargs["start_time"] = normalize_time(source, event_json["dateUtc"])
            kwargs["end_time"] = normalize_time(source, event_json["endDateUtc"])
            kwargs["image_url"] = drexel_athletics_default_image_url
        case _:
            return None
    kwargs["_id"] = f"{source}:{kwargs['org_name']}:{event_json['id']}".lower()
    kwargs["_id"] = kwargs["_id"].replace(" ", "").replace("_", "").replace("-", "").replace("'", "").replace("\"", "")
    if kwargs["location"] is not None:
        kwargs["location"] = simplify_location(kwargs["location"])
    return Event(**kwargs)


def create_dragonlink_url(count=15):
    base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
    timestamp = quote(datetime.now().replace(microsecond=0).isoformat(), safe="")
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
    now = datetime.now()
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

    return list({e._id: e for e in events if e is not None}.values())


def load_events_from_file(path="events.json"):
    with open(path) as f:
        events_json = json.load(f)
    events = []
    for e in events_json:
        events.append(Event(
            _id=e["id"],
            source=e["source"],
            name=e["name"],
            org_name=e["org_name"],
            location=e["location"],
            start_time=datetime.fromtimestamp(e["start_time"]) if e["start_time"] else None,
            end_time=datetime.fromtimestamp(e["end_time"]) if e["end_time"] else None,
            image_url=e["image_url"],
        ))
    return events


def save_events_to_file(events):
    with open("events.json", "w") as f:
        json.dump([event.to_json() for event in events], f, indent=4)


def save_events_to_db(events):
    with psycopg2.connect(
            host=os.getenv("RDS_ENDPOINT"),
            database="postgres",
            user=os.getenv("RDS_USERNAME"),
            password=os.getenv("RDS_PASSWORD"),
            port="5432"
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE main.events")
            cursor.executemany(
                '''
                INSERT INTO main.events(id, source, name, org_name, location, image_url, start_time, end_time)
                VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s), to_timestamp(%s))
                ''',
                [(e[0], e[1], e[2], e[3], e[4], e[7], e[5], e[6]) for e in [event.to_sql() for event in events]])


def fill_db():
    events = load_events_from_file()
    print(f"Events: {len(events)}")
    save_events_to_db(events)


def update_events():
    events = collect_all_events()
    print(f"Events: {len(events)}")
    save_events_to_file(events)


if __name__ == "__main__":
    load_dotenv()
    update_events()
    fill_db()
