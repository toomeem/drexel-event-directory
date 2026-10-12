import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from backend.python_files.event_class import Event, EventDraft
from backend.python_files.event_sources.dragonlink_event_functions import DragonlinkEventSource
from backend.python_files.event_sources.drexel_athletics_event_functions import DrexelAthleticsEventSource
from backend.python_files.event_sources.drexel_event_functions import DrexelEventSource
from backend.python_files.main import create_event_object, dedup_events


def make_event(event_id, source, name="Shared Event", org_name="Shared Org"):
    return Event(
        _id=event_id,
        source=source,
        name=name,
        org_name=org_name,
        location="Main Hall",
        image_url="https://example.com/image.jpg",
        start_time=datetime(2026, 10, 12, 18, tzinfo=timezone.utc),
        end_time=datetime(2026, 10, 12, 19, tzinfo=timezone.utc),
        event_link="https://example.com/event",
        event_status="in-person",
        theme="social",
        perks=[],
        food_related=False,
        popular=False,
        recurring=False,
        for_new_students=False,
        on_campus=True,
        religion=None,
    )


class SourceParserTests(unittest.TestCase):
    @staticmethod
    def _dragonlink_event():
        return {
            "id": "12345",
            "name": "Student Organization Social",
            "organizationName": "Test Organization",
            "location": "Main Hall",
            "startsOn": "2026-10-12T18:00:00-04:00",
            "endsOn": "2026-10-12T19:00:00-04:00",
            "description": "An event for students.",
            "imagePath": "event-image.jpg",
            "organizationProfilePicture": None,
            "theme": "Social",
            "categoryNames": [],
            "benefitNames": ["Free Food"],
        }

    @staticmethod
    def _drexel_event():
        return {
            "id": "12345_67890",
            "title": "Academic Workshop",
            "address": "Main Hall",
            "startDate": "2026-10-12T18:00:00",
            "endDate": "2026-10-12T19:00:00",
            "contentUrl": "https://drexel.edu/events/test",
            "body": "An event for all students.",
            "image": "https://example.com/event.jpg",
            "allDay": False,
            "audiences": ["Everyone"],
            "authors": ["Test Department"],
            "departmentNames": ["Academic Support"],
            "typeNames": ["Academic Events"],
            "features": ["Free Food"],
        }

    @staticmethod
    def _athletics_event():
        return {
            "id": 12345,
            "atVs": "vs",
            "opponent": {"title": "Test University"},
            "sport": {
                "globalSportShortname": "msoc",
                "title": "Men's Soccer",
            },
            "location": "Philadelphia, Pa.",
            "facility": {"title": "Vidas Field"},
            "allDay": False,
            "tbd": False,
            "date": "2026-10-12T18:00:00",
            "enddate": "2026-10-12T20:00:00",
            "dateUtc": "2026-10-12T22:00:00+00:00",
            "endDateUtc": "2026-10-13T00:00:00+00:00",
        }

    def test_dragonlink_response_produces_draft(self):
        draft = DragonlinkEventSource("unused", [], 60).parse(self._dragonlink_event())

        self.assertIsInstance(draft, EventDraft)
        self.assertEqual(draft.name, "Student Organization Social")
        self.assertEqual(draft.perks, ["free_food"])
        self.assertIsNotNone(draft.start_time)

    def test_drexel_events_response_produces_draft(self):
        draft = DrexelEventSource("unused", [], 60).parse(self._drexel_event())

        self.assertIsInstance(draft, EventDraft)
        self.assertEqual(draft.name, "Academic Workshop")
        self.assertEqual(draft.theme, "academic")
        self.assertIn("free_food", draft.perks)
        self.assertIsNotNone(draft.start_time)

    def test_athletics_response_produces_draft(self):
        draft = DrexelAthleticsEventSource("unused", [], 60).parse(self._athletics_event())

        self.assertIsInstance(draft, EventDraft)
        self.assertEqual(draft.name, "DREX vs Test University")
        self.assertEqual(draft.theme, "athletics")
        self.assertIn("Vidas Field", draft.location)
        self.assertIsNotNone(draft.start_time)

    def test_parsers_skip_ids_that_already_exist(self):
        source = DragonlinkEventSource("unused", [], 60)
        raw = self._dragonlink_event()
        draft = source.parse(raw)
        source_with_existing_id = DragonlinkEventSource("unused", [draft._id], 60)

        self.assertIsNone(source_with_existing_id.parse(raw))


class PipelineTests(unittest.TestCase):
    def test_deduplication_prefers_higher_priority_source(self):
        low_priority = make_event("low", "drexel_events")
        high_priority = make_event("high", "dragonlink")

        result = dedup_events([], [low_priority, high_priority])

        self.assertEqual(result, [high_priority])

    def test_deduplication_skips_event_already_in_database(self):
        existing = make_event("existing", "dragonlink")
        duplicate = make_event("new-id", "dragonlink")

        self.assertEqual(dedup_events([existing], [duplicate]), [])

    @patch(
        "backend.python_files.main.get_image_s3_url",
        return_value="https://example.com/cached.jpg",
    )
    def test_create_event_object_validates_enriches_and_converts(self, _get_image):
        class Source:
            name = "dragonlink"

            @staticmethod
            def parse(_raw):
                return EventDraft(
                    source="dragonlink",
                    _id="id",
                    name="Weekly Pizza Social",
                    org_name="Test Organization",
                    location="Main Hall",
                    image_url="https://example.com/original.jpg",
                    start_time=datetime(2026, 10, 12, 18),
                    description="Free food will be served.",
                )

        event = create_event_object(Source(), object(), "unused")

        self.assertIsInstance(event, Event)
        self.assertTrue(event.food_related)
        self.assertTrue(event.recurring)
        self.assertIn("free_food", event.perks)
        self.assertEqual(event.image_url, "https://example.com/cached.jpg")


if __name__ == "__main__":
    unittest.main()
