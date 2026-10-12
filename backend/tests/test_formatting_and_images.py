import unittest
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import BytesIO
from io import StringIO
from zoneinfo import ZoneInfo

from PIL import Image

from backend.python_files.image_parsing_functions import resize_image
from backend.python_files.lambda_function import db_entry_to_json, is_date_only, make_time_str


PHILLY_TZ = ZoneInfo("America/New_York")


class TimeFormattingTests(unittest.TestCase):
    def test_single_time_uses_today_label(self):
        start = datetime.now(PHILLY_TZ).replace(hour=18, minute=30, second=0, microsecond=0)

        self.assertEqual(make_time_str(start, None), "Today @ 6:30 PM")

    def test_same_period_range_shows_ampm_once(self):
        start = datetime.now(PHILLY_TZ).replace(hour=18, minute=0, second=0, microsecond=0)
        end = start.replace(hour=20)

        self.assertEqual(make_time_str(start, end), "Today @ 6:00 - 8:00 PM")

    def test_cross_period_range_labels_both_periods(self):
        start = datetime.now(PHILLY_TZ).replace(hour=11, minute=30, second=0, microsecond=0)
        end = start.replace(hour=13, minute=0)

        self.assertEqual(make_time_str(start, end), "Today @ 11:30 AM - 1:00 PM")

    def test_overnight_range_labels_both_days(self):
        start = datetime.now(PHILLY_TZ).replace(hour=23, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=2)

        self.assertEqual(make_time_str(start, end), "Today @ 11:00 PM - Tomorrow @ 1:00 AM")

    def test_date_only_is_limited_to_athletics_midnight(self):
        midnight = datetime.now(PHILLY_TZ).replace(hour=0, minute=0, second=0, microsecond=0)

        self.assertTrue(is_date_only("drexel_athletics", midnight))
        self.assertFalse(is_date_only("dragonlink", midnight))
        self.assertFalse(is_date_only("drexel_athletics", midnight.replace(hour=1)))

    def test_database_row_conversion(self):
        start = datetime.now(PHILLY_TZ).replace(hour=18, minute=0, second=0, microsecond=0)
        row = (
            "id", "dragonlink", "Event", "Organization", "Main Hall",
            "https://example.com/image.jpg", start, start + timedelta(hours=1),
            "https://example.com/event", "in-person", "social",
            "free_food|prizes", True, False, False, True, True, None,
        )

        result = db_entry_to_json(row)

        self.assertEqual(result["id"], "id")
        self.assertEqual(result["perks"], ["free_food", "prizes"])
        self.assertEqual(result["time"], "Today @ 6 - 7 PM")


class ImageResizingTests(unittest.TestCase):
    @staticmethod
    def _image_bytes(mode, size, color, image_format):
        image = Image.new(mode, size, color)
        output = BytesIO()
        image.save(output, format=image_format)
        return output.getvalue()

    def test_resize_crops_to_target_ratio_and_outputs_jpeg(self):
        original = self._image_bytes("RGB", (1200, 1200), "blue", "PNG")

        resized = resize_image(original)

        result = Image.open(BytesIO(resized))
        self.assertEqual(result.format, "JPEG")
        self.assertEqual(result.size, (600, 400))
        self.assertEqual(result.mode, "RGB")

    def test_resize_flattens_transparency(self):
        original = self._image_bytes("RGBA", (600, 400), (255, 0, 0, 0), "PNG")

        resized = resize_image(original)

        result = Image.open(BytesIO(resized))
        self.assertEqual(result.mode, "RGB")

    def test_resize_rejects_non_image_data(self):
        with redirect_stdout(StringIO()):
            self.assertIsNone(resize_image(b"not an image"))


if __name__ == "__main__":
    unittest.main()
