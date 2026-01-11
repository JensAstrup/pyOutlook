import json
from typing import TYPE_CHECKING

import requests

from pyOutlook.internal.utils import check_response

if TYPE_CHECKING:
    from pyOutlook.core.main import OutlookAccount

__all__ = ['Contact']


class Contact(object):
    """Represents someone sending or receiving an email.

    Provides a structured representation of email addresses with optional
    name and focused inbox override settings.

    :param email: The email address of the contact.
    :type email: str
    :param name: The contact's display name. May be ``None`` if not provided by the API.
    :type name: str or None
    :param focused: Whether messages from this sender go to Focused inbox.
        ``True`` for Focused, ``False`` for Other, ``None`` if not set or retrieved.
    :type focused: bool or None

    :ivar email: The email address.
    :ivar name: The display name.
    :ivar focused: Focused inbox override status. This value is set when retrieving
        a contact from the API, or after calling :meth:`set_focused`.

    Example::

        # Creating a contact for sending
        recipient = Contact('user@example.com', name='John Doe')

        # Using with the API
        payload = dict(recipient)  # Converts to API format
    """

    def __init__(self, email: str, name: str | None = None, focused: bool | None = None):
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
        """Allows ``dict(Contact)`` to return an API-formatted dictionary.

        Used when building API payloads for sending messages.

        :yields: Tuples of (key, value) for dictionary construction.
        :rtype: Iterator[tuple[str, dict]]

        Example::

            recipient = Contact('user@example.com', name='John')
            api_format = dict(recipient)
            # {'EmailAddress': {'Name': 'John', 'Address': 'user@example.com'}}
        """
        yield 'EmailAddress', {'Name': self.name, 'Address': self.email}

    def set_focused(self, account: 'OutlookAccount', is_focused: bool) -> bool:
        """Set whether emails from this contact go to Focused or Other inbox.

        Creates an inference classification override for this sender's email address.
        After calling this method, all future emails from this contact will be
        automatically sorted to the specified inbox section.

        :param account: The OutlookAccount to set the override for.
        :type account: OutlookAccount
        :param is_focused: ``True`` to send to Focused inbox, ``False`` for Other.
        :type is_focused: bool

        :returns: ``True`` if the request was successful.
        :rtype: bool

        :raises AuthError: If authentication fails (invalid or expired token).
        :raises RequestError: If the API request is invalid.
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
