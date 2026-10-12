import unittest
from datetime import datetime, timedelta, timezone

from backend.python_files.event_class import Event, EventDraft


def make_event(**overrides):
    values = {
        "_id": "event-id",
        "source": "dragonlink",
        "name": "Test Event",
        "org_name": "Test Organization",
        "location": "Main Building",
        "image_url": "https://example.com/image.jpg",
        "start_time": datetime.now(timezone.utc) + timedelta(days=1),
        "end_time": datetime.now(timezone.utc) + timedelta(days=1, hours=1),
        "event_link": "https://example.com/event",
        "event_status": "in-person",
        "theme": "social",
        "perks": ["free_food"],
        "food_related": True,
        "popular": False,
        "recurring": False,
        "for_new_students": False,
        "on_campus": True,
        "religion": None,
    }
    values.update(overrides)
    return Event(**values)


class EventDraftTests(unittest.TestCase):
    def test_to_event_copies_fields(self):
        start = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
        draft = EventDraft(
            source="static",
            _id="123",
            name="Game Night",
            org_name="The Post",
            start_time=start,
            perks=["prizes"],
        )

        event = draft.to_event()

        self.assertEqual(event._id, "123")
        self.assertEqual(event.source, "static")
        self.assertEqual(event.start_time, start)
        self.assertEqual(event.perks, ["prizes"])

    def test_to_event_rejects_missing_required_fields(self):
        for draft in (
            EventDraft(source="test", name="Name", start_time=datetime.now()),
            EventDraft(source="test", _id="id", start_time=datetime.now()),
            EventDraft(source="test", _id="id", name="Name"),
        ):
            with self.subTest(draft=draft):
                with self.assertRaises(ValueError):
                    draft.to_event()


class EventTests(unittest.TestCase):
    def test_json_round_trip_preserves_event_data(self):
        event = make_event(
            start_time=datetime(2026, 10, 12, 18, 30),
            end_time=datetime(2026, 10, 12, 20),
        )

        restored = Event.from_json(event.to_json())

        self.assertEqual(restored.to_json(), event.to_json())

    def test_to_sql_serializes_perks(self):
        row = make_event(perks=["free_food", "prizes"]).to_sql()

        self.assertEqual(row[11], "free_food|prizes")
        self.assertEqual(len(row), 18)

    def test_same_source_events_with_same_start_and_org_are_equal(self):
        start = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
        first = make_event(_id="1", start_time=start)
        second = make_event(_id="2", name="Different title", start_time=start)

        self.assertEqual(first, second)

    def test_different_source_events_match_by_name_and_time(self):
        start = datetime(2026, 10, 12, 18, tzinfo=timezone.utc)
        first = make_event(source="dragonlink", start_time=start)
        second = make_event(source="drexel_events", start_time=start, org_name="Another Organization")

        self.assertEqual(first, second)

    def test_out_of_range_detects_past_and_distant_events(self):
        past = make_event(
            start_time=datetime.now(timezone.utc) - timedelta(days=2),
            end_time=datetime.now(timezone.utc) - timedelta(days=1),
        )
        distant = make_event(
            start_time=datetime.now(timezone.utc) + timedelta(days=20),
            end_time=None,
        )
        upcoming = make_event(
            start_time=datetime.now(timezone.utc) + timedelta(hours=2),
            end_time=None,
        )

        self.assertTrue(past.is_out_of_range(10))
        self.assertTrue(distant.is_out_of_range(10))
        self.assertFalse(upcoming.is_out_of_range(10))


if __name__ == "__main__":
    unittest.main()
