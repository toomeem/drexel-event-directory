from datetime import datetime, timedelta

import requests
from backend.python_files.helper_functions import stable_hash


def ucity_district_event_parsing(event_json, kwargs, existing_event_ids):
    source = "ucity_district"
    # some of these are excluded because they are collected by the uCity square pipline
    excluded_event_names = ["Life Sciences Luncheon", "Weekly improvised music drop-in jam session",
                            "Food Truck Thursdays at The Lawn", "Monthly Innovation eXchange",
                            "Summer Series with Worldtown Soundsystem", "Wheelthrowing 101: Thursday Evenings",
                            "Native Futurism by Holly Wilson",
                            "Young Artist Summer Camp: Potions & Pigments: Art from the natural worlds"]
    excluded_event_locations = ["Booker's Restaurant & Bar", "Dahlak",
                                ]

    if event_json["title"] in excluded_event_names:
        return None
    elif event_json["meta"]["vibemap_event_hotspots_place"] in excluded_event_locations:
        return None

    kwargs["_id"] = stable_hash(source + str(event_json["id"]))
    if kwargs["_id"] in existing_event_ids:
        return None

    try:
        kwargs["start_time"] = datetime.strptime(event_json["meta"]["vibemap_event_start_date"], "%Y-%m-%dT%H:%M:%S")
        kwargs["end_time"] = datetime.strptime(event_json["meta"]["vibemap_event_end_date"], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        kwargs["start_time"] = datetime.strptime(event_json["meta"]["vibemap_event_start_date"], "%Y-%m-%d %H:%M:%S")
        kwargs["end_time"] = datetime.strptime(event_json["meta"]["vibemap_event_end_date"], "%Y-%m-%d %H:%M:%S")
    if (kwargs["end_time"] - kwargs["start_time"]) > timedelta(hours=24):
        return None

    kwargs["name"] = event_json["title"]
    if "vibemap_event_organizer" in event_json["meta"].keys():
        kwargs["org_name"] = event_json["meta"]["vibemap_event_organizer"]
    elif event_json["meta"]["vibemap_event_performers"]:
        kwargs["org_name"] = event_json["meta"]["vibemap_event_performers"]
    else:
        kwargs["org_name"] = event_json["meta"]["vibemap_event_hotspots_place"]

    kwargs["location"] = event_json["meta"]["vibemap_event_hotspots_place"]
    kwargs["image_url"] = event_json["featured_image"]
    kwargs["event_link"] = event_json["permalink"]
    kwargs["event_status"] = "in-person"
    kwargs["theme"] = "social"
    if event_json["meta"]["vibemap_event_recurs"]:
        kwargs["recurring"] = True
    kwargs["description"] = event_json["meta"]["vibemap_event_text_full"]

    return kwargs


def collect_ucity_district_events(count):
    response = requests.get(f"https://www.universitycity.org/wp-json/vibemap/v1/events-data?page=1&per_page={count}")
    return dict(response.json())["events"]
