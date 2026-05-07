import json
import os
import time
from datetime import datetime, timedelta
from urllib.parse import quote

from openai import OpenAI
from pydantic import BaseModel

import psycopg2
import requests
from dotenv import load_dotenv
from event_class import Event


class OnlineStatus(BaseModel):
    event_status: str  # in-person, virtual, hybrid
    physical_location: str


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
    remove_list = ["\r", ", PA 19104", "Philadelphia"]
    replace_list = [(" Street", " St"), ("\n", " "), ("  ", " "), ("  ", " ")]
    suffixes = [" - Classroom w/ 14 PCs", " - Classroom", ","]
    for i in remove_list:
        location = location.replace(i, "")
    for old, new in replace_list:
        location = location.replace(old, new)
    location = location.strip()
    for suffix in suffixes:
        location = location.removesuffix(suffix)
    return location.strip()


def match_default_image(name, org_name, location):
    name = name.lower() if name else ""
    org_name = org_name.lower() if org_name else ""
    location = location.lower() if location else ""
    drexel_default_image = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/home/where-dragons-soar/lancasterwalk-area-lawn-3200x1600_16x9/lancasterwalk-area-lawn-3200x1600_16x9_16x9.jpg"
    pearlstein_image = "https://drexel.edu/news/~/media/Drexel/Core-Site-Group/News/Images/v2/story-images/2022/March/Pearlstein_gallery96-copy/pearlstein_gallery96-copy_16x9.jpg?w=3200&hash=E14D6C3BEF38BF17CAAD5EABC5C9162F"
    westphal_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQejsADyZdJy0QWh6odgCt42Bw9A5fsAPtXMg&s"
    dac_image = "https://www.sasaki.com/wp-content/uploads/2019/10/TurDRC09_website-1800x1350.jpg"
    main_building_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Main_Building_-_Drexel_University_%2853590618820%29.jpg/250px-Main_Building_-_Drexel_University_%2853590618820%29.jpg"
    hagerty_library_image = "https://pbs.twimg.com/media/G8D-sieWQAMOGeO.jpg"
    korman_image = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT3qHPfEMM3sZWBAwamvamv8lvT4LzQmfcwQw&s"
    pisb_image = "https://www.architectmagazine.com/wp-content/uploads/sites/5/2013/616a38fa-c2f8-4e1f-85e3-e23d8bcb9126.jpg"
    rush_building = "https://drexel.edu/~/media/Drexel/Core-Site-Group/Core/Images/admissions/virtual-tour/rush-building.jpg"
    med_building = "https://www.salus.edu/news-stories/_files/images/drexel-nursing-building-pic1.jpg"
    image_aliases = {
        "pearlstein gallery": pearlstein_image,
        "westphal": westphal_image,
        "dac": dac_image,
        "rec center": dac_image,
        "main building": main_building_image,
        "hagerty": hagerty_library_image,
        "korman": korman_image,
        "pisb": pisb_image,
        "papadakis": pisb_image,
        "science": pisb_image,
        "rush": rush_building,
        "lancaster": drexel_default_image,
        "nursing": med_building,
        "medicine": med_building,
    }
    for key, image in image_aliases.items():
        if key in name or key in org_name or key in location:
            return image
    return drexel_default_image


def get_online_status(client, location):
    response = client.chat.completions.parse(
        model="gpt-5-nano-2025-08-07",
        messages=[
            {
                "role": "system",
                "content":
                    '''
                        You are an expert at structured data extraction. 
                        You will be given information about the location of an event on Drexel University's campus and your task is to determine whether the event is hybrid, virtual or in-person. 
                        If an event is virtual, it will explicitly state that is is event_status/virtual and will likely say 'zoom' or 'meet'. If it doesn't clearly state that it is virtual, you will assume it is in-person.
                        You will first select the 'event_status' field. Here are the only allowed responses for the event_status field: ['in-person', 'virtual', 'hybrid'].
                        If the event is hybrid, It will explicitly state a physical location and that it is virtual/event_status. I will most likely signal this using 'and'/'&' or 'or' to show that there are multiple options. Example 'PISB 108 & Online'
                        For hybrid events, for the 'physical_location' parameter just return the physical location and ignore any information about the virtual aspect of the event. For in-person events, just return the location as the 'physical_location' and for virtual events, return 'N/A' for the physical location.
                 ''',
            },
            {"role": "user", "content": location},
        ],
        response_format=OnlineStatus,
    )
    response_object = response.choices[0].message.parsed
    return {"event_status": response_object.event_status, "physical_location": response_object.physical_location}


