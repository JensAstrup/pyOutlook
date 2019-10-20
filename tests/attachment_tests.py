from base64 import b64encode

from unittest import TestCase
try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import Mock, patch
from pyOutlook import *


class AttachmentTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.content_1 = b64encode(b'1234')
        cls.content_2 = b64encode(b'12345')
        cls.attachment = Attachment('Attachment 1', cls.content_1, 'OutlookID')
        cls.no_id_attachment = Attachment('Attachment 1', cls.content_1)

    def test__str__(self):
        self.assertEqual(str(self.attachment), 'Attachment 1')

    def test__repr__(self):
        self.assertEqual(repr(self.attachment), 'Attachment 1')

    def test__eq__other_equal_id(self):
        other = Attachment('Attachment 1', self.content_1, 'OutlookID')
        self.assertEqual(self.attachment, other)

    def test__eq__other_unequal_id(self):
        other = Attachment('Attachment 1', self.content_1, 'OtherOutlookID')
        self.assertNotEqual(self.attachment, other)

    def test__eq__other_no_id(self):
        other = Attachment('Attachment 1', self.content_1)
        self.assertNotEqual(self.attachment, other)

    def test__eq__other_equal_content(self):
        other = Attachment('Attachment 1', self.content_1)
        self.assertEqual(self.no_id_attachment, other)

    def test__eq__other_unequal_content(self):
        other = Attachment('Attachment 1', self.content_2)
        self.assertNotEqual(self.no_id_attachment, other)

    def test__hash__with_id(self):
        expected = hash('OutlookID')
        self.assertEqual(hash(self.attachment), expected)

    def test__hash__without_id(self):
        expected = hash(self.content_1)
        self.assertEqual(hash(self.no_id_attachment), expected)
