from typing import Any, Iterator
from base64 import b64decode

from datetime import datetime

__all__ = ['Attachment']


class Attachment(object):
    """Represents a file attachment on an email message.

    Attachments can be created for sending with new messages or retrieved
    from existing messages via the API.

    :param name: The filename of the attachment.
    :type name: str
    :param content: The base64-encoded content of the attachment.
    :type content: str
    :param outlook_id: The content ID assigned by Outlook (for retrieved attachments).
    :type outlook_id: str or None
    :param size: The size in bytes (for retrieved attachments).
    :type size: int or None
    :param last_modified: When the attachment was last modified.
    :type last_modified: datetime or None
    :param content_type: The MIME type of the attachment (e.g., ``'application/pdf'``).
    :type content_type: str or None

    :ivar name: The filename.
    :ivar bytes: The decoded binary content of the attachment.
    :vartype bytes: bytes
    :ivar outlook_id: The Outlook-assigned content ID.
    :ivar size: Size in bytes.
    :ivar last_modified: Last modification timestamp.
    :vartype last_modified: datetime
    :ivar content_type: MIME type.

    Example::

        # Creating an attachment for sending
        import base64
        with open('document.pdf', 'rb') as f:
            content = base64.b64encode(f.read()).decode('utf-8')
        attachment = Attachment('document.pdf', content, content_type='application/pdf')

        # Accessing content from a retrieved attachment
        with open('downloaded.pdf', 'wb') as f:
            f.write(attachment.bytes)
    """

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
        """Allows ``dict(attachment)`` to return an API-formatted dictionary.

        Used for uploading attachments to the Microsoft Graph API. Returns
        the fields required for the fileAttachment resource type.

        :yields: Tuples of (key, value) for dictionary construction.
        :rtype: Iterator[tuple[str, Any]]

        Example::

            payload = dict(attachment)
            # {'@odata.type': '#microsoft.graph.fileAttachment', 'name': '...', ...}
        """
        yield '@odata.type', '#microsoft.graph.fileAttachment'
        yield 'name', self.name
        yield 'contentBytes', self._content
        yield 'contentType', self.content_type