def dragonlink_event_parsing(event_json, kwargs):
    source = "dragonlink"
    dragonlink_base_url = "https://drexel.campuslabs.com/engage/"
    dragonlink_image_url = dragonlink_base_url + "image/"
    dragonlink_event_url = dragonlink_base_url + "event/"
    kwargs["name"] = event_json["name"]
    kwargs["org_name"] = event_json["organizationName"]
    kwargs["location"] = event_json["location"]
    kwargs["start_time"] = normalize_time(source, event_json["startsOn"])
    kwargs["end_time"] = normalize_time(source, event_json["endsOn"])
    if event_json["imagePath"]:
        kwargs["image_url"] = dragonlink_image_url + event_json["imagePath"]
    elif event_json["organizationProfilePicture"]:
        kwargs["image_url"] = dragonlink_image_url + event_json["organizationProfilePicture"]
    kwargs["event_link"] = dragonlink_event_url + event_json["id"]

    if event_json["theme"] in ["Arts", "Athletics", "Cultural", "Fundraising", "Social", "Spirituality"]:
        kwargs["theme"] = event_json["theme"]
    elif "Credit" in event_json["categoryNames"] or event_json["theme"] == "CommunityService":
        kwargs["theme"] = "Community"
    elif "Philanthropy" in event_json["categoryNames"] or "Fundraising" in event_json["categoryNames"]:
        kwargs["theme"] = "Fundraising"
    elif "Social" in event_json["categoryNames"] or "Fraternity and Sorority Life" in event_json["categoryNames"]:
        kwargs["theme"] = "Social"
    elif "Professional Development/Leadership" in event_json["categoryNames"] or "Leadership Development" in event_json[
        "categoryNames"] or "Networking" in event_json["categoryNames"]:
        kwargs["theme"] = "Career"
    elif "Academic" in event_json["categoryNames"] or "Educational" in event_json["categoryNames"]:
        kwargs["theme"] = "Academic"
    elif "Residence Life - Community and Civic Engagement" in event_json["categoryNames"]:
        kwargs["theme"] = "Community"
    else:
        kwargs["theme"] = "Social"
    # kwargs["perks"] = event_json["benefitNames"]
    return kwargs


def drexel_event_parsing(event_json, kwargs):
    source = "drexel_events"
    if "deadline" in str(event_json["typeNames"]).lower() or event_json["allDay"]:
        return None
    authors = event_json.get("authors")
    department_names = event_json.get("departmentNames")
    if authors:
        kwargs["org_name"] = authors[0]
    elif department_names:
        kwargs["org_name"] = department_names[0]
    else:
        kwargs["org_name"] = "Drexel University"

    kwargs["name"] = event_json["title"]
    kwargs["location"] = event_json["address"]
    kwargs["start_time"] = normalize_time(source, event_json["startDate"])
    kwargs["end_time"] = normalize_time(source, event_json["endDate"])
    kwargs["event_link"] = event_json["contentUrl"]
    if event_json["image"]:
        kwargs["image_url"] = event_json["image"]
    if event_json["typeNames"]:
        type_names = event_json["typeNames"]
        if "Exhibit" in type_names or "Performing Arts" in event_json["departmentNames"]:
            kwargs["theme"] = "Arts"
        elif "Academic Events" in type_names or "Academic Support" in type_names:
            kwargs["theme"] = "Academic"
        elif "SCDC: Information Sessions" in type_names or "SCDC: Workshops" in type_names:
            kwargs["theme"] = "Academic"
        elif "Co-op & Career Development" in type_names or "Lectures" in type_names:
            kwargs["theme"] = "Academic"
        elif "Diversity & Inclusion" in type_names:
            kwargs["theme"] = "Cultural"
        elif "Community Service" in type_names or "Civic Engagement" in type_names:
            kwargs["theme"] = "Community"
        elif "ANS: Museum Activities" in type_names:
            kwargs["theme"] = "Social"
        elif "Student Life & Organizations" in type_names:
            kwargs["theme"] = "Social"
        elif "Seminars" in type_names:
            kwargs["theme"] = "Academic"
        else:
            kwargs["theme"] = "Social"
    # kwargs["perks"] = event_json["benefitNames"]
    return kwargs


