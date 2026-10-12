import unittest
from datetime import datetime

from backend.python_files.event_class import EventDraft
from backend.python_files.helper_functions import (
    enrich_perks,
    get_event_status,
    get_religion,
    is_food_related,
    is_for_new_students,
    is_invalid_event,
    is_on_campus,
    is_recurring,
    normalize_time,
    simplify_event_name,
    simplify_location,
    stable_hash,
)


class HelperFunctionTests(unittest.TestCase):
    def test_stable_hash_is_deterministic(self):
        self.assertEqual(stable_hash("event"), stable_hash("event"))
        self.assertEqual(stable_hash("event"), "4119639092e62c55ea8be348e4d9260d")
        self.assertNotEqual(stable_hash("event"), stable_hash("another event"))

    def test_normalize_time_handles_empty_naive_and_aware_values(self):
        self.assertIsNone(normalize_time(None))
        self.assertEqual(normalize_time("2026-10-12T18:30:00"), datetime(2026, 10, 12, 18, 30))
        self.assertEqual(
            normalize_time("2026-10-12T18:30:00-04:00").utcoffset().total_seconds(),
            -4 * 60 * 60,
        )

    def test_event_status_classifies_online_hybrid_and_in_person(self):
        self.assertEqual(get_event_status("dragonlink", "Zoom"), "online")
        self.assertEqual(get_event_status("dragonlink", "Main Hall and virtual"), "hybrid")
        self.assertEqual(get_event_status("dragonlink", "Main Hall"), "in-person")
        self.assertEqual(get_event_status("drexel_athletics", "Online"), "in-person")

    def test_rule_based_labels_cover_common_event_language(self):
        self.assertTrue(is_food_related("Pizza Social", [], "Main Hall", ""))
        self.assertTrue(is_recurring("Weekly Game Night", ""))
        self.assertTrue(is_for_new_students("New Student Welcome", ""))
        self.assertEqual(
            get_religion("Community Dinner", "Chabad Student Group", "Main Hall"),
            "jewish",
        )

    def test_enrich_perks_deduplicates_matches(self):
        perks = enrich_perks("Free pizza", "Free food will be served", ["free_food"])

        self.assertEqual(perks.count("free_food"), 1)

    def test_on_campus_matching_is_case_insensitive_for_known_off_campus_org(self):
        self.assertFalse(
            is_on_campus(
                "Networking",
                "Biomed Grad Student Association",
                "Graduate Campus",
            )
        )

    def test_simplification_helpers_normalize_common_values(self):
        self.assertEqual(simplify_event_name("Hosted by Test Group"), "")
        self.assertEqual(simplify_location("Main Auditorium"), "Main Building Auditorium")

    def test_invalid_event_rejects_missing_required_fields(self):
        valid = EventDraft(
            source="test",
            _id="id",
            name="A Valid Event",
            location="Main Hall",
            start_time=datetime(2026, 10, 12, 18),
        )

        self.assertTrue(is_invalid_event(None))
        self.assertTrue(is_invalid_event(EventDraft(source="test")))
        self.assertFalse(is_invalid_event(valid))


if __name__ == "__main__":
    unittest.main()
