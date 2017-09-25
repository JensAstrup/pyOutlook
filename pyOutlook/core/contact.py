import json
import typing

import requests

from pyOutlook.internal.utils import check_response

if typing.TYPE_CHECKING:
    from pyOutlook import OutlookAccount

__all__ = ['Contact']


class Contact(object):
    """ Represents someone sending or receiving an email. Cuts down on the amount of dictionaries floating around that
    each hold the API's syntax and allows for functionality to be added in the future.
    """

    def __init__(self, email, name=None):
        """
        Args:
            email (str): The email of the user
            name (str): The user's name, which is not always provided by the API.
        """
        self.email = email
        self.name = name

    def __str__(self):
        if self.name is None:
            return self.email
        return '{} ({})'.format(self.name, self.email)

    def __repr__(self):
        return str(self)

    @classmethod
    def _json_to_contact(cls, json_value):
        contact = json_value.get('EmailAddress', None)
        if contact is not None:
            email = contact.get('Address', None)
            name = contact.get('Name', None)
            return Contact(email, name)
        else:
            return None

    @classmethod
    def _json_to_contacts(cls, json_value):
        return [cls._json_to_contact(contact) for contact in json_value]

    def _api_representation(self):
        """ Returns the JSON formatting required by Outlook's API for contacts """
        return dict(EmailAddress=dict(Name=self.name, Address=self.email))

    def set_focused_override(self, account, is_focused):
        # type: (OutlookAccount, bool) -> bool
        """ Emails from this contact will either always be put in the Focused inbox, or always put in Other, based on
        the value of is_focused.

        Args:
            account (OutlookAccount): The :class:`OutlookAccount <pyOutlook.core.main.OutlookAccount>`
                the override should be set for
            is_focused (bool): Whether this contact should be set to Focused, or Other.

        Returns:
            True if the request was successful
        """
        endpoint = 'https://outlook.office.com/api/v2.0/me/InferenceClassification/Overrides'

        if is_focused:
            classification = 'Focused'
        else:
            classification = 'Other'

        data = dict(ClassifyAs=classification, SenderEmailAddress=dict(Address=self.email))

        r = requests.post(endpoint, headers=account._headers, data=json.dumps(data))

        return check_response(r)
