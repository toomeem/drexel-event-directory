import unittest
from datetime import datetime
from unittest.mock import patch

from backend.python_files.event_class import EventDraft
from backend.python_files.event_sources.static_recurring_events import StaticRecurringEventSource


class FixedDateTime(datetime):
    @classmethod
    def today(cls):
        # Monday
        return cls(2026, 10, 12, 9, 30)


class StaticRecurringDefinitionTests(unittest.TestCase):
    def setUp(self):
        self.source = StaticRecurringEventSource(
            bucket_name="unused",
            existing_event_ids=[],
            days_out=60,
        )

    def test_every_definition_has_valid_required_fields(self):
        required_fields = {
            "name",
            "org_name",
            "location",
            "image_url",
            "start_time",
            "end_time",
            "weekday",
            "event_link",
            "event_status",
            "theme",
            "perks",
            "food_related",
            "popular",
            "for_new_students",
        }
        valid_weekdays = {
            "monday", "tuesday", "wednesday", "thursday",
            "friday", "saturday", "sunday",
        }

        definitions = self.source._event_definitions()

        self.assertTrue(definitions)
        for definition in definitions:
            with self.subTest(event=definition.get("name")):
                self.assertTrue(required_fields.issubset(definition))
                self.assertTrue(definition["name"].strip())
                self.assertTrue(definition["org_name"].strip())
                self.assertTrue(definition["location"].strip())
                self.assertIn(definition["weekday"].lower(), valid_weekdays)
                datetime.strptime(definition["start_time"], "%H:%M")
                if definition["end_time"] is not None:
                    datetime.strptime(definition["end_time"], "%H:%M")
                self.assertIsInstance(definition["perks"], list)
                self.assertIn(definition["event_status"], {"in-person", "online", "hybrid"})
                self.assertTrue(definition["event_link"].startswith("http"))
                self.assertTrue(definition["image_url"].startswith("http"))

    @patch(
        "backend.python_files.event_sources.static_recurring_events.datetime",
        FixedDateTime,
    )
    def test_next_occurrence_uses_today_or_the_next_matching_weekday(self):
        self.assertEqual(self.source._next_occurrence("monday").date(), datetime(2026, 10, 12).date())
        self.assertEqual(self.source._next_occurrence("sunday").date(), datetime(2026, 10, 18).date())

    @patch(
        "backend.python_files.event_sources.static_recurring_events.datetime",
        FixedDateTime,
    )
    def test_collect_builds_six_weekly_occurrences_per_definition(self):
        definitions = self.source._event_definitions()

        occurrences = self.source.collect()

        self.assertEqual(len(occurrences), len(definitions) * 6)
        starts_for_first = [
            start for definition, start, _ in occurrences
            if definition["name"] == definitions[0]["name"]
        ]
        self.assertEqual(len(starts_for_first), 6)
        self.assertTrue(all(
            (later - earlier).days == 7
            for earlier, later in zip(starts_for_first, starts_for_first[1:])
        ))

    def test_parse_returns_complete_draft(self):
        definition = self.source._event_definitions()[0]
        start = datetime(2026, 10, 12, 18)
        end = datetime(2026, 10, 12, 20)

        draft = self.source.parse((definition, start, end))

        self.assertIsInstance(draft, EventDraft)
        self.assertEqual(draft.name, definition["name"])
        self.assertEqual(draft.start_time, start)
        self.assertEqual(draft.end_time, end)
        self.assertTrue(draft.recurring)
        self.assertIsNot(draft.perks, definition["perks"])
        self.assertIsNotNone(draft.to_event())

    def test_parse_skips_existing_event_id(self):
        definition = self.source._event_definitions()[0]
        occurrence = (definition, datetime(2026, 10, 12, 18), None)
        draft = self.source.parse(occurrence)
        source_with_existing_id = StaticRecurringEventSource(
            bucket_name="unused",
            existing_event_ids=[draft._id],
            days_out=60,
        )

        self.assertIsNone(source_with_existing_id.parse(occurrence))


if __name__ == "__main__":
    unittest.main()
