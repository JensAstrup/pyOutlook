import base64
import logging
import json

from datetime import datetime
from typing import TYPE_CHECKING

import requests

from pyOutlook.core.attachment import Attachment
from pyOutlook.core.contact import Contact
from pyOutlook.internal.utils import get_valid_filename, check_response

if TYPE_CHECKING:
    from pyOutlook.core.folder import Folder

log = logging.getLogger('pyOutlook')

__all__ = ['Message']


class Message:
    """Message model with instance methods for operations.

    This class stores message data and provides instance methods for all
    operations that can be performed on a single message.

    :param account: The OutlookAccount instance for API authentication.
    :type account: OutlookAccount
    :param body: The body content of the email, including HTML formatting.
    :type body: str
    :param subject: The subject of the email.
    :type subject: str
    :param to_recipients: List of recipients for the email.
    :type to_recipients: list[Contact] or None
    :param sender: The Contact who sent this email.
    :type sender: Contact or None
    :param cc: List of Contacts in the CC field.
    :type cc: list[Contact] or None
    :param bcc: List of Contacts in the BCC field.
    :type bcc: list[Contact] or None
    :param message_id: A string provided by Outlook identifying this specific email.
    :type message_id: str or None

    :ivar account: The associated OutlookAccount.
    :ivar message_id: The Outlook message ID.
    :ivar subject: The email subject.
    :ivar body: The email body content with HTML formatting.
    :ivar body_preview: The first 255 characters of the body.
    :ivar sender: The Contact who sent this email.
    :vartype sender: Contact
    :ivar to: List of recipient Contacts.
    :vartype to: list[Contact]
    :ivar cc: List of CC recipient Contacts.
    :vartype cc: list[Contact]
    :ivar bcc: List of BCC recipient Contacts.
    :vartype bcc: list[Contact]
    :ivar is_draft: Whether the email is a draft.
    :ivar is_read: Whether the email has been read.
    :ivar importance: The importance level (use ``IMPORTANCE_LOW``, ``IMPORTANCE_NORMAL``, ``IMPORTANCE_HIGH``).
    :ivar categories: List of category names.
    :vartype categories: list[str]
    :ivar focused: Whether the message is in the focused inbox.
    :ivar time_created: When the email was created.
    :vartype time_created: datetime
    :ivar time_sent: When the email was sent.
    :vartype time_sent: datetime
    :ivar parent_folder_id: The ID of the folder containing this message.

    :cvar IMPORTANCE_LOW: Low importance level (0).
    :cvar IMPORTANCE_NORMAL: Normal importance level (1).
    :cvar IMPORTANCE_HIGH: High importance level (2).

    Example::

        # Create and send a new message
        message = Message(account, body='<p>Hello!</p>', subject='Greetings',
                         to_recipients=[Contact('user@example.com')])
        message.send()

        # Work with retrieved messages
        for msg in account.inbox():
            print(msg.subject)
            msg.is_read = True  # Mark as read
    """
    
    IMPORTANCE_LOW = 0
    IMPORTANCE_NORMAL = 1
    IMPORTANCE_HIGH = 2
    
    def __init__(self, account, body: str = '', subject: str = '', to_recipients: list[Contact] | None = None, 
                 sender: Contact | None = None, cc: list[Contact] | None = None, bcc: list[Contact] | None = None, message_id: str | None = None, **kwargs):
        self.account = account
        self.message_id = message_id
        self.subject = subject
        self.body = body
        self.body_preview = kwargs.get('body_preview', '')
        self.sender = sender
        self.to = to_recipients or []
        self.cc = cc or []
        self.bcc = bcc or []
        self._is_read = kwargs.get('is_read', False)
        self.is_draft = kwargs.get('is_draft', False)
        self.importance = kwargs.get('importance', self.IMPORTANCE_NORMAL)
        self.categories = kwargs.get('categories', [])
        self.focused = kwargs.get('focused', False)
        self.time_created = kwargs.get('time_created')
        self.time_sent = kwargs.get('time_sent')
        self.parent_folder_id = kwargs.get('parent_folder_id')
        
        # Internal state
        self._attachments = []
        self._has_attachments = kwargs.get('has_attachments', False)
        self._parent_folder_cache = None
    
    def __str__(self):
        return self.subject
    
    def __repr__(self):
        return f'Message(subject={self.subject!r}, message_id={self.message_id!r})'
    
    @property
    def headers(self) -> dict:
        """HTTP headers for API requests.

        :returns: Dictionary with Authorization and Content-Type headers.
        :rtype: dict
        """
        return {
            'Authorization': f'Bearer {self.account.access_token}',
            'Content-Type': 'application/json'
        }

    @property
    def is_read(self) -> bool:
        """Get the read status of this message.

        :returns: ``True`` if the message has been read, ``False`` otherwise.
        :rtype: bool
        """
        return self._is_read

    @is_read.setter
    def is_read(self, value: bool):
        """Set the read status of this message.

        Setting this property will call :meth:`set_read_status` to update
        the status via the API.

        :param value: ``True`` to mark as read, ``False`` for unread.
        :type value: bool
        """
        self.set_read_status(value)

    @property
    def attachments(self) -> list[Attachment]:
        """Get attachments, lazy-loading from API if needed.

        Attachments are fetched from the API on first access and cached
        for subsequent calls.

        :returns: List of Attachment objects.
        :rtype: list[Attachment]
        """
        if not self._has_attachments:
            return []
        
        if self._attachments:
            return self._attachments
        
        # Lazy load from API
        if self.message_id:
            from pyOutlook.services.message import MessageService
            endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/attachments'
            r = requests.get(endpoint, headers=self.headers, timeout=10)
            
            if check_response(r):
                data = r.json()
                self._attachments = []
                for attachment in data['value']:
                    last_modified_str = attachment['lastModifiedDateTime']
                    # Handle 'Z' suffix for UTC timezone (fromisoformat doesn't support 'Z')
                    if last_modified_str and last_modified_str.endswith('Z'):
                        last_modified_str = last_modified_str[:-1] + '+00:00'
                    last_modified = datetime.fromisoformat(last_modified_str)
                    
                    self._attachments.append(Attachment(
                        name=attachment['name'], 
                        content=attachment['contentBytes'], 
                        outlook_id=attachment['contentId'],
                        size=attachment['size'],
                        last_modified=last_modified,
                        content_type=attachment['contentType']
                    ))
        
        return self._attachments
    
    @property
    def parent_folder(self) -> 'Folder':
        """Returns the Folder this message is in.

        Lazily loads the folder from the API using the ``parent_folder_id``.
        The folder is cached after the first retrieval.

        :returns: The folder containing this message, or ``None`` if not available.
        :rtype: Folder or None

        .. warning::
            This property currently calls a non-existent method and will raise
            an AttributeError. Use ``account.folders.get(message.parent_folder_id)``
            instead until this is fixed.
        """
        if self._parent_folder_cache is None and self.parent_folder_id:
            self._parent_folder_cache = self.account.get_folder_by_id(self.parent_folder_id)

        return self._parent_folder_cache
    
    def send(self, content_type: str = 'HTML') -> None:
        """Sends this message.

        :param content_type: The content type of the body, either ``'HTML'`` or ``'Text'``.
            Defaults to ``'HTML'``.
        :type content_type: str

        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.

        .. warning::
            This method currently uses the legacy Outlook REST API endpoint.
            For Microsoft Graph API support, use :meth:`MessageService.send` via
            ``account.messages.send()`` instead.
        """
        payload = self._create_api_payload(content_type)
        endpoint = 'https://outlook.office.com/api/v1.0/me/sendmail'

        r = requests.post(endpoint, headers=self.headers, data=json.dumps(payload))
        check_response(r)
    
    def reply(self, comment: str) -> None:
        """Reply to this message.

        Sends a reply to the sender of this message.

        :param comment: The reply text. HTML formatting is supported.
        :type comment: str

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if not self.message_id:
            raise ValueError('Cannot reply to a message without message_id')

        payload = json.dumps({'Comment': comment})
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/reply'

        r = requests.post(endpoint, headers=self.headers, data=payload)
        check_response(r)

    def reply_all(self, comment: str) -> None:
        """Reply to all recipients of this message.

        Sends a reply to the sender and all recipients (To and CC) of this message.

        :param comment: The reply text. HTML formatting is supported.
        :type comment: str

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if not self.message_id:
            raise ValueError('Cannot reply to a message without message_id')

        payload = json.dumps({'Comment': comment})
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/replyall'

        r = requests.post(endpoint, headers=self.headers, data=payload)
        check_response(r)

    def forward(self, to_recipients: list, forward_comment: str | None = None) -> None:
        """Forward this message to recipients.

        :param to_recipients: List of recipients. Can be Contact instances or email
            address strings.
        :type to_recipients: list[Contact] or list[str]
        :param forward_comment: Optional comment to include with the forwarded message.
        :type forward_comment: str or None

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.

        .. warning::
            This method calls ``api_representation()`` on Contact objects, which
            is currently not implemented. Use ``dict(contact)`` format instead
            until this is fixed.
        """
        if not self.message_id:
            raise ValueError('Cannot forward a message without message_id')

        payload = {}

        if forward_comment is not None:
            payload['Comment'] = forward_comment

        # Convert strings to Contacts if needed
        if any(isinstance(recipient, str) for recipient in to_recipients):
            to_recipients = [Contact(email=email) for email in to_recipients]

        # Convert to API format
        to_recipients = [contact.api_representation() for contact in to_recipients]
        payload['ToRecipients'] = to_recipients

        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/forward'

        r = requests.post(endpoint, headers=self.headers, data=json.dumps(payload))
        check_response(r)

    def delete(self) -> None:
        """Delete this message.

        Permanently removes this message from the mailbox.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if not self.message_id:
            raise ValueError('Cannot delete a message without message_id')

        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}'

        r = requests.delete(endpoint, headers=self.headers)
        check_response(r)
    
    def move_to(self, destination) -> None:
        """Move this message to a destination folder.

        The message ID may change after moving.

        :param destination: The target folder. Can be a Folder instance, folder ID
            string, or well-known folder name (e.g., ``'Inbox'``, ``'DeletedItems'``).
        :type destination: Folder or str

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if not self.message_id:
            raise ValueError('Cannot move a message without message_id')

        from pyOutlook.core.folder import Folder

        if isinstance(destination, Folder):
            destination_id = destination.id
        else:
            destination_id = destination

        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/move'
        payload = json.dumps({'DestinationId': destination_id})

        r = requests.post(endpoint, headers=self.headers, data=payload)
        check_response(r)

        # Update message_id if changed
        data = r.json()
        self.message_id = data.get('Id', self.message_id)

    def move_to_inbox(self) -> None:
        """Move this message to the Inbox folder.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.move_to('Inbox')

    def move_to_deleted(self) -> None:
        """Move this message to the Deleted Items folder.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.move_to('DeletedItems')

    def move_to_drafts(self) -> None:
        """Move this message to the Drafts folder.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.move_to('Drafts')

    def copy_to(self, destination) -> None:
        """Copy this message to a destination folder.

        Creates a copy of this message in the target folder.

        :param destination: The target folder. Can be a Folder instance, folder ID
            string, or well-known folder name (e.g., ``'Inbox'``, ``'DeletedItems'``).
        :type destination: Folder or str

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if not self.message_id:
            raise ValueError('Cannot copy a message without message_id')

        from pyOutlook.core.folder import Folder

        if isinstance(destination, Folder):
            destination_id = destination.id
        else:
            destination_id = destination

        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/copy'
        payload = json.dumps({'DestinationId': destination_id})

        r = requests.post(endpoint, headers=self.headers, data=payload)
        check_response(r)

    def copy_to_inbox(self) -> None:
        """Copy this message to the Inbox folder.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.copy_to('Inbox')

    def copy_to_deleted(self) -> None:
        """Copy this message to the Deleted Items folder.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.copy_to('DeletedItems')

    def copy_to_drafts(self) -> None:
        """Copy this message to the Drafts folder.

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.copy_to('Drafts')
    
    def set_read_status(self, is_read: bool) -> None:
        """Set the read status of this message.

        If the message has a ``message_id``, the status is updated via the API.

        :param is_read: ``True`` to mark as read, ``False`` for unread.
        :type is_read: bool

        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if self.message_id:
            endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}'
            payload = json.dumps({'IsRead': is_read})

            r = requests.patch(endpoint, headers=self.headers, data=payload)
            check_response(r)

        self._is_read = is_read

    def set_focused(self, is_focused: bool) -> None:
        """Set the focused status of this message.

        Moves this message to the Focused or Other section of the inbox.

        :param is_focused: ``True`` for Focused inbox, ``False`` for Other.
        :type is_focused: bool

        :raises ValueError: If the message has no ``message_id``.
        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        if not self.message_id:
            raise ValueError('Cannot set focused status on a message without message_id')

        endpoint = f"https://graph.microsoft.com/v1.0/me/messages('{self.message_id}')"
        data = {'InferenceClassification': 'Focused' if is_focused else 'Other'}

        r = requests.patch(endpoint, data=json.dumps(data), headers=self.headers)
        check_response(r)

        self.focused = is_focused

    def add_category(self, category_name: str) -> None:
        """Add a category to this message.

        Categories are labels that can be used to organize messages.
        The category is added locally and, if the message has been saved,
        updated via the API.

        :param category_name: Name of the category to add.
        :type category_name: str

        :raises RequestError: If the API request fails.
        :raises AuthError: If authentication fails.
        """
        self.categories.append(category_name)

        if self.message_id:
            endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}'
            payload = json.dumps({'Categories': self.categories})

            r = requests.patch(endpoint, headers=self.headers, data=payload)
            check_response(r)

    def attach(self, file_bytes, file_name: str) -> None:
        """Add an attachment to this message.

        The attachment is added locally for inclusion when the message is sent.

        :param file_bytes: The raw bytes of the file to attach, or a string
            that will be encoded to bytes.
        :type file_bytes: bytes or str
        :param file_name: The filename for the attachment. Special characters
            will be sanitized.
        :type file_name: str
        """
        try:
            file_bytes = base64.b64encode(file_bytes)
        except TypeError:
            file_bytes = base64.b64encode(bytes(file_bytes, 'utf-8'))

        self._attachments.append(
            Attachment(get_valid_filename(file_name), file_bytes.decode('utf-8'))
        )
        self._has_attachments = True

    def _create_api_payload(self, content_type: str) -> dict:
        """Create the JSON payload for sending this message.

        Builds the message payload in the format expected by the Microsoft API.

        :param content_type: Either ``'HTML'`` or ``'Text'``.
        :type content_type: str

        :returns: Dictionary formatted for the Outlook API sendMail endpoint.
        :rtype: dict

        .. warning::
            This method calls ``api_representation()`` on Contact and Attachment
            objects, which is currently not implemented. The code may fail until
            these methods are added.
        """
        payload = {
            'Subject': self.subject,
            'Body': {
                'ContentType': content_type,
                'Content': self.body
            }
        }
        
        if self.sender is not None:
            payload['From'] = self.sender.api_representation()
        
        # Handle To recipients
        to = self.to
        if any(isinstance(item, str) for item in to):
            to = [Contact(email=email) for email in to]
        payload['ToRecipients'] = [contact.api_representation() for contact in to]
        
        # Handle CC recipients
        if self.cc:
            cc = self.cc
            if any(isinstance(email, str) for email in cc):
                cc = [Contact(email=email) for email in cc]
            payload['CcRecipients'] = [contact.api_representation() for contact in cc]
        
        # Handle BCC recipients
        if self.bcc:
            bcc = self.bcc
            if any(isinstance(email, str) for email in bcc):
                bcc = [Contact(email=email) for email in bcc]
            payload['BccRecipients'] = [contact.api_representation() for contact in bcc]
        
        # Handle attachments
        if self._attachments:
            payload['Attachments'] = [att.api_representation() for att in self._attachments]
        
        payload['Importance'] = str(self.importance)
        
        return {'Message': payload}
    
    # Backward compatibility: class methods that delegate to MessageService
    @classmethod
    def _json_to_messages(cls, account, json_value: dict) -> list['Message']:
        """Converts JSON array to list of Message instances.

        .. deprecated::
            Use :meth:`MessageService._json_to_messages` directly instead.
            This method exists for backward compatibility.

        :param account: The OutlookAccount for the messages.
        :type account: OutlookAccount
        :param json_value: JSON response containing ``'value'`` array.
        :type json_value: dict

        :returns: List of Message instances.
        :rtype: list[Message]
        """
        from pyOutlook.services.message import MessageService
        return MessageService._json_to_messages(account, json_value)

    @classmethod
    def _json_to_message(cls, account, api_json: dict) -> 'Message':
        """Converts JSON to a Message instance.

        .. deprecated::
            Use :meth:`MessageService._json_to_message` directly instead.
            This method exists for backward compatibility.

        :param account: The OutlookAccount for the message.
        :type account: OutlookAccount
        :param api_json: JSON object representing a message.
        :type api_json: dict

        :returns: Message instance.
        :rtype: Message
        """
        from pyOutlook.services.message import MessageService
        return MessageService._json_to_message(account, api_json)