def drexel_athletics_event_parsing(event_json, kwargs):
    source = "drexel_athletics"
    drexel_athletics_image = "https://drexel.edu/identity/~/media/Drexel/UMaC-Site-Group/Identity/Images/athletics/resized_logos/Athletics-Wordmark-DU-Blue-yellow-3200x1800-Identity-Images.jpg"
    drexel_athletics_schedule_url = "https://drexeldragons.com/sports/"
    drexel_athletics_aliases = {
        "mbball": "mens-basketball",
        "wbball": "womens-basketball",
        "mgolf": "mens-golf",
        "mlax": "mens-lacrosse",
        "wlax": "womens-lacrosse",
        "mcrew": "mens-crew",
        "wcrew": "womens-crew",
        "msoc": "mens-soccer",
        "wsoc": "womens-soccer",
        "msquash": "mens-squash",
        "wsquash": "womens-squash",
        "mswim": "mens-swimming-and-diving",
        "wswim": "womens-swimming-and-diving",
        "mten": "mens-tennis",
        "wten": "womens-tennis",
        "wrestling": "wrestling",
        "fhockey": "field-hockey",
        "softball": "softball",
    }

    at_vs = event_json["atVs"]
    opponent = event_json["opponent"]["title"]
    sport_shorthand = drexel_athletics_aliases[event_json["sport"]["globalSportShortname"]]

    kwargs["name"] = " ".join(["DREX", at_vs, opponent])
    kwargs["org_name"] = f"Drexel {event_json['sport']['title']}"
    kwargs["location"] = event_json["location"]
    kwargs["start_time"] = normalize_time(source, event_json["dateUtc"])
    kwargs["end_time"] = normalize_time(source, event_json["endDateUtc"])
    kwargs["image_url"] = drexel_athletics_image
    kwargs["event_link"] = drexel_athletics_schedule_url + sport_shorthand + "/schedule"
    return kwargs


def create_event_object(source, event_json, client):
    online_keywords = ["zoom", "virtual", "hybrid", "handshake"]
    online_location_default_text = "Virtual Event"
    kwargs = {
        "_id": None,
        "source": source,
        "name": None,
        "org_name": None,
        "location": None,
        "image_url": None,
        "start_time": None,
        "end_time": None,
        "event_link": None,
        "event_status": None,
        "theme": None,
        "perks": [],
    }

    match source:
        case "dragonlink":
            kwargs = dragonlink_event_parsing(event_json, kwargs)
        case "drexel_events":
            kwargs = drexel_event_parsing(event_json, kwargs)
        case "drexel_athletics":
            kwargs = drexel_athletics_event_parsing(event_json, kwargs)
        case _:
            return None

    kwargs["_id"] = f"{source}:{kwargs['org_name']}:{event_json['id']}".lower()
    kwargs["_id"] = kwargs["_id"].replace(" ", "").replace("_", "").replace("-", "").replace("'", "").replace("\"", "")
    if kwargs["location"] is not None:
        kwargs["location"] = simplify_location(kwargs["location"])
    if kwargs["image_url"] is None:
        kwargs["image_url"] = match_default_image(kwargs["name"], kwargs["org_name"], kwargs["location"])

    if source == "drexel_athletics":
        kwargs["event_status"] = "in-person"
    elif any(keyword in str(kwargs["location"]).lower() for keyword in online_keywords):
        online_status_response = get_online_status(client, kwargs["location"])
        kwargs["event_status"] = online_status_response["event_status"]
        if kwargs["event_status"] == "hybrid":
            kwargs["location"] = online_status_response["physical_location"]
        elif kwargs["event_status"] == "virtual":
            kwargs["location"] = online_location_default_text
    else:
        kwargs["event_status"] = "in-person"

    return Event(**kwargs)


