import json
from copy import deepcopy
from datetime import datetime, timedelta

from backend.python_files.event_class import Event
from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash
from backend.python_files.image_parsing_functions import get_image_s3_url


class StaticRecurringEventSource(EventSource):
    name = "static_recurring_events"
    priority = 6

    @staticmethod
    def _event_definitions():
        with open("backend/data_files/static_recurring_events.json") as f:
            return json.load(f)

    @staticmethod
    def _weekday_num(weekday_str):
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6,
        }
        return weekdays[weekday_str.lower()]

    def _next_occurrence(self, weekday_str):
        weekday_num = self._weekday_num(weekday_str)
        now = datetime.today()
        while now.weekday() != weekday_num:
            now += timedelta(days=1)
        return now

    def _definition_to_event(self, event_definition):
        date = self._next_occurrence(event_definition["weekday"])
        start_time = datetime.strptime(event_definition["start_time"], "%H:%M").time()
        start = datetime.combine(date, start_time)

        if event_definition["end_time"]:
            end_time = datetime.strptime(event_definition["end_time"], "%H:%M").time()
            end = datetime.combine(date, end_time)
        else:
            end = None

        event_id = stable_hash(event_definition["name"] + str(start.timestamp()))
        image_url = get_image_s3_url(event_definition["image_url"], self.bucket_name)

        return Event(
            _id=event_id,
            source=self.name,
            name=event_definition["name"],
            org_name=event_definition["org_name"],
            location=event_definition["location"],
            image_url=image_url,
            start_time=start,
            end_time=end,
            event_link=event_definition["event_link"],
            event_status=event_definition["event_status"],
            theme=event_definition["theme"],
            perks=event_definition["perks"],
            food_related=event_definition["food_related"],
            popular=event_definition["popular"],
            recurring=True,
            for_new_students=event_definition["for_new_students"],
            on_campus=True,
            religion=None,
        )

    def collect(self):
        original_events = [self._definition_to_event(definition) for definition in self._event_definitions()]
        all_events = []

        for original_event in original_events:
            all_events.append(original_event)
            for occurrence in range(1, 6):
                new_event = deepcopy(original_event)
                new_event.start_time = original_event.start_time + timedelta(days=7 * occurrence)
                if original_event.end_time:
                    new_event.end_time = original_event.end_time + timedelta(days=7 * occurrence)
                new_event._id = stable_hash(new_event.name + str(new_event.start_time.timestamp()))
                all_events.append(new_event)

        event_dicts = []
        for event in all_events:
            if event._id in self.existing_event_ids:
                continue
            event_dict = event.to_json()
            event_dict["_id"] = event_dict.pop("id")
            event_dict["description"] = ""
            event_dict["start_time"] = datetime.fromtimestamp(event_dict["start_time"])
            if event_dict["end_time"]:
                event_dict["end_time"] = datetime.fromtimestamp(event_dict["end_time"])
            event_dicts.append(event_dict)

        return event_dicts

    def parse(self, event_data, event_fields):
        return event_data
