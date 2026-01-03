import requests

from pyOutlook.internal.utils import check_response

__all__ = ['ContactService']


class ContactService:
    '''Service class for creating Contact instances from API responses.
    
    This service acts as a factory, handling retrieval and instantiation of
    Contact objects. All operations on individual contacts are instance methods
    on the Contact class itself.
    '''
    
    @classmethod
    def get_contact_overrides(cls, account):
        '''Retrieves contact overrides for focused inbox.
        
        Args:
            account: OutlookAccount instance
            
        Returns:
            List of Contact instances with focused status
        '''
        endpoint = 'https://graph.microsoft.com/v1.0/me/InferenceClassification/Overrides'
        r = requests.get(endpoint, headers=account._headers)
        
        check_response(r)
        return cls._json_to_contacts(r.json())
    
    @classmethod
    def _json_to_contact(cls, json_value: dict):
        '''Factory method: Converts JSON to a Contact instance.
        
        Args:
            json_value: JSON object representing a contact
            
        Returns:
            Contact instance or None if invalid data
        '''
        from pyOutlook.core.contact import Contact
        
        contact = json_value.get('EmailAddress', None)
        # The API returns this information in a different format if it's related to Focused inbox overrides
        contact_override = json_value.get('SenderEmailAddress', None)
        
        if contact is not None:
            email = contact.get('Address', None)
            name = contact.get('Name', None)
            return Contact(email, name)
        
        # This contains override information
        elif contact_override is not None:
            # Whether they are 'Focused' or 'Other'
            classification = json_value.get('ClassifyAs', 'Other')
            focused = True if classification == 'Focused' else False
            
            email = contact_override.get('Address', None)
            name = contact_override.get('Name', None)
            
            return Contact(email, name, focused=focused)
        
        return None
    
    @classmethod
    def _json_to_contacts(cls, json_value):
        '''Converts JSON array to list of Contact instances.
        
        Args:
            json_value: JSON response, either a dict with 'value' key or a list
            
        Returns:
            List of Contact instances
        '''
        # Sometimes, multiple contacts will be provided behind a dictionary with 'value' as the key
        try:
            json_value = json_value['value']
        except (TypeError, KeyError):
            pass
        
        return [cls._json_to_contact(contact) for contact in json_value]
