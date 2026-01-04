import json
import requests

from pyOutlook.internal.utils import check_response

__all__ = ['Contact']


class Contact(object):
    """ Represents someone sending or receiving an email. Cuts down on the amount of dictionaries floating around that
    each hold the API's syntax and allows for functionality to be added in the future.

    Args:
        email (str): The email of the user
        name (str): The user's name, which is not always provided by the API.

    Keyword Args:
        focused: Whether messages from this sender are always sent to the Focused inbox, or to the Other tab.
            This value is set when retrieving a contact from the API, or after setting it via
            :func:`set_focused() <pyOutlook.core.contact.Contact.set_focused>`

    Attributes:
        email: The email of the user
        name: The name of the user
        focused: A boolean indicating whether this contact has an override for their messages to go to the Focused inbox
            or the "Other" inbox. None indicates that the value has not yet been retrieved by the API or set.
    """

    def __init__(self, email, name=None, focused=None):
        # type: (str, str, bool) -> None
        self.email = email
        self.name = name
        self.focused = focused

    def __str__(self):
        if self.name is None:
            return self.email
        return '{} ({})'.format(self.name, self.email)

    def __repr__(self):
        return str(self)

    def __iter__(self):
        """Allows dict(Contact) to return an API-formatted dictionary."""
        yield 'EmailAddress', {'Name': self.name, 'Address': self.email}

    def set_focused(self, account, is_focused):
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
        endpoint = 'https://graph.microsoft.com/v1.0/me/InferenceClassification/Overrides'

        if is_focused:
            classification = 'Focused'
        else:
            classification = 'Other'

        data = dict(ClassifyAs=classification, SenderEmailAddress=dict(Address=self.email))

        r = requests.post(endpoint, headers=account._headers, data=json.dumps(data), timeout=10)

        # Will raise an error if necessary, otherwise returns True
        result = check_response(r)

        self.focused = is_focused

        return result
