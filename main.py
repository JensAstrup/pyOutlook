# Authorization and misc functions
from pyOutlook import retrieve
from pyOutlook import create_message
from pyOutlook import folders
from pyOutlook.internal_methods import MiscError


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
        return retrieve.get_messages(self, 0)

    def get_more_messages(self, page):
        if not isinstance(page, int):
            print type(page)
            raise MiscError('page parameter must be of type integer')
        return retrieve.get_messages(self, page)

    def get_inbox(self):
        return retrieve.get_inbox(self)

    # create_message.py
    @property
    def new_email(self):
        return create_message.NewMessage(self.access_token)

    def get_sent_messages(self):
        return retrieve.get_messages_from_folder_name(self, 'SentItems')

    def get_deleted_messages(self):
        return retrieve.get_messages_from_folder_name(self, 'DeletedItems')

    def get_draft_messages(self):
        return retrieve.get_messages_from_folder_name(self, 'Drafts')

    def get_folder_messages(self, folder):
        return retrieve.get_messages_from_folder_name(self, folder)

    # folders
    def get_folders(self):
        """

        :return: a list of Folder objects
        """
        return folders.get_folders(self)

    def create_folder(self, parent_folder_id, new_folder_name):
        """
        :param parent_folder_id: Either the ID of the parent folder, or a common name ('Inbox', 'Drafts', 'DeletedItems'
        :param new_folder_name: The name for the new folder
        :return: new folder Id
        """
        return folders.create_folder(self, parent_folder_id, new_folder_name)
