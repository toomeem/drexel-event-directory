import json
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

from backend.python_files.event_class import Event, EventDraft
from backend.python_files.event_sources.dragonlink_event_functions import DragonlinkEventSource
from backend.python_files.event_sources.drexel_athletics_event_functions import DrexelAthleticsEventSource
from backend.python_files.event_sources.drexel_event_functions import DrexelEventSource
from backend.python_files.main import create_event_object, dedup_events
from backend.python_files.paths import API_RESPONSES_DIR


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


class SavedResponseParserTests(unittest.TestCase):
    @staticmethod
    def _load(file_name):
        with (API_RESPONSES_DIR / file_name).open(encoding="utf-8") as file:
            return json.load(file)

    def test_dragonlink_saved_response_produces_drafts(self):
        source = DragonlinkEventSource("unused", [], 60)
        raw_events = self._load("dragonlink_response.json")["value"]

        drafts = [source.parse(raw) for raw in raw_events[:25]]
        drafts = [draft for draft in drafts if draft is not None]

        self.assertTrue(drafts)
        self.assertTrue(all(isinstance(draft, EventDraft) for draft in drafts))
        self.assertTrue(all(draft.name and draft.start_time for draft in drafts))

    def test_drexel_events_saved_response_produces_drafts(self):
        source = DrexelEventSource("unused", [], 60)
        raw_events = self._load("drexel_events_response.json")

        drafts = [source.parse(raw) for raw in raw_events[:25]]
        drafts = [draft for draft in drafts if draft is not None]

        self.assertTrue(drafts)
        self.assertTrue(all(isinstance(draft, EventDraft) for draft in drafts))
        self.assertTrue(all(draft.name and draft.start_time for draft in drafts))

    def test_athletics_saved_response_produces_drafts(self):
        source = DrexelAthleticsEventSource("unused", [], 60)
        raw_events = self._load("drexel_athletics_response.json")

        drafts = [source.parse(raw) for raw in raw_events[:25]]

        self.assertTrue(drafts)
        self.assertTrue(all(isinstance(draft, EventDraft) for draft in drafts))
        self.assertTrue(all(draft.name and draft.start_time for draft in drafts))

    def test_parsers_skip_ids_that_already_exist(self):
        source = DragonlinkEventSource("unused", [], 60)
        raw = self._load("dragonlink_response.json")["value"][0]
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
