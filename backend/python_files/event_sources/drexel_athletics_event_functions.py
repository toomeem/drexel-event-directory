import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash, normalize_time


class DrexelAthleticsEventSource(EventSource):
    name = "drexel_athletics"
    priority = 2

    @staticmethod
    def _local_midnight(date_str):
        if not date_str:
            return None
        return datetime.fromisoformat(date_str[:10]).replace(tzinfo=ZoneInfo("America/New_York"))

    def _create_api_url(self):
        now = datetime.now()
        start_date = now.strftime("%m-%d-%Y")
        end_date = (now + timedelta(days=self.days_out)).strftime("%m-%d-%Y")
        return f"https://drexeldragons.com/api/v2/Calendar/from/{start_date}/to/{end_date}"

    def collect(self):
        response = requests.get(self._create_api_url(), timeout=30)

        if response.status_code != 200:
            print(f"Error: {response.status_code} {response.text}")
            return []

        events_json = []
        for day in list(response.json()):
            if day["events"] is not None:
                events_json.extend(day["events"])

        with open("backend/data_files/api_responses_json/drexel_athletics_response.json", "w", encoding="utf-8") as f:
            json.dump(events_json, f, indent=4)

        return events_json

    def parse(self, event_json, event_fields):
        drexel_athletics_image = "https://drexel.edu/identity/~/media/Drexel/UMaC-Site-Group/Identity/Images/athletics/resized_logos/Athletics-Wordmark-DU-Blue-yellow-3200x1800-Identity-Images.jpg"
        drexel_athletics_schedule_url = "https://drexeldragons.com/sports/"
        drexel_athletics_aliases = {"mbball": "mens-basketball", "wbball": "womens-basketball",
                                    "mgolf": "mens-golf", "mlax": "mens-lacrosse", "wlax": "womens-lacrosse",
                                    "mcrew": "mens-crew", "wcrew": "womens-crew", "msoc": "mens-soccer",
                                    "wsoc": "womens-soccer", "msquash": "mens-squash",
                                    "wsquash": "womens-squash", "mswim": "mens-swimming-and-diving",
                                    "wswim": "womens-swimming-and-diving", "mten": "mens-tennis",
                                    "wten": "womens-tennis", "wrestling": "wrestling",
                                    "fhockey": "field-hockey", "softball": "softball"}

        event_fields["_id"] = stable_hash(self.name + str(event_json["id"]))
        if event_fields["_id"] in self.existing_event_ids:
            return None

        at_vs = event_json["atVs"]
        opponent = event_json["opponent"]["title"]
        sport_short_raw = event_json["sport"]["globalSportShortname"]
        sport_shorthand = drexel_athletics_aliases.get(sport_short_raw)
        if sport_shorthand is None:
            print(f"Unknown athletics sport shortname: {sport_short_raw}")
            sport_shorthand = sport_short_raw

        event_fields["name"] = " ".join(["DREX", at_vs, opponent])
        if at_vs == "at":
            event_fields["on_campus"] = False
        event_fields["org_name"] = f"Drexel {event_json['sport']['title']}"
        event_fields["location"] = event_json["location"].strip('.,-_ ')
        if event_json["facility"]:
            event_fields["location"] += f" ({event_json['facility']['title']})"
        if event_json["allDay"] or event_json["tbd"]:
            # Date-only events are stored at local midnight for make_time_str.
            event_fields["start_time"] = self._local_midnight(event_json["date"])
            event_fields["end_time"] = self._local_midnight(event_json["enddate"])
        else:
            event_fields["start_time"] = normalize_time(event_json["dateUtc"])
            event_fields["end_time"] = normalize_time(event_json["endDateUtc"])
        event_fields["image_url"] = drexel_athletics_image
        event_fields["event_link"] = drexel_athletics_schedule_url + sport_shorthand + "/schedule"
        event_fields["theme"] = "athletics"

        return event_fields