def create_dragonlink_api_url(count):
    base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
    timestamp = quote(datetime.now().replace(microsecond=0).isoformat(), safe="")
    base_filters = "&orderByField=endsOn&orderByDirection=ascending&status=Approved&take="
    return base_url + "?endsAfter=" + timestamp + base_filters + str(count)


def collect_dragonlink_events(count=100):
    response = requests.get(create_dragonlink_api_url(count))
    return dict(response.json())["value"]


def create_drexel_events_api_url(page=1):
    return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="


def collect_drexel_events(count=100):
    results = []
    for i in range(count // 10):
        response = requests.get(create_drexel_events_api_url(i + 1))
        results.extend(dict(response.json())["results"])
        time.sleep(.1)
    return results


def create_drexel_athletics_api_url(days_out=90):
    now = datetime.now()
    start_date = now.strftime("%m-%d-%Y")
    end_date = (now + timedelta(days=days_out)).strftime("%m-%d-%Y")
    return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"


def create_drexel_athletics_events():
    url = create_drexel_athletics_api_url()
    response = requests.get(url)

    response_json = list(response.json())
    events_json = []

    for day in response_json:
        if day["events"] is None:
            continue
        for event in day["events"]:
            events_json.append(event)

    return events_json


def collect_all_events(client):
    events = []
    events.extend([create_event_object("dragonlink", event_json, client) for event_json in collect_dragonlink_events()])
    events.extend([create_event_object("drexel_events", event_json, client) for event_json in collect_drexel_events()])
    events.extend(
        [create_event_object("drexel_athletics", event_json, client) for event_json in
         create_drexel_athletics_events()])

    # remove duplicates using __eq__; higher priority wins (kept as last occurrence)
    source_priority = {"drexel_events": 0, "drexel_athletics": 1, "dragonlink": 2}
    events = [e for e in events if e is not None]
    events.sort(key=lambda x: (x.start_time.timestamp(), source_priority.get(x.source, 0)))

    return [e for i, e in enumerate(events) if e not in events[i + 1:]]


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
            image_url=e["image_url"],
            start_time=datetime.fromtimestamp(e["start_time"]) if e["start_time"] else None,
            end_time=datetime.fromtimestamp(e["end_time"]) if e["end_time"] else None,
            event_link=e["event_link"]
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
                INSERT INTO main.events(id, source, name, org_name, location, image_url, start_time, end_time,
                                        event_link)
                VALUES (%s, %s, %s, %s, %s, %s, to_timestamp(%s), to_timestamp(%s), %s)
                ''',
                [(e[0], e[1], e[2], e[3], e[4], e[5], e[6], e[7], e[8]) for e in
                 [event.to_sql() for event in events]])


def fill_db():
    events = load_events_from_file()
    print(f"Uploading {len(events)} events to database...")
    save_events_to_db(events)


def update_events(client):
    print("Updating events...")
    events = collect_all_events(client)
    save_events_to_file(events)
    print(f"Saved {len(events)} events to file.")


if __name__ == "__main__":
    start = time.time()
    load_dotenv()
    client = OpenAI()

    # update_events(client)
    fill_db()

    end = time.time()
    print(f"Finished in {round(end - start, 2)} seconds.")
