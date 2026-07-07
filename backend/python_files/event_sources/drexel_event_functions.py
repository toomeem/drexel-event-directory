import json
import os
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from backend.python_files.helper_functions import stable_hash, normalize_time


def create_drexel_events_api_url(page):
    return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="


def get_drexel_events_response(page):
    time.sleep(random.random() * 0.5)
    response = requests.get(create_drexel_events_api_url(page))
    if response.status_code != 200:
        print(f"Error: {response.status_code} {response.text}")
        return []
    return dict(response.json())["results"]


def collect_drexel_events(count):
    results = []
    events_per_page = 10
    max_threads = 5
    total_requests = (count // events_per_page) + 1
    requests_nums = [i for i in range(1, total_requests + 1)]

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(get_drexel_events_response, i) for i in requests_nums]
        for future in as_completed(futures):
            results.extend(future.result())

    os.makedirs("../json_examples", exist_ok=True)
    with open("backend/json_examples/drexel_events_response.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)

    return results


def drexel_event_parsing(event_json, kwargs, existing_event_ids):
    source = "drexel_events"
    correct_audiences = ["Undergraduate Students", "Graduate Students", "Everyone", "International Students",
                         "Prospective Students", "Senior Class"]
    excluded_event_ids = ["46659_123060"]
    kwargs["_id"] = stable_hash(source + str(event_json["id"]))

    if kwargs["_id"] in existing_event_ids:
        return None
    elif event_json["id"] in excluded_event_ids:
        return None
    elif "deadline" in str(event_json["typeNames"]).lower() or event_json["allDay"]:
        return None
    elif event_json["audiences"] and not any([i in event_json["audiences"] for i in correct_audiences]):
        return None
    elif "registration for this event has closed" in event_json["body"].lower():
        return None
    elif "registration is now closed" in event_json["body"].lower():
        return None

    authors = event_json.get("authors")
    department_names = event_json.get("departmentNames")
    if authors:
        kwargs["org_name"] = authors[0]
    elif department_names:
        kwargs["org_name"] = department_names[0]
    research_keywords = ["PhD Research Proposal", "PhD Thesis Defense"]
    for i in research_keywords:
        if i in event_json["body"]:
            speaker = event_json["body"].split("Advisor:")[0]
            speaker = speaker.split("Speaker:")[1]
            speaker = speaker.split("<br />")[1]
            kwargs["org_name"] = speaker.replace(",", " -").strip(" ,.:\n\r")
            break

    kwargs["name"] = event_json["title"]
    kwargs["location"] = event_json["address"]
    kwargs["start_time"] = normalize_time(source, event_json["startDate"])
    kwargs["end_time"] = normalize_time(source, event_json["endDate"])
    kwargs["event_link"] = event_json["contentUrl"]
    kwargs["description"] = event_json["body"]
    if event_json["image"]:
        kwargs["image_url"] = event_json["image"]

    type_names = event_json.get("typeNames") or []
    department_names = event_json.get("departmentNames") or []

    if "Exhibit" in type_names or "Performing Arts" in department_names:
        kwargs["theme"] = "arts"
    elif "Academic Events" in type_names or "Academic Support" in type_names:
        kwargs["theme"] = "academic"
    elif "SCDC: Information Sessions" in type_names or "SCDC: Workshops" in type_names:
        kwargs["theme"] = "academic"
    elif "Co-op & Career Development" in type_names or "Lectures" in type_names:
        kwargs["theme"] = "academic"
    elif "Diversity & Inclusion" in type_names:
        kwargs["theme"] = "cultural"
    elif "health advocate" in kwargs["description"].lower():
        kwargs["theme"] = "health"
    elif "Community Service" in type_names or "Civic Engagement" in type_names:
        kwargs["theme"] = "community"
    elif "ANS: Museum Activities" in type_names:
        kwargs["theme"] = "social"
    elif "Student Life & Organizations" in type_names:
        kwargs["theme"] = "social"
    elif "Seminars" in type_names:
        kwargs["theme"] = "academic"
    else:
        kwargs["theme"] = "social"

    features = event_json.get("features") or []
    for feature in features:
        if feature == "Giveaways":
            kwargs["perks"].append("giveaway")
        elif "credit" in feature.lower() or feature == "CEU Available":
            kwargs["perks"].append("credit")
        elif feature == "Free Food":
            kwargs["perks"].append("free_food")

    unknown_perks = [f for f in features if
                     f and f not in ("Free Food", "Free Stuff", "Credit", "Online Access", "Giveaways",
                                     "CEU Available")]
    if unknown_perks:
        print(f"Unknown perk: {unknown_perks}")

    return kwargs
