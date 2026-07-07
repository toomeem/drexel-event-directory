import json
import os
from datetime import datetime
from urllib.parse import quote

import requests
from backend.python_files.helper_functions import stable_hash, normalize_time, is_athletic_event


def create_dragonlink_api_url(count):
    base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
    timestamp = quote(datetime.now().replace(microsecond=0).isoformat(), safe="")
    base_filters = "&orderByField=endsOn&orderByDirection=ascending&status=Approved&take="
    return base_url + "?endsAfter=" + timestamp + base_filters + str(count)


def collect_dragonlink_events(count):
    response = requests.get(create_dragonlink_api_url(count))
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return []

    response = dict(response.json())
    os.makedirs("../json_examples", exist_ok=True)
    with open("backend/json_examples/dragonlink_response.json", "w", encoding="utf-8") as f:
        json.dump(response, f, indent=4)

    return response["value"]


def dragonlink_event_parsing(event_json, kwargs, existing_event_ids):
    source = "dragonlink"
    dragonlink_base_url = "https://drexel.campuslabs.com/engage/"
    specific_events_to_exclude = ["12449523", "12449521", "12492168", "12490851", "12485439"]
    dragonlink_image_url = dragonlink_base_url + "image/"
    dragonlink_event_url = dragonlink_base_url + "event/"

    if str(event_json["id"]) in specific_events_to_exclude:
        return None

    kwargs["_id"] = stable_hash(source + str(event_json["id"]))
    if kwargs["_id"] in existing_event_ids:
        return None

    kwargs["name"] = event_json["name"]
    kwargs["org_name"] = event_json["organizationName"]
    kwargs["location"] = event_json["location"]
    kwargs["start_time"] = normalize_time(source, event_json["startsOn"])
    kwargs["end_time"] = normalize_time(source, event_json["endsOn"])
    kwargs["description"] = event_json["description"]

    if event_json["imagePath"]:
        kwargs["image_url"] = dragonlink_image_url + event_json["imagePath"]
    elif event_json["organizationProfilePicture"]:
        kwargs["image_url"] = dragonlink_image_url + event_json["organizationProfilePicture"]
    kwargs["event_link"] = dragonlink_event_url + event_json["id"]

    if is_athletic_event(kwargs["name"], kwargs["org_name"], kwargs["location"]):
        kwargs["theme"] = "athletics"
    elif event_json["theme"] in ["Arts", "Athletics", "Cultural", "Fundraising", "Social", "Spirituality"]:
        kwargs["theme"] = event_json["theme"].lower()
    elif "Credit" in event_json["categoryNames"] or event_json["theme"] == "CommunityService":
        kwargs["theme"] = "community"
    elif "Philanthropy" in event_json["categoryNames"] or "Fundraising" in event_json["categoryNames"]:
        kwargs["theme"] = "fundraising"
    elif "Social" in event_json["categoryNames"] or "Fraternity and Sorority Life" in event_json["categoryNames"]:
        kwargs["theme"] = "social"
    elif "Professional Development/Leadership" in event_json["categoryNames"] or "Leadership Development" in event_json[
        "categoryNames"] or "Networking" in event_json["categoryNames"]:
        kwargs["theme"] = "career"
    elif "Academic" in event_json["categoryNames"] or "Educational" in event_json["categoryNames"]:
        kwargs["theme"] = "academic"
    elif "Residence Life - Community and Civic Engagement" in event_json["categoryNames"]:
        kwargs["theme"] = "community"
    else:
        kwargs["theme"] = "social"

    kwargs["perks"] = [i.lower().replace(" ", "_") for i in event_json["benefitNames"]]

    return kwargs
