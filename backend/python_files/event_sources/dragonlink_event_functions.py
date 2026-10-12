import json
from datetime import datetime
from urllib.parse import quote

import requests

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash, normalize_time


class DragonlinkEventSource(EventSource):
    name = "dragonlink"
    priority = 5

    @staticmethod
    def _create_api_url(count):
        base_url = "https://drexel.campuslabs.com/engage/api/discovery/event/search"
        timestamp = quote(datetime.now().replace(microsecond=0).isoformat(), safe="")
        base_filters = "&orderByField=endsOn&orderByDirection=ascending&status=Approved&take="
        return base_url + "?endsAfter=" + timestamp + base_filters + str(count)

    def collect(self):
        response = requests.get(self._create_api_url(350))
        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.text}")
            return []

        response = dict(response.json())
        with open("backend/data_files/api_responses_json/dragonlink_response.json", "w", encoding="utf-8") as f:
            json.dump(response, f, indent=4)

        return response["value"]

    def parse(self, event_json, event_fields):
        dragonlink_base_url = "https://drexel.campuslabs.com/engage/"
        specific_events_to_exclude = ["12449523", "12449521", "12492168", "12490851", "12485439"]
        dragonlink_image_url = dragonlink_base_url + "image/"
        dragonlink_event_url = dragonlink_base_url + "event/"

        if str(event_json["id"]) in specific_events_to_exclude:
            return None

        event_fields["_id"] = stable_hash(self.name + str(event_json["id"]))
        if event_fields["_id"] in self.existing_event_ids:
            return None

        event_fields["name"] = event_json["name"]
        event_fields["org_name"] = event_json["organizationName"]
        event_fields["location"] = event_json["location"]
        event_fields["start_time"] = normalize_time(event_json["startsOn"])
        event_fields["end_time"] = normalize_time(event_json["endsOn"])
        event_fields["description"] = event_json["description"]

        if event_json["imagePath"]:
            event_fields["image_url"] = dragonlink_image_url + event_json["imagePath"]
        elif event_json["organizationProfilePicture"]:
            event_fields["image_url"] = dragonlink_image_url + event_json["organizationProfilePicture"]
        event_fields["event_link"] = dragonlink_event_url + event_json["id"]

        if event_json["theme"] in ["Arts", "Athletics", "Cultural", "Fundraising", "Social", "Spirituality"]:
            event_fields["theme"] = event_json["theme"].lower()
        elif "Philanthropy" in event_json["categoryNames"] or "Fundraising" in event_json["categoryNames"]:
            event_fields["theme"] = "fundraising"
        elif "Social" in event_json["categoryNames"] or "Fraternity and Sorority Life" in event_json["categoryNames"]:
            event_fields["theme"] = "social"
        elif "Professional Development/Leadership" in event_json["categoryNames"] or "Leadership Development" in \
                event_json["categoryNames"] or "Networking" in event_json["categoryNames"]:
            event_fields["theme"] = "career"
        elif "Academic" in event_json["categoryNames"] or "Educational" in event_json["categoryNames"]:
            event_fields["theme"] = "academic"
        else:
            event_fields["theme"] = "social"

        event_fields["perks"] = [i.lower().replace(" ", "_") for i in event_json["benefitNames"]]

        return event_fields
