import unittest
from io import BytesIO
from unittest.mock import patch

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from backend.python_files.helper_functions import is_known_ai_image
from backend.python_files.image_parsing_functions import S3_BASE_PATH, get_image_s3_url, has_ai_image_metadata

AI_XMP = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description xmlns:Iptc4xmpExt="http://iptc.org/std/Iptc4xmpExt/2008-02-29/" '
    'Iptc4xmpExt:DigitalSourceType="http://cv.iptc.org/newscodes/digitalsourcetype/{source_type}"/>'
    '</rdf:RDF></x:xmpmeta>'
)


def png_bytes(xmp=None):
    info = PngInfo()
    if xmp is not None:
        info.add_itxt("XML:com.adobe.xmp", xmp)
    output = BytesIO()
    Image.new("RGB", (60, 40), "blue").save(output, format="PNG", pnginfo=info)
    return output.getvalue()


def rules(*ai_images):
    return patch("backend.python_files.helper_functions._load_data_file",
                 return_value={"ai_images": list(ai_images)})


class AiImageMetadataTests(unittest.TestCase):
    def test_detects_generative_ai_digital_source_types(self):
        for source_type in ("trainedAlgorithmicMedia", "compositeWithTrainedAlgorithmicMedia"):
            with self.subTest(source_type=source_type):
                self.assertTrue(has_ai_image_metadata(png_bytes(AI_XMP.format(source_type=source_type))))

    def test_ignores_images_without_ai_metadata(self):
        self.assertFalse(has_ai_image_metadata(png_bytes()))
        self.assertFalse(has_ai_image_metadata(png_bytes(AI_XMP.format(source_type="digitalCapture"))))


class AiImageRuleTests(unittest.TestCase):
    def test_bundled_rules_file_is_valid(self):
        self.assertFalse(is_known_ai_image("https://example.com/not-listed.jpg"))

    def test_matches_any_listed_reference(self):
        with rules("https://example.com/ai.jpg", "images/default_images/ai.jpg"):
            self.assertTrue(is_known_ai_image("https://example.com/ai.jpg"))
            self.assertTrue(is_known_ai_image(None, "images/default_images/ai.jpg"))
            self.assertFalse(is_known_ai_image("https://example.com/photo.jpg"))

    def test_rejects_malformed_rules(self):
        for bad_rules in ({}, {"ai_images": "x"}, {"ai_images": [""]}, {"ai_images": [1]}, []):
            with self.subTest(rules=bad_rules):
                with patch("backend.python_files.helper_functions._load_data_file", return_value=bad_rules):
                    with self.assertRaises(ValueError):
                        is_known_ai_image("https://example.com/ai.jpg")


@patch("backend.python_files.image_parsing_functions.upload_image_to_s3")
class GetImageS3UrlTests(unittest.TestCase):
    url = "https://example.com/flyer.png"

    def test_new_image_with_ai_metadata_is_labeled(self, upload):
        image = png_bytes(AI_XMP.format(source_type="trainedAlgorithmicMedia"))
        with rules(), \
                patch("backend.python_files.image_parsing_functions.image_in_s3", return_value=False), \
                patch("backend.python_files.image_parsing_functions.download_image", return_value=image):
            s3_url, is_ai_image = get_image_s3_url(self.url, "bucket")

        self.assertTrue(s3_url.startswith(S3_BASE_PATH))
        self.assertTrue(is_ai_image)
        upload.assert_called_once()

    def test_new_image_without_evidence_is_not_labeled(self, _upload):
        with rules(), \
                patch("backend.python_files.image_parsing_functions.image_in_s3", return_value=False), \
                patch("backend.python_files.image_parsing_functions.download_image", return_value=png_bytes()):
            self.assertFalse(get_image_s3_url(self.url, "bucket")[1])

    def test_cached_image_uses_rules_file_only(self, _upload):
        with patch("backend.python_files.image_parsing_functions.image_in_s3", return_value=True), \
                patch("backend.python_files.image_parsing_functions.download_image") as download:
            with rules():
                self.assertFalse(get_image_s3_url(self.url, "bucket")[1])
            with rules(self.url):
                self.assertTrue(get_image_s3_url(self.url, "bucket")[1])

        download.assert_not_called()

    def test_bucket_image_matches_by_s3_key(self, _upload):
        key = "images/default_images/ai_default.jpg"
        with rules(key):
            self.assertEqual(get_image_s3_url(S3_BASE_PATH + key, "bucket"), (S3_BASE_PATH + key, True))

    def test_failed_download_is_not_labeled(self, _upload):
        with rules(self.url), \
                patch("backend.python_files.image_parsing_functions.image_in_s3", return_value=False), \
                patch("backend.python_files.image_parsing_functions.download_image", return_value=None):
            self.assertEqual(get_image_s3_url(self.url, "bucket"), (None, False))


if __name__ == "__main__":
    unittest.main()
