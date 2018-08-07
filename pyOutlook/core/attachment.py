from base64 import b64decode

from datetime import datetime
from dateutil import parser

__all__ = ['Attachment']


class Attachment(object):
    def __init__(self, name, content, outlook_id=None, size=None, last_modified=None, content_type=None):
        # type: (str, str, str, int, datetime, str) -> None
        self.name = name

        self._content = content
        self.bytes = b64decode(content)

        self.outlook_id = outlook_id
        self.size = size
        self.last_modified = last_modified
        self.content_type = content_type

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    @classmethod
    def json_to_attachment(cls, account, api_json):
        outlook_id = api_json.get('Id')
        name = api_json.get('Name')

        content = api_json.get('ContentBytes', None)
        size = api_json.get('Size', None)
        content_type = api_json.get('ContentType', None)

        last_modified = api_json.get('LastModifiedDateTime', None)
        if last_modified is not None:
            parser.parse(last_modified, ignoretz=True)

        return Attachment(name, outlook_id=outlook_id, content=content, size=size,
                          content_type=content_type, last_modified=last_modified)

    @classmethod
    def json_to_attachments(cls, account, api_json):
        return [cls.json_to_attachment(account, value) for value in api_json['value']]

    def api_representation(self):
        """ Used for uploading attachments - less information is required than what we receive from the API """
        return {'@odata.type': '#Microsoft.OutlookServices.FileAttachment', 'Name': self.name,
                'ContentBytes': self._content}
