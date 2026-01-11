from pyOutlook.core.attachment import Attachment
import json
import logging
from typing import TYPE_CHECKING

from dateutil import parser
import requests

from pyOutlook.core.message import Message
from pyOutlook.core.contact import Contact
from pyOutlook.internal.utils import check_response

if TYPE_CHECKING:
    from pyOutlook.core.main import OutlookAccount

log = logging.getLogger('pyOutlook')

__all__ = ['MessageService']


def _recipient_to_dict(recipient: Contact | str) -> dict:
    """Convert a recipient to API format.

    :param recipient: Either a Contact object or a string email address.
    :type recipient: Contact or str

    :returns: Dictionary in the format expected by the Microsoft Graph API.
    :rtype: dict
    """
    if isinstance(recipient, str):
        return {'EmailAddress': {'Name': None, 'Address': recipient}}
    return dict(recipient)


class MessageService:
    """Service class for creating Message instances from API responses.

    This service acts as a factory, handling retrieval and instantiation of
    Message objects. All operations on individual messages are instance methods
    on the Message class itself.

    :param account: The OutlookAccount for API authentication.
    :type account: OutlookAccount

    :ivar account: The associated OutlookAccount.
    """
    account: 'OutlookAccount'

    def __init__(self, account: 'OutlookAccount'):
        self.account = account

    def get(self, message_id: str) -> 'Message':
        """Retrieve a single message from the API.

        :param message_id: The ID of the message to retrieve.
        :type message_id: str

        :returns: The retrieved message.
        :rtype: Message

        :raises AuthError: If authentication fails.
        :raises RequestError: If the message ID is invalid or the request fails.
        """
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        check_response(r)
        return self._json_to_message(r.json())

    def all(self, page: int = 0) -> list['Message']:
        """Retrieve multiple messages from the API.

        :param page: Page number for pagination (0-indexed). Each page contains
            10 messages by default.
        :type page: int

        :returns: List of messages from the specified page.
        :rtype: list[Message]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.
        """
        endpoint = 'https://graph.microsoft.com/v1.0/me/messages'
        if page > 0:
            endpoint = f"{endpoint}/?%24skip={page}0"

        log.debug(f'Getting messages from endpoint: {endpoint} with Headers: {self.account._headers}')

        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        check_response(r)

        return self._json_to_messages(r.json())

    def from_folder(self, folder_name: str) -> list['Message']:
        """Retrieve messages from a specific folder.

        :param folder_name: The name or ID of the folder. Well-known folder names
            include ``'Inbox'``, ``'SentItems'``, ``'DeletedItems'``, ``'Drafts'``.
        :type folder_name: str

        :returns: List of messages from the folder.
        :rtype: list[Message]

        :raises AuthError: If authentication fails.
        :raises RequestError: If the folder is not found or the request fails.
        """
        endpoint = f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_name}/messages'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        check_response(r)
        return self._json_to_messages(r.json())

    def _json_to_messages(self, json_value: dict) -> list['Message']:
        """Convert JSON array to list of Message instances.

        :param json_value: JSON response containing ``'value'`` array.
        :type json_value: dict

        :returns: List of Message instances.
        :rtype: list[Message]
        """
        return [self._json_to_message(message) for message in json_value['value']]

    def _json_to_message(self, api_json: dict) -> 'Message':
        """Factory method: Convert JSON to a Message instance.

        :param api_json: JSON object representing a message.
        :type api_json: dict

        :returns: Message instance.
        :rtype: Message
        """
        # Import here to avoid circular dependency
        from pyOutlook.core.message import Message
        uid = api_json['id']
        subject = api_json.get('subject', '')
        
        sender = api_json.get('sender', {})
        sender = Contact(sender['emailAddress']['address'])
        
        body = api_json.get('body', {}).get('content', '')
        body_preview = api_json.get('bodyPreview', '')
        
        to_recipients = api_json.get('toRecipients', [])
        # Parse recipients, handling malformed data gracefully
        parsed_recipients = []
        for recipient in to_recipients:
            try:
                email_address = recipient.get('emailAddress', {})
                address = email_address.get('address', None)
                if address:
                    parsed_recipients.append(Contact(address))
            except (KeyError, TypeError, AttributeError):
                # Skip malformed recipient data
                continue
        to_recipients = parsed_recipients
        
        is_read = api_json['isRead']
        has_attachments = api_json['hasAttachments']
        
        time_created = api_json.get('createdDateTime', None)
        if time_created is not None:
            time_created = parser.parse(time_created, ignoretz=True)
        
        time_sent = api_json.get('SentDateTime', None)
        if time_sent is not None:
            time_sent = parser.parse(time_sent, ignoretz=True)
        
        parent_folder_id = api_json.get('ParentFolderId', None)
        is_draft = api_json.get('IsDraft', None)
        importance = api_json.get('Importance', Message.IMPORTANCE_NORMAL)
        
        categories = api_json.get('Categories', [])
        
        focused = api_json.get('InferenceClassification', 'Other') == 'Focused'
        
        return Message(
            self.account, 
            body, 
            subject, 
            to_recipients, 
            sender=sender, 
            id=uid, 
            is_read=is_read,
            time_created=time_created, 
            time_sent=time_sent, 
            parent_folder_id=parent_folder_id,
            is_draft=is_draft, 
            importance=importance, 
            body_preview=body_preview,
            categories=categories, 
            has_attachments=has_attachments,
            focused=focused
        )

    def send(self, subject: str, body: str, to: list[Contact | str], cc: list[Contact | str] | None = None,
             bcc: list[Contact | str] | None = None, attachments: list['Attachment'] | None = None) -> None:
        """Send a message.

        Uses the Microsoft Graph API to send a new email message.

        :param subject: The subject line of the message.
        :type subject: str
        :param body: The HTML body content of the message.
        :type body: str
        :param to: List of recipients. Can be Contact objects or email address strings.
        :type to: list[Contact] or list[str]
        :param cc: List of CC recipients. Can be Contact objects or email strings.
        :type cc: list[Contact] or list[str] or None
        :param bcc: List of BCC recipients. Can be Contact objects or email strings.
        :type bcc: list[Contact] or list[str] or None
        :param attachments: List of Attachment objects to include.
        :type attachments: list[Attachment] or None

        :raises AuthError: If authentication fails.
        :raises RequestError: If the API request fails.

        Example::

            account.messages.send(
                subject='Meeting Tomorrow',
                body='<p>Let\\'s meet at 10am.</p>',
                to=['colleague@example.com'],
                cc=[Contact('manager@example.com', name='Manager')]
            )
        """
        payload: dict[str, object] = {
            'subject': subject,
            'body': {
                'contentType': 'HTML',
                'content': body
            },
            'toRecipients': [_recipient_to_dict(recipient) for recipient in to]
        }
        if cc:
            payload['ccRecipients'] = [_recipient_to_dict(recipient) for recipient in cc]
        if bcc:
            payload['bccRecipients'] = [_recipient_to_dict(recipient) for recipient in bcc]
        if attachments:
            payload['attachments'] = [dict(attachment) for attachment in attachments]
        r = requests.post('https://graph.microsoft.com/v1.0/me/sendMail', 
                          headers=self.account._headers, 
                          data=json.dumps({'message': payload}), timeout=10)
        check_response(r)