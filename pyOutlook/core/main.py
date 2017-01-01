# Authorization and misc functions
from pyOutlook.core.folders import get_folders, get_folder
from pyOutlook.internal import retrieve
from pyOutlook.internal.utils import Deprecated, set_global_token__
from pyOutlook.internal.errors import MiscError, AuthError
from pyOutlook.internal.createMessage import NewMessage
from pyOutlook.core.message import Message


class OutlookAccount(object):
    """Sets up access to Outlook account for all methods & classes.

    Access token required for instantiation. Can be refreshed at a later time using .set_access_token().

    Warnings:
        This module does not handle the OAuth process. You must retrieve and refresh tokens separately.

    Attributes:
        access_token: A string OAuth token from Outlook allowing access to a user's account

    """
    def __init__(self, access_token):
        if type(access_token) is None:
            raise AuthError('No access token provided with object instantiation.')
        self.access_token = access_token
        set_global_token__(access_token)

    def set_access_token(self, access_token):
        """Sets access token.

        Set the access token after creating an OutlookAccount object.

        Args:
            access_token: A string representing the OAuth token

        Returns:
            None

        """
        self.access_token = access_token
        set_global_token__(access_token)

    def __get_access_token(self):
        return self.access_token

    token = property(__get_access_token)

    def get_message(self, message_id) -> Message:
        """Gets message matching provided id.

        Retrieves the Outlook email matching the provided message_id.

        Args:
            message_id: A string for the intended message, provided by Outlook

        Returns:
            Message

        """
        return retrieve.get_message(self, message_id)

    def get_messages(self):
        """Get first 10 messages in account, across all folders.

        Returns:
            List[Message]

        """
        return retrieve.get_messages(self, 0)

    def get_more_messages(self, page):
        """Retrieves additional messages, across all folders, indicated by 'page' number. get_messages() fetches page 1.

        Args:
            page (int): Integer representing the 'page' of results to fetch

        Returns:
            List[Message]

        """
        if not isinstance(page, int):
            raise MiscError('page parameter must be of type integer')
        return retrieve.get_messages(self, page)

    @Deprecated('OutlookAccount.get_inbox() is deprecated. Use account.inbox() instead.')
    def get_inbox(self):
        """Retrieves first ten messages in account's inbox.

        Returns:
            List[Message]

        Warnings:
            This method is deprecated, use :py:meth:`~pyOutlook.OutlookAccount.inbox` instead

        """
        return self.inbox()

    def inbox(self):
        """Retrieves first ten messages in account's inbox.

        Returns:
            List[Message]

        """
        return retrieve.get_inbox(self)

    def new_email(self):
        """Creates a NewMessage object.

        Returns:
            NewMessage

        """
        return NewMessage(self.access_token)

    def send_email(self, body=None, subject=None, to=None, cc=None, bcc=None,
                   send_as=None, attachment=None):
        """Sends an email in one method using variables to set the various pieces of the email.

        Args:
            body (str): The body of the email
            subject (str): The subject of the email
            to (list): A list of email addresses
            cc (list): A list of email addresses which will be added to the 'Carbon Copy' line
            bcc (list): A list of email addresses while be blindly added to the email
            send_as (str): A string email address which the OutlookAccount has access to
            attachment (dict): A dictionary with three parts [1] 'name' - a string which will become the file's name \
            [2] 'ext' - a string which will become the file extension [3] 'bytes' - the bytes of the file.

        """
        email = NewMessage(self.access_token)
        if body is not None:
            email.set_body(body)
        if subject is not None:
            email.set_subject(subject)
        if to is not None:
            email.to(to)
        if cc is not None:
            email.cc(cc)
        if bcc is not None:
            email.bcc(bcc)
        if send_as is not None:
            email.send_as(send_as)
        if attachment is not None:
            if 'bytes' not in attachment or 'name' not in attachment or 'ext' not in attachment:
                raise TypeError('Was unable to find one or more keys in the attachment dictionary: bytes, name, ext.')
            email.attach(attachment['bytes'], attachment['name'], attachment['ext'])
        email.send()

    @Deprecated('OutlookAccount.get_sent_messages() is deprecated. Use account.sent_messages() instead.')
    def get_sent_messages(self):
        """Retrieves last ten sent messages.

        Returns:
            list[Message]

        Warnings:
            This method is deprecated, use :py:meth:`~pyOutlook.OutlookAccount.sent_messages` instead


        """
        return self.sent_messages()

    def sent_messages(self):
        """Retrieves last ten sent messages.

        Returns:
            list[Message]

        """
        return retrieve.get_messages_from_folder_name(self, 'SentItems')

    @Deprecated('OutlookAccount.get_deleted_messages() is deprecated. Use account.deleted_messages() instead.')
    def get_deleted_messages(self):
        """Retrieves last ten deleted messages.

        Returns:
            list[Message]

        Warnings:
            This method is deprecated, use :py:meth:`~pyOutlook.OutlookAccount.deleted_messages` instead

        """
        return self.deleted_messages()

    def deleted_messages(self):
        """Retrieves last ten deleted messages.

        Returns:
            list[Message]

        """
        return retrieve.get_messages_from_folder_name(self, 'DeletedItems')

    @Deprecated('OutlookAccount.get_draft_messages() is deprecated. Use account.draft_messages() instead.')
    def get_draft_messages(self):
        """Retrieves last ten draft messages.

        Returns:
            list[Message]

        Warnings:
            This method is deprecated, use :py:meth:`~pyOutlook.OutlookAccount.draft_messages` instead

        """
        return self.draft_messages()

    def draft_messages(self):
        """Retrieves last ten draft messages.

        Returns:
            list[Message]

        """
        return retrieve.get_messages_from_folder_name(self, 'Drafts')

    # TODO: keep as get_x or rename?
    def get_folder_messages(self, folder):
        """Retrieve first ten messages from provided folder.

        Args:
            folder: String providing the folder ID, from Outlook, to retrieve messages from

        Returns:
            list[Message]

        """
        return retrieve.get_messages_from_folder_name(self, folder)

    # TODO: keep as get_x or rename?
    def get_folders(self):
        """Retrieves a list of folders in the account.

        Returns:
            list[Folder]

        """
        return get_folders(self)

    # TODO: keep as get_x or rename?
    def get_folder(self, folder_id):
        """Retrieve a Folder object matching the folder ID provided.

        Args:
            folder_id: String identifying the Outlook folder to return

        Returns:
            Folder

        """
        return get_folder(self, folder_id)
