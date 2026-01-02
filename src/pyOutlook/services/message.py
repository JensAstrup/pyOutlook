import logging

from dateutil import parser
import requests

from pyOutlook.core.attachment import Attachment
from pyOutlook.core.contact import Contact
from pyOutlook.internal.utils import check_response

log = logging.getLogger('pyOutlook')

__all__ = ['MessageService']


class MessageService:
    '''Service class for creating Message instances from API responses.
    
    This service acts as a factory, handling retrieval and instantiation of
    Message objects. All operations on individual messages are instance methods
    on the Message class itself.
    '''
    
    @classmethod
    def get_message(cls, account, message_id: str):
        '''Retrieves a single message from the API.
        
        Args:
            account: OutlookAccount instance
            message_id: The ID of the message to retrieve
            
        Returns:
            Message instance
        '''
        endpoint = f'https://outlook.office.com/api/v2.0/me/messages/{message_id}'
        r = requests.get(endpoint, headers=account._headers)
        check_response(r)
        return cls._json_to_message(account, r.json())
    
    @classmethod
    def get_messages(cls, account, page: int = 0):
        '''Retrieves multiple messages from the API.
        
        Args:
            account: OutlookAccount instance
            page: Integer representing the 'page' of results to fetch
            
        Returns:
            List of Message instances
        '''
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages'
        if page > 0:
            endpoint = endpoint + '/?%24skip=' + str(page) + '0'
        
        log.debug(f'Getting messages from endpoint: {endpoint} with Headers: {account._headers}')
        
        r = requests.get(endpoint, headers=account._headers)
        check_response(r)
        
        return cls._json_to_messages(account, r.json())
    
    @classmethod
    def get_messages_from_folder(cls, account, folder_name: str):
        '''Retrieves messages from a specific folder.
        
        Args:
            account: OutlookAccount instance
            folder_name: Name of the folder
            
        Returns:
            List of Message instances
        '''
        endpoint = f'https://outlook.office.com/api/v2.0/me/MailFolders/{folder_name}/messages'
        r = requests.get(endpoint, headers=account._headers)
        check_response(r)
        return cls._json_to_messages(account, r.json())
    
    @classmethod
    def _json_to_messages(cls, account, json_value: dict):
        '''Converts JSON array to list of Message instances.
        
        Args:
            account: OutlookAccount instance
            json_value: JSON response containing 'value' array
            
        Returns:
            List of Message instances
        '''
        return [cls._json_to_message(account, message) for message in json_value['value']]
    
    @classmethod
    def _json_to_message(cls, account, api_json: dict):
        '''Factory method: Converts JSON to a Message instance.
        
        Args:
            account: OutlookAccount instance
            api_json: JSON object representing a message
            
        Returns:
            Message instance
        '''
        # Import here to avoid circular dependency
        from pyOutlook.core.message import Message
        
        uid = api_json['Id']
        subject = api_json.get('Subject', '')
        
        sender = api_json.get('Sender', {})
        sender = Contact._json_to_contact(sender)
        
        body = api_json.get('Body', {}).get('Content', '')
        body_preview = api_json.get('BodyPreview', '')
        
        to_recipients = api_json.get('ToRecipients', [])
        to_recipients = Contact._json_to_contacts(to_recipients)
        
        is_read = api_json['IsRead']
        has_attachments = api_json['HasAttachments']
        
        time_created = api_json.get('CreatedDateTime', None)
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
            account, 
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
    
    @classmethod
    def _json_to_attachments(cls, account, api_json: dict):
        '''Factory method: Converts JSON array to list of Attachment instances.
        
        Args:
            account: OutlookAccount instance
            api_json: JSON response containing 'value' array
            
        Returns:
            List of Attachment instances
        '''
        return [cls._json_to_attachment(account, value) for value in api_json['value']]
    
    @classmethod
    def _json_to_attachment(cls, account, api_json: dict):
        '''Factory method: Converts JSON to an Attachment instance.
        
        Args:
            account: OutlookAccount instance
            api_json: JSON object representing an attachment
            
        Returns:
            Attachment instance
        '''
        outlook_id = api_json.get('Id')
        name = api_json.get('Name')
        content = api_json.get('ContentBytes', None)
        size = api_json.get('Size', None)
        content_type = api_json.get('ContentType', None)
        
        last_modified = api_json.get('LastModifiedDateTime', None)
        if last_modified is not None:
            last_modified = parser.parse(last_modified, ignoretz=True)
        
        return Attachment(
            name, 
            outlook_id=outlook_id, 
            content=content, 
            size=size,
            content_type=content_type, 
            last_modified=last_modified
        )
