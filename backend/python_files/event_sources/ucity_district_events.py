from datetime import datetime

import requests

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash


class UCityDistrictEventSource(EventSource):
    name = "ucity_district"
    priority = 4

    def collect(self):
        excluded_url_keywords = ["little-explorers", "allison-zuckerman", "ortizs-war", "benedetta-tagliabue",
                                 "food-truck-thursdays", "septa-replacing-trolleys-with-buses",
                                 "health-center-career-day", "fugitivity-of-water-2", "coffee-with-a-codex",
                                 "manuscript-studies-interest-group", "black-womens-debt-free-college-pathways",
                                 "penn-led-international-action-collaborative",
                                 "guided-tour-sacred-objects-religion-and-ritual", "gswsfqt-open-house",
                                 "archaeology-institute-of-america-lecture",
                                 "professional-development-webinar-series",
                                 "building-resilience-through-ptsd-massage",
                                 "restorative-yoga-ayurvedic-bodywork", "rend-collective",
                                 "penn-student-making-workshop", "ralph-lemon-the-fugitivity-of-water",
                                 "youth-soccer", "sas-commons"]
        response = requests.get(
            "https://www.universitycity.org/wp-json/vibemap/v1/events-data?page=1&per_page=500", timeout=30)
        return [event for event in dict(response.json())["events"]
                if not any(keyword in event["permalink"] for keyword in excluded_url_keywords)]

    def parse(self, event_json):
        event_fields = self.new_event_draft()
        # Some events are excluded because they are collected by the uCity Square pipeline.
        excluded_event_names = ["Weekly improvised music drop-in jam session", "Monthly Innovation eXchange",
                                "Summer Series with Worldtown Soundsystem", "Wheelthrowing 101: Thursday Evenings",
                                "Native Futurism by Holly Wilson",
                                "Young Artist Summer Camp: Potions & Pigments: Art from the natural worlds"]
        excluded_event_locations = ["Booker's Restaurant & Bar", "Dahlak"]

        if event_json["title"] in excluded_event_names:
            return None
        elif event_json["meta"]["vibemap_event_hotspots_place"] in excluded_event_locations:
            return None
        elif event_json["meta"]["vibemap_event_is_all_day"]:
            return None
        elif event_json["meta"]["vibemap_event_organizer"] == "Penn Libraries":
            return None

        event_fields._id = stable_hash(self.name + str(event_json["id"]))
        if event_fields._id in self.existing_event_ids:
            return None

        try:
            event_fields.start_time = datetime.strptime(
                event_json["meta"]["vibemap_event_start_date"], "%Y-%m-%dT%H:%M:%S")
            event_fields.end_time = datetime.strptime(
                event_json["meta"]["vibemap_event_end_date"], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            event_fields.start_time = datetime.strptime(
                event_json["meta"]["vibemap_event_start_date"], "%Y-%m-%d %H:%M:%S")
            event_fields.end_time = datetime.strptime(
                event_json["meta"]["vibemap_event_end_date"], "%Y-%m-%d %H:%M:%S")
        if event_fields.end_time.day != event_fields.start_time.day:
            return None

        event_fields.name = event_json["title"]
        if "vibemap_event_organizer" in event_json["meta"].keys():
            event_fields.org_name = event_json["meta"]["vibemap_event_organizer"]
        elif event_json["meta"]["vibemap_event_performers"]:
            event_fields.org_name = event_json["meta"]["vibemap_event_performers"]
        else:
            event_fields.org_name = event_json["meta"]["vibemap_event_hotspots_place"]

        event_fields.location = event_json["meta"]["vibemap_event_hotspots_place"]
        event_fields.image_url = event_json["featured_image"]
        event_fields.event_link = event_json["permalink"]
        event_fields.event_status = "in-person"
        event_fields.theme = "social"
        if event_json["meta"]["vibemap_event_recurs"]:
            event_fields.recurring = True
        event_fields.description = event_json["meta"]["vibemap_event_text_full"]

        return event_fields
