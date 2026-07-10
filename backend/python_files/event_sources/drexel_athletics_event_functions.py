import json
from datetime import datetime, timedelta

import requests
from backend.python_files.helper_functions import stable_hash, normalize_time


def create_drexel_athletics_api_url(days_out):
    # set default days_out to higher amount after streamlining data collection process
    now = datetime.now()
    start_date = now.strftime("%m-%d-%Y")
    end_date = (now + timedelta(days=days_out)).strftime("%m-%d-%Y")
    return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"


def collect_drexel_athletics_events(days_out):
    url = create_drexel_athletics_api_url(days_out)
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return []

    response_json = list(response.json())
    events_json = []

    for day in response_json:
        if day["events"] is None:
            continue
        for event in day["events"]:
            events_json.append(event)

    with open("backend/data_files/api_responses_json/drexel_athletics_response.json", "w", encoding="utf-8") as f:
        json.dump(events_json, f, indent=4)

    return events_json


def drexel_athletics_event_parsing(event_json, kwargs, existing_event_ids):
    source = "drexel_athletics"
    drexel_athletics_image = "https://drexel.edu/identity/~/media/Drexel/UMaC-Site-Group/Identity/Images/athletics/resized_logos/Athletics-Wordmark-DU-Blue-yellow-3200x1800-Identity-Images.jpg"
    drexel_athletics_schedule_url = "https://drexeldragons.com/sports/"
    drexel_athletics_aliases = {"mbball": "mens-basketball", "wbball": "womens-basketball", "mgolf": "mens-golf",
                                "mlax": "mens-lacrosse", "wlax": "womens-lacrosse", "mcrew": "mens-crew",
                                "wcrew": "womens-crew", "msoc": "mens-soccer", "wsoc": "womens-soccer",
                                "msquash": "mens-squash", "wsquash": "womens-squash",
                                "mswim": "mens-swimming-and-diving", "wswim": "womens-swimming-and-diving",
                                "mten": "mens-tennis", "wten": "womens-tennis", "wrestling": "wrestling",
                                "fhockey": "field-hockey", "softball": "softball", }

    kwargs["_id"] = stable_hash(source + str(event_json["id"]))
    if kwargs["_id"] in existing_event_ids:
        return None

    at_vs = event_json["atVs"]
    opponent = event_json["opponent"]["title"]
    sport_short_raw = event_json["sport"]["globalSportShortname"]
    sport_shorthand = drexel_athletics_aliases.get(sport_short_raw)
    if sport_shorthand is None:
        print(f"Unknown athletics sport shortname: {sport_short_raw}")
        sport_shorthand = sport_short_raw

    kwargs["name"] = " ".join(["DREX", at_vs, opponent])
    kwargs["org_name"] = f"Drexel {event_json['sport']['title']}"
    kwargs["location"] = event_json["location"].strip('.,-_ ')
    if event_json["facility"]:
        kwargs["location"] += f" ({event_json['facility']['title']})"
    kwargs["start_time"] = normalize_time(source, event_json["dateUtc"])
    kwargs["end_time"] = normalize_time(source, event_json["endDateUtc"])
    kwargs["image_url"] = drexel_athletics_image
    kwargs["event_link"] = drexel_athletics_schedule_url + sport_shorthand + "/schedule"
    kwargs["theme"] = "athletics"
    kwargs["perks"] = []
    return kwargs
