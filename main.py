# Authorization and misc functions
from pyOutlook import message_actions
from pyOutlook import internal_methods
from pyOutlook import retrieve
from pyOutlook import create_message


class AuthError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class OutlookAccount(object):
    def __init__(self, access_token):
        if type(access_token) is None:
            raise AuthError('No access token provided with object instantiation.')
        self.access_token = access_token
        pass

    def set_access_token(self, access_token):
        self.access_token = access_token

    def __get_access_token(self):
        return self.access_token

    token = property(__get_access_token)

    # References
    ###
    # retrieve.py
    def get_message(self, message_id):
        return retrieve.get_message(self, message_id)

    def get_messages(self):
        return retrieve.get_messages(self)

    def get_inbox(self):
        return retrieve.get_inbox(self)

    # create_message.py
    @property
    def new_email(self):
        return create_message.Message(self.access_token)

    # message_actions.py
    def forward_message(self, message_id: str, to_recipients: str):
        if type(message_id) is None:
            raise internal_methods.MiscError('Message ID not provided. Can not forward message.')

        if type(to_recipients) is None:
            raise internal_methods.MiscError('Message Recipients not provided. Can not forward message.')

        message_actions.forward_message(self, message_id, to_recipients, None)

    def forward_message_with_comment(self, message_id: str, to_recipients: str, forward_comment: str):

        if type(message_id) is None:
            raise internal_methods.MiscError('Message ID not provided. Can not forward message.')

        if type(to_recipients) is None:
            raise internal_methods.MiscError('Message Recipients not provided. Can not forward message.')

        message_actions.forward_message(self, message_id, to_recipients, forward_comment)

    def reply(self, message_id: str, reply_comment: str):

        if type(message_id) is None:
            raise internal_methods.MiscError('Message ID not provided. Can not forward message.')

        message_actions.reply(self, message_id, reply_comment, True)

    def reply_all(self, message_id: str, reply_comment: str):

        if type(message_id) is None:
            raise internal_methods.MiscError('Message ID not provided. Can not forward message.')

        message_actions.reply(self, message_id, reply_comment, True)
