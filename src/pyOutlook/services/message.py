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


class MessageService:
    '''Service class for creating Message instances from API responses.
    
    This service acts as a factory, handling retrieval and instantiation of
    Message objects. All operations on individual messages are instance methods
    on the Message class itself.
    '''
    account: 'OutlookAccount'

    def __init__(self, account: 'OutlookAccount'):
        self.account = account
    
    def get(self, message_id: str) -> 'Message':
        '''Retrieves a single message from the API.
        
        Args:
            account: OutlookAccount instance
            message_id: The ID of the message to retrieve
            
        Returns:
            Message instance
        '''
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{message_id}'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        check_response(r)
        return self._json_to_message(r.json())
    
    def all(self, page: int = 0) -> list['Message']:
        '''Retrieves multiple messages from the API.
        
        Args:
            page: Integer representing the 'page' of results to fetch
            
        Returns:
            List of Message instances
        '''
        endpoint = 'https://graph.microsoft.com/v1.0/me/messages'
        if page > 0:
            endpoint = f"{endpoint}/?%24skip={page}0"
        
        log.debug(f'Getting messages from endpoint: {endpoint} with Headers: {self.account._headers}')
        
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        check_response(r)
        
        return self._json_to_messages(r.json())
    
    def from_folder(self, folder_name: str) -> list['Message']:
        '''Retrieves messages from a specific folder.
        
        Args:
            folder_name: Name of the folder
            
        Returns:
            List of Message instances
        '''
        endpoint = f'https://graph.microsoft.com/v1.0/me/mailFolders/{folder_name}/messages'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        check_response(r)
        return self._json_to_messages(r.json())
    
    def _json_to_messages(self, json_value: dict) -> list['Message']:
        '''Converts JSON array to list of Message instances.
        
        Args:
            json_value: JSON response containing 'value' array
            
        Returns:
            List of Message instances
        '''
        return [self._json_to_message(message) for message in json_value['value']]
    
    def _json_to_message(self, api_json: dict) -> 'Message':
        '''Factory method: Converts JSON to a Message instance.
        
        Args:
            api_json: JSON object representing a message
            
        Returns:
            Message instance
        '''
        # Import here to avoid circular dependency
        from pyOutlook.core.message import Message

        uid = api_json['id']
        subject = api_json.get('subject', '')
        
        sender = api_json.get('sender', {})
        sender = Contact(sender['emailAddress']['address'])
        
        body = api_json.get('body', {}).get('content', '')
        body_preview = api_json.get('bodyPreview', '')
        
        to_recipients = api_json.get('toRecipients', [])
        to_recipients = [Contact(recipient['emailAddress']['address']) for recipient in to_recipients]
        # Filter out None values to match Message.__init__ type signature
        to_recipients = [contact for contact in (to_recipients or []) if contact is not None]
        
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
            message_id=uid, 
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

    def send(self, subject: str, body: str, to: list[Contact], cc: list[Contact] | None = None, 
             bcc: list[Contact] | None = None, attachments: list['Attachment'] | None = None) -> None:
        '''Sends a message.
        
        Args:
            subject: The subject of the message
            body: The body of the message
            to: The list of recipients
            cc: The list of CC recipients
            bcc: The list of BCC recipients
        '''
        payload: dict[str, object] = {
            'subject': subject,
            'body': {
                'contentType': 'HTML',
                'content': body
            },
            'toRecipients': [contact.api_representation() for contact in to]
        }
        if cc:
            payload['ccRecipients'] = [contact.api_representation() for contact in cc]
        if bcc:
            payload['bccRecipients'] = [contact.api_representation() for contact in bcc]
        if attachments:
            payload['attachments'] = [dict(attachment) for attachment in attachments]
        r = requests.post('https://graph.microsoft.com/v1.0/me/sendMail', 
                          headers=self.account._headers, 
                          data=json.dumps(payload), timeout=10)
        check_response(r)