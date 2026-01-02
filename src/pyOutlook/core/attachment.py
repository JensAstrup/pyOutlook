from base64 import b64decode

from datetime import datetime
from dateutil import parser

__all__ = ['Attachment']


class Attachment(object):
    def __init__(self, name: str, content: str, outlook_id: str | None = None, size: int | None = None, last_modified: datetime | None = None, content_type: str | None = None):
        self.name = name
        self._content = content
        self.bytes = b64decode(content)
        self.outlook_id = outlook_id
        self.size = size
        self.last_modified = last_modified
        self.content_type = content_type

    @classmethod
    def json_to_attachment(cls, account, api_json):
        '''Backward compatibility: delegates to MessageService.'''
        from pyOutlook.services.message import MessageService
        return MessageService._json_to_attachment(account, api_json)

    @classmethod
    def json_to_attachments(cls, account, api_json):
        '''Backward compatibility: delegates to MessageService.'''
        from pyOutlook.services.message import MessageService
        return MessageService._json_to_attachments(account, api_json)

    def api_representation(self):
        """ Used for uploading attachments - less information is required than what we receive from the API """
        return {'@odata.type': '#Microsoft.OutlookServices.FileAttachment', 'Name': self.name,
                'ContentBytes': self._content}
