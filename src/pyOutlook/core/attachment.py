from typing import Any, Iterator
from base64 import b64decode

from datetime import datetime

__all__ = ['Attachment']


class Attachment(object):
    def __init__(self, name: str, content: str, outlook_id: str | None = None, 
                size: int | None = None, last_modified: datetime | None = None, 
                content_type: str | None = None):
        self.name = name
        self._content = content
        self.bytes = b64decode(content)
        self.outlook_id = outlook_id
        self.size = size
        self.last_modified = last_modified
        self.content_type = content_type

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        """ Used for uploading attachments - allows dict(attachment) to work.
        Less information is required than what we receive from the API.
        """
        yield '@odata.type', '#microsoft.graph.fileAttachment'
        yield 'name', self.name
        yield 'contentBytes', self._content
        yield 'contentType', self.content_type
