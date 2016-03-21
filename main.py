# Authorization and misc functions
import retrieve
import create_message


class AuthError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class OutlookAccount(object):
    def __init__(self):
        self.acess_token = None
        pass

    def set_access_token(self, access_token):
        self.acess_token = access_token

    def __get_access_token(self):
        return self.acess_token

    token = property(__get_access_token)

    # References
    ###
    # Retrieving
    def get_message(self, message_id):
        return retrieve.get_message(self, message_id)

    def get_messages(self):
        return retrieve.get_messages(self)

    def get_inbox(self):
        return retrieve.get_inbox(self)

    # Sending
    @property
    def new_email(self):
        return create_message.Message(self.acess_token)
