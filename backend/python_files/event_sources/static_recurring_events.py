import json
from datetime import datetime, timedelta

from backend.python_files.event_sources.event_source import EventSource
from backend.python_files.helper_functions import stable_hash
from backend.python_files.paths import DATA_DIR


class StaticRecurringEventSource(EventSource):
    name = "static_recurring_events"
    priority = 6

    @staticmethod
    def _event_definitions():
        with (DATA_DIR / "static_recurring_events.json").open(encoding="utf-8") as f:
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

    def _first_occurrence(self, event_definition):
        date = self._next_occurrence(event_definition["weekday"])
        start_time = datetime.strptime(event_definition["start_time"], "%H:%M").time()
        start = datetime.combine(date, start_time)

        if event_definition["end_time"]:
            end_time = datetime.strptime(event_definition["end_time"], "%H:%M").time()
            end = datetime.combine(date, end_time)
        else:
            end = None

        return start, end

    def collect(self):
        occurrences = []
        for definition in self._event_definitions():
            first_start, first_end = self._first_occurrence(definition)
            for occurrence in range(6):
                offset = timedelta(days=7 * occurrence)
                start = first_start + offset
                end = first_end + offset if first_end else None
                occurrences.append((definition, start, end))
        return occurrences

    def parse(self, event_data):
        definition, start, end = event_data
        event_id = stable_hash(definition["name"] + str(start.timestamp()))
        if event_id in self.existing_event_ids:
            return None

        event_fields = self.new_event_draft()
        event_fields._id = event_id
        event_fields.name = definition["name"]
        event_fields.org_name = definition["org_name"]
        event_fields.location = definition["location"]
        event_fields.image_url = definition["image_url"]
        event_fields.start_time = start
        event_fields.end_time = end
        event_fields.event_link = definition["event_link"]
        event_fields.event_status = definition["event_status"]
        event_fields.theme = definition["theme"]
        event_fields.perks = list(definition["perks"])
        event_fields.food_related = definition["food_related"]
        event_fields.popular = definition["popular"]
        event_fields.recurring = True
        event_fields.for_new_students = definition["for_new_students"]
        return event_fields
