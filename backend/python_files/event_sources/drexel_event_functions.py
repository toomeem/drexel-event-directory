import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash, normalize_time


class DrexelEventSource(EventSource):
    name = "drexel_events"
    priority = 1

    @staticmethod
    def _create_api_url(page):
        return f"https://drexel.edu/api/du/scevent?pageId=%7B1F80CA59-5675-4C76-B499-BA06662B3E34%7D&page={page}&perPage=10&sortOrder=asc&loadAllPages=false&q=&sortBy=relevance&startDate=&endDate="

    def _get_response(self, page):
        time.sleep(random.random() * 0.5)  # wait up to 0.5 seconds
        url = self._create_api_url(page)
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.text}")
            exit()
        if dict(response.json()) == {}:
            if page > 1:
                return []
            print(f"error with url: '{url}'")
            exit()
        return dict(response.json())["results"]

    def collect(self):
        results = []
        events_per_page = 10
        total_requests = (350 // events_per_page) + 1
        request_nums = range(1, total_requests + 1)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self._get_response, page) for page in request_nums]
            for future in as_completed(futures):
                results.extend(future.result())

        with open("backend/data_files/api_responses_json/drexel_events_response.json", "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)

        return results


    def parse(self, event_json, event_fields):
        correct_audiences = ["Undergraduate Students", "Graduate Students", "Everyone", "International Students",
                             "Prospective Students", "Senior Class"]
        excluded_event_ids = ["46659_123060"]
        event_fields["_id"] = stable_hash(self.name + str(event_json["id"]))

        if event_fields["_id"] in self.existing_event_ids:
            return None
        elif event_json["id"] in excluded_event_ids:
            return None
        elif "deadline" in str(event_json["typeNames"]).lower() or event_json["allDay"]:
            return None
        elif event_json["audiences"] and not any(i in event_json["audiences"] for i in correct_audiences):
            return None
        elif "registration for this event has closed" in event_json["body"].lower():
            return None
        elif "registration is now closed" in event_json["body"].lower():
            return None

        authors = event_json.get("authors")
        department_names = event_json.get("departmentNames")
        if authors:
            event_fields["org_name"] = authors[0]
        elif department_names:
            event_fields["org_name"] = department_names[0]
        research_keywords = ["PhD Research Proposal", "PhD Thesis Defense"]
        for keyword in research_keywords:
            if keyword in event_json["body"]:
                speaker = event_json["body"].split("Advisor:")[0]
                speaker = speaker.split("Speaker:")[1]
                speaker = speaker.split("<br />")[1]
                event_fields["org_name"] = speaker.replace(",", " -").strip(" ,.:\n\r ")
                break

        event_fields["name"] = event_json["title"]
        event_fields["location"] = event_json["address"]
        event_fields["start_time"] = normalize_time(event_json["startDate"])
        event_fields["end_time"] = normalize_time(event_json["endDate"])
        event_fields["event_link"] = event_json["contentUrl"]
        event_fields["description"] = event_json["body"]
        if event_json["image"]:
            event_fields["image_url"] = event_json["image"]

        type_names = event_json.get("typeNames") or []
        department_names = event_json.get("departmentNames") or []

        if "Exhibit" in type_names or "Performing Arts" in department_names:
            event_fields["theme"] = "arts"
        elif "Academic Events" in type_names or "Academic Support" in type_names:
            event_fields["theme"] = "academic"
        elif "SCDC: Information Sessions" in type_names or "SCDC: Workshops" in type_names:
            event_fields["theme"] = "academic"
        elif "Co-op & Career Development" in type_names or "Lectures" in type_names:
            event_fields["theme"] = "academic"
        elif "Diversity & Inclusion" in type_names:
            event_fields["theme"] = "cultural"
        elif "health advocate" in event_fields["description"].lower():
            event_fields["theme"] = "health"
        elif "ANS: Museum Activities" in type_names:
            event_fields["theme"] = "social"
        elif "Student Life & Organizations" in type_names:
            event_fields["theme"] = "social"
        elif "Seminars" in type_names:
            event_fields["theme"] = "academic"
        else:
            event_fields["theme"] = "social"

        features = event_json.get("features") or []
        for feature in features:
            if feature == "Giveaways":
                event_fields["perks"].append("giveaway")
            elif "credit" in feature.lower() or feature == "CEU Available":
                event_fields["perks"].append("credit")
            elif feature == "Free Food":
                event_fields["perks"].append("free_food")

        unknown_perks = [feature for feature in features
                         if feature and feature not in ("Free Food", "Free Stuff", "Credit", "Online Access",
                                                       "Giveaways", "CEU Available")]
        if unknown_perks:
            print(f"Unknown perk: {unknown_perks}")

        return event_fields
