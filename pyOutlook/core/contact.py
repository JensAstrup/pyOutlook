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
