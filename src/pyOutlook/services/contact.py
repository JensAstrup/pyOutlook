from pyOutlook.core.contact import Contact
from typing import TYPE_CHECKING

import requests

from pyOutlook.internal.utils import check_response

if TYPE_CHECKING:
    from pyOutlook.core.main import OutlookAccount

__all__ = ['ContactService']


class ContactService:
    '''Service class for creating Contact instances from API responses.
    
    This service acts as a factory, handling retrieval and instantiation of
    Contact objects. All operations on individual contacts are instance methods
    on the Contact class itself.
    '''
    
    account: 'OutlookAccount'

    def __init__(self, account: 'OutlookAccount'):
        self.account = account

    def get_overrides(self) -> list[Contact | None]:
        '''Retrieves contact overrides for focused inbox.
        
        Returns:
            List of Contact instances with focused status
        '''
        endpoint = 'https://graph.microsoft.com/v1.0/me/inferenceClassification/overrides'
        r = requests.get(endpoint, headers=self.account._headers, timeout=10)
        
        check_response(r)
        return self._json_to_contacts(r.json())
    
    def _json_to_contact(self, json_value: dict) -> Contact | None:
        '''Factory method: Converts JSON to a Contact instance.
        
        Args:
            json_value: JSON object representing a contact
            
        Returns:
            Contact instance or None if invalid data
        '''
        
        contact = json_value.get('emailAddress', None)
        # The API returns this information in a different format if it's related to Focused inbox overrides
        contact_override = json_value.get('senderEmailAddress', None)
        
        if contact is not None:
            email = contact.get('address', None)
            name = contact.get('name', None)
            return Contact(email, name)
        
        # This contains override information
        elif contact_override is not None:
            # Whether they are 'Focused' or 'Other'
            classification = json_value.get('classifyAs', 'Other')
            focused = True if classification == 'Focused' else False
            
            email = contact_override.get('address', None)
            name = contact_override.get('name', None)
            
            return Contact(email, name, focused=focused)
        
        return None
    
    def _json_to_contacts(self, json_value: dict) -> list[Contact | None]:
        '''Converts JSON array to list of Contact instances.
        
        Args:
            json_value: JSON response, either a dict with 'value' key or a list
            
        Returns:
            List of Contact instances
        '''
        # Sometimes, multiple contacts will be provided behind a dictionary with 'value' as the key
        value = json_value['value']
        
        return [self._json_to_contact(contact) for contact in value]
