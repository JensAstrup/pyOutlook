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
    '''Message model with instance methods for operations.
    
    This class stores message data and provides instance methods for all
    operations that can be performed on a single message.
    
    Attributes:
        account: OutlookAccount instance
        message_id: A string provided by Outlook identifying this specific email
        body: The body content of the email, including HTML formatting
        body_preview: The first 255 characters of the body
        subject: The subject of the email
        sender: The Contact who sent this email
        to: A list of Contacts
        cc: A list of Contacts in the CC field
        bcc: A list of Contacts in the BCC field
        is_draft: Whether or not the email is a draft
        is_read: Whether the email has been read
        importance: The importance level (0=low, 1=normal, 2=high)
        categories: A list of category names
        focused: Whether the message is in the focused inbox
        time_created: A datetime representing when the email was created
        time_sent: A datetime representing when the email was sent
        parent_folder_id: The ID of the folder containing this message
    '''
    
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
    def headers(self):
        '''HTTP headers for API requests.'''
        return {
            'Authorization': f'Bearer {self.account.access_token}',
            'Content-Type': 'application/json'
        }
    
    @property
    def is_read(self):
        '''Get the read status of this message.'''
        return self._is_read
    
    @is_read.setter
    def is_read(self, value: bool):
        '''Set the read status of this message.'''
        self.set_read_status(value)
    
    @property
    def attachments(self):
        '''Get attachments, lazy-loading from API if needed.'''
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
    def parent_folder(self):
        '''Returns the Folder this message is in.
        
        Returns: Folder instance
        '''
        if self._parent_folder_cache is None and self.parent_folder_id:
            self._parent_folder_cache = self.account.get_folder_by_id(self.parent_folder_id)
        
        return self._parent_folder_cache
    
    def send(self, content_type: str = 'HTML') -> None:
        '''Sends this message.
        
        Args:
            content_type: Either 'HTML' or 'Text', defaults to HTML
        '''
        payload = self._create_api_payload(content_type)
        endpoint = 'https://outlook.office.com/api/v1.0/me/sendmail'
        
        r = requests.post(endpoint, headers=self.headers, data=json.dumps(payload))
        check_response(r)
    
    def reply(self, comment: str) -> None:
        '''Reply to this message.
        
        Args:
            comment: The reply text (HTML supported)
        '''
        if not self.message_id:
            raise ValueError('Cannot reply to a message without message_id')
        
        payload = json.dumps({'Comment': comment})
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/reply'
        
        r = requests.post(endpoint, headers=self.headers, data=payload)
        check_response(r)
    
    def reply_all(self, comment: str) -> None:
        '''Reply to all recipients of this message.
        
        Args:
            comment: The reply text (HTML supported)
        '''
        if not self.message_id:
            raise ValueError('Cannot reply to a message without message_id')
        
        payload = json.dumps({'Comment': comment})
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}/replyall'
        
        r = requests.post(endpoint, headers=self.headers, data=payload)
        check_response(r)
    
    def forward(self, to_recipients: list, forward_comment: str | None = None) -> None:
        '''Forward this message to recipients.
        
        Args:
            to_recipients: List of Contact instances or email strings
            forward_comment: Optional comment to include
        '''
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
        '''Delete this message.'''
        if not self.message_id:
            raise ValueError('Cannot delete a message without message_id')
        
        endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}'
        
        r = requests.delete(endpoint, headers=self.headers)
        check_response(r)
    
    def move_to(self, destination) -> None:
        '''Move this message to a destination folder.
        
        Args:
            destination: Folder instance or folder ID string
        '''
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
        '''Move this message to the Inbox folder.'''
        self.move_to('Inbox')
    
    def move_to_deleted(self) -> None:
        '''Move this message to the Deleted Items folder.'''
        self.move_to('DeletedItems')
    
    def move_to_drafts(self) -> None:
        '''Move this message to the Drafts folder.'''
        self.move_to('Drafts')
    
    def copy_to(self, destination) -> None:
        '''Copy this message to a destination folder.
        
        Args:
            destination: Folder instance or folder ID string
        '''
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
        '''Copy this message to the Inbox folder.'''
        self.copy_to('Inbox')
    
    def copy_to_deleted(self) -> None:
        '''Copy this message to the Deleted Items folder.'''
        self.copy_to('DeletedItems')
    
    def copy_to_drafts(self) -> None:
        '''Copy this message to the Drafts folder.'''
        self.copy_to('Drafts')
    
    def set_read_status(self, is_read: bool) -> None:
        '''Set the read status of this message.
        
        Args:
            is_read: True to mark as read, False for unread
        '''
        if self.message_id:
            endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}'
            payload = json.dumps({'IsRead': is_read})
            
            r = requests.patch(endpoint, headers=self.headers, data=payload)
            check_response(r)
        
        self._is_read = is_read
    
    def set_focused(self, is_focused: bool) -> None:
        '''Set the focused status of this message.
        
        Args:
            is_focused: True for Focused inbox, False for Other
        '''
        if not self.message_id:
            raise ValueError('Cannot set focused status on a message without message_id')
        
        endpoint = f"https://graph.microsoft.com/v1.0/me/messages('{self.message_id}')"
        data = {'InferenceClassification': 'Focused' if is_focused else 'Other'}
        
        r = requests.patch(endpoint, data=json.dumps(data), headers=self.headers)
        check_response(r)
        
        self.focused = is_focused
    
    def add_category(self, category_name: str) -> None:
        '''Add a category to this message.
        
        Args:
            category_name: Name of the category to add
        '''
        self.categories.append(category_name)
        
        if self.message_id:
            endpoint = f'https://graph.microsoft.com/v1.0/me/messages/{self.message_id}'
            payload = json.dumps({'Categories': self.categories})
            
            r = requests.patch(endpoint, headers=self.headers, data=payload)
            check_response(r)
    
    def attach(self, file_bytes, file_name: str) -> None:
        '''Add an attachment to this message.
        
        Args:
            file_bytes: The bytes of the file to attach
            file_name: The name of the file
        '''
        try:
            file_bytes = base64.b64encode(file_bytes)
        except TypeError:
            file_bytes = base64.b64encode(bytes(file_bytes, 'utf-8'))
        
        self._attachments.append(
            Attachment(get_valid_filename(file_name), file_bytes.decode('utf-8'))
        )
        self._has_attachments = True
    
    def _create_api_payload(self, content_type: str) -> dict:
        '''Create the JSON payload for sending this message.
        
        Args:
            content_type: Either 'HTML' or 'Text'
            
        Returns:
            Dictionary formatted for the Outlook API
        '''
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
    def _json_to_messages(cls, account, json_value: dict):
        '''Converts JSON array to list of Message instances.
        
        Delegates to MessageService for backward compatibility.
        '''
        from pyOutlook.services.message import MessageService
        return MessageService._json_to_messages(account, json_value)
    
    @classmethod
    def _json_to_message(cls, account, api_json: dict):
        '''Converts JSON to a Message instance.
        
        Delegates to MessageService for backward compatibility.
        '''
        from pyOutlook.services.message import MessageService
        return MessageService._json_to_message(account, api_json)
