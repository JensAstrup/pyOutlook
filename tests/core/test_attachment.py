import base64
from datetime import datetime
from unittest import TestCase

from pyOutlook.core.attachment import Attachment


class AttachmentTestCase(TestCase):
    """Test suite for the Attachment class."""

    def test_init__with_all_parameters(self):
        """Test that Attachment initializes correctly with all parameters provided."""
        name = "test_file.pdf"
        content = base64.b64encode(b"test content").decode('utf-8')
        outlook_id = "AAMkAGI2THVSAAA="
        size = 1024
        last_modified = datetime(2024, 1, 15, 10, 30, 0)
        content_type = "application/pdf"

        attachment = Attachment(
            name=name,
            content=content,
            outlook_id=outlook_id,
            size=size,
            last_modified=last_modified,
            content_type=content_type
        )

        self.assertEqual(attachment.name, name)
        self.assertEqual(attachment._content, content)
        self.assertEqual(attachment.bytes, base64.b64decode(content))
        self.assertEqual(attachment.outlook_id, outlook_id)
        self.assertEqual(attachment.size, size)
        self.assertEqual(attachment.last_modified, last_modified)
        self.assertEqual(attachment.content_type, content_type)

    def test_init__with_minimal_parameters(self):
        """Test that Attachment initializes correctly with only required parameters."""
        name = "document.txt"
        content = base64.b64encode(b"minimal content").decode('utf-8')

        attachment = Attachment(name=name, content=content)

        self.assertEqual(attachment.name, name)
        self.assertEqual(attachment._content, content)
        self.assertEqual(attachment.bytes, base64.b64decode(content))
        self.assertIsNone(attachment.outlook_id)
        self.assertIsNone(attachment.size)
        self.assertIsNone(attachment.last_modified)
        self.assertIsNone(attachment.content_type)

    def test_init__with_none_optional_parameters(self):
        """Test that Attachment handles explicit None values for optional parameters."""
        name = "file.doc"
        content = base64.b64encode(b"content").decode('utf-8')

        attachment = Attachment(
            name=name,
            content=content,
            outlook_id=None,
            size=None,
            last_modified=None,
            content_type=None
        )

        self.assertEqual(attachment.name, name)
        self.assertEqual(attachment._content, content)
        self.assertIsNone(attachment.outlook_id)
        self.assertIsNone(attachment.size)
        self.assertIsNone(attachment.last_modified)
        self.assertIsNone(attachment.content_type)

    def test_init__bytes_decoded_correctly(self):
        """Test that base64 content is correctly decoded to bytes."""
        original_bytes = b"This is a test file with special chars: \x00\x01\x02\xff"
        content = base64.b64encode(original_bytes).decode('utf-8')

        attachment = Attachment(name="binary_file.bin", content=content)

        self.assertEqual(attachment.bytes, original_bytes)

    def test_init__empty_content(self):
        """Test that Attachment handles empty content correctly."""
        content = base64.b64encode(b"").decode('utf-8')

        attachment = Attachment(name="empty.txt", content=content)

        self.assertEqual(attachment._content, content)
        self.assertEqual(attachment.bytes, b"")

    def test_init__with_zero_size(self):
        """Test that Attachment handles zero size correctly."""
        content = base64.b64encode(b"some content").decode('utf-8')

        attachment = Attachment(name="file.txt", content=content, size=0)

        self.assertEqual(attachment.size, 0)

    def test_init__with_large_size(self):
        """Test that Attachment handles large size values correctly."""
        content = base64.b64encode(b"data").decode('utf-8')
        large_size = 1024 * 1024 * 100  # 100 MB

        attachment = Attachment(name="large_file.zip", content=content, size=large_size)

        self.assertEqual(attachment.size, large_size)

    def test_init__with_various_content_types(self):
        """Test that Attachment handles different content types correctly."""
        content = base64.b64encode(b"content").decode('utf-8')
        content_types = [
            "text/plain",
            "application/pdf",
            "image/jpeg",
            "application/vnd.ms-excel",
            "application/octet-stream"
        ]

        for content_type in content_types:
            with self.subTest(content_type=content_type):
                attachment = Attachment(
                    name=f"file.{content_type.split('/')[-1]}",
                    content=content,
                    content_type=content_type
                )
                self.assertEqual(attachment.content_type, content_type)

    def test_iter__yields_correct_format(self):
        """Test that __iter__ yields the correct dictionary format for API upload."""
        name = "upload_file.pdf"
        content = base64.b64encode(b"file content").decode('utf-8')
        content_type = "application/pdf"

        attachment = Attachment(name=name, content=content, content_type=content_type)

        result = dict(attachment)

        expected = {
            '@odata.type': '#microsoft.graph.fileAttachment',
            'name': name,
            'contentBytes': content,
            'contentType': content_type
        }

        self.assertEqual(result, expected)

    def test_iter__yields_correct_order(self):
        """Test that __iter__ yields items in the expected order."""
        name = "ordered_file.txt"
        content = base64.b64encode(b"test").decode('utf-8')
        content_type = "text/plain"

        attachment = Attachment(name=name, content=content, content_type=content_type)

        items = list(attachment)

        expected_order = [
            ('@odata.type', '#microsoft.graph.fileAttachment'),
            ('name', name),
            ('contentBytes', content),
            ('contentType', content_type)
        ]

        self.assertEqual(items, expected_order)

    def test_iter__with_none_content_type(self):
        """Test that __iter__ includes None content_type when not set."""
        name = "no_type.bin"
        content = base64.b64encode(b"binary").decode('utf-8')

        attachment = Attachment(name=name, content=content)

        result = dict(attachment)

        self.assertIn('contentType', result)
        self.assertIsNone(result['contentType'])

    def test_iter__omits_optional_fields(self):
        """Test that __iter__ only includes fields needed for upload, not all instance attributes."""
        name = "file.txt"
        content = base64.b64encode(b"content").decode('utf-8')
        outlook_id = "AAMkAGI2THVSAAA="
        size = 512
        last_modified = datetime.now()

        attachment = Attachment(
            name=name,
            content=content,
            outlook_id=outlook_id,
            size=size,
            last_modified=last_modified
        )

        result = dict(attachment)

        # These fields should NOT be in the upload format
        self.assertNotIn('outlook_id', result)
        self.assertNotIn('size', result)
        self.assertNotIn('last_modified', result)
        self.assertNotIn('bytes', result)
        self.assertNotIn('_content', result)

    def test_iter__reusable(self):
        """Test that __iter__ can be called multiple times on the same instance."""
        name = "reusable.txt"
        content = base64.b64encode(b"data").decode('utf-8')

        attachment = Attachment(name=name, content=content)

        result1 = dict(attachment)
        result2 = dict(attachment)

        self.assertEqual(result1, result2)

    def test_init__with_unicode_filename(self):
        """Test that Attachment handles Unicode characters in filename correctly."""
        unicode_names = [
            "文档.pdf",
            "Тест.txt",
            "café_résumé.doc",
            "emoji_😀.png"
        ]
        content = base64.b64encode(b"content").decode('utf-8')

        for name in unicode_names:
            with self.subTest(name=name):
                attachment = Attachment(name=name, content=content)
                self.assertEqual(attachment.name, name)

    def test_init__with_special_characters_in_filename(self):
        """Test that Attachment handles special characters in filename."""
        special_names = [
            "file (1).txt",
            "document-v2.pdf",
            "report_2024.xlsx",
            "file.backup.tar.gz"
        ]
        content = base64.b64encode(b"content").decode('utf-8')

        for name in special_names:
            with self.subTest(name=name):
                attachment = Attachment(name=name, content=content)
                self.assertEqual(attachment.name, name)

    def test_bytes__immutable_after_init(self):
        """Test that bytes attribute reflects the decoded content correctly."""
        original_data = b"Test data for immutability check"
        content = base64.b64encode(original_data).decode('utf-8')

        attachment = Attachment(name="test.bin", content=content)

        # Verify bytes is correct
        self.assertEqual(attachment.bytes, original_data)

        # Verify it's a fresh decode each time (not cached in a mutable way)
        self.assertEqual(attachment.bytes, base64.b64decode(attachment._content))

    def test_init__with_past_last_modified(self):
        """Test that Attachment handles past datetime for last_modified."""
        past_date = datetime(2020, 1, 1, 0, 0, 0)
        content = base64.b64encode(b"old file").decode('utf-8')

        attachment = Attachment(
            name="old_file.txt",
            content=content,
            last_modified=past_date
        )

        self.assertEqual(attachment.last_modified, past_date)

    def test_init__with_future_last_modified(self):
        """Test that Attachment handles future datetime for last_modified."""
        future_date = datetime(2030, 12, 31, 23, 59, 59)
        content = base64.b64encode(b"future file").decode('utf-8')

        attachment = Attachment(
            name="future_file.txt",
            content=content,
            last_modified=future_date
        )

        self.assertEqual(attachment.last_modified, future_date)

    def test_iter__multiple_iterations_on_same_object(self):
        """Test that iterating multiple times yields consistent results."""
        name = "consistent.txt"
        content = base64.b64encode(b"data").decode('utf-8')

        attachment = Attachment(name=name, content=content)

        # Iterate multiple times
        iterations = [list(attachment) for _ in range(3)]

        # All iterations should be identical
        self.assertTrue(all(it == iterations[0] for it in iterations))
