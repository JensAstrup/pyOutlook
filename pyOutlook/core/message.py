# Functions used by other files, but not used directly in parent code
import requests

from pyOutlook.internal.errors import AuthError, MiscError
from pyOutlook.internal.utils import jsonify_recipients, get_global_token


# noinspection PyUnresolvedReferences
class Message(object):
    """An object representing an email inside of the OutlookAccount.

        Attributes:
            message_id: A string provided by Outlook identifying this specific email
            body: The body content of the email, including HTML formatting
            subject: The subject of the email
            senderEmail: The email of the person who sent this email
            senderName: The name of the person who sent this email, as provided by Outlook
            toRecipients: A comma separated string of emails who were sent this email in the 'To' field

        """

    def __init__(self, message_id: str, body: str, subject: str, sender_email: str, sender_name: str,
                 to_recipients: list):
        self.message_id = message_id
        self.body = body
        self.subject = subject
        self.sender_email = sender_email
        self.sender_name = sender_name
        self.to_recipients = to_recipients

    def __str__(self):
        return self.__getattribute__('subject')

    def forward_message(self, to_recipients, forward_comment):
        """Forward Message to recipients with an optional comment.

        Args:
            to_recipients: Comma separated string list of recipients to send email to.
            forward_comment: String comment to append to forwarded email.

        Examples:
            >>> email.forward_message('john.doe@domain.com, betsy.donalds@domain.com')
            >>> email.forward_message('john.doe@domain.com', 'Hey Joe')

        Raises:
            MiscError: A comma separated string of emails, or one string email, must be provided
            AuthError: Raised if Outlook returns a 401, generally caused by an invalid or expired access token.

        """
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        payload = '{'
        if type(forward_comment) is not None:
            payload += '"Comment" : "' + str(forward_comment) + '",'
        if type(to_recipients) is None:
            raise MiscError('To Recipients is not defined. Can not forward message.')

        payload += '"ToRecipients" : [' + jsonify_recipients(to_recipients, 'to', True) + ']}'

        r = requests.post('https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/forward',
                          headers=headers, data=payload)

        if r.status_code == 401:
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')

    def reply(self, reply_comment):
        """Reply to the Message.

        Notes:
            HTML can be inserted in the string and will be interpreted properly by Outlook.

        Args:
            reply_comment: String message to send with email.

        """
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/reply'

        r = requests.post(endpoint, headers=headers, data=payload)

        if r.status_code == 401:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    def reply_all(self, reply_comment):
        """Replies to everyone on the email, including those on the CC line.

        With great power, comes great responsibility.

        Args:
            reply_comment: The string comment to send to everyone on the email.

        """
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/replyall'

        r = requests.post(endpoint, headers=headers, data=payload)

        if r.status_code == 401:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    def delete_message(self):
        """Deletes the email"""
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id

        r = requests.delete(endpoint, headers=headers)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    def __move_to(self, destination):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/move'
        payload = '{ "DestinationId": "' + destination + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    def move_to_inbox(self):
        """Moves the email to the account's Inbox"""
        self.__move_to('Inbox')

    def move_to_deleted(self):
        """Moves the email to the account's Deleted Items folder"""
        self.__move_to('DeletedItems')

    def move_to_drafts(self):
        """Moves the email to the account's Drafts folder"""
        self.__move_to('Drafts')

    def move_to(self, folder_id):
        """Moves the email to the folder specified by the folder_id.

        The folder id must match the id provided by Outlook.

        Args:
            folder_id: A string containing the folder ID the message should be moved to

        """
        self.__move_to(folder_id)

    def __copy_to(self, destination):
        access_token = get_global_token()
        headers = {"Authorization": "Bearer " + access_token, "Content-Type": "application/json"}
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/copy'
        payload = '{ "DestinationId": "' + destination + '"}'

        r = requests.post(endpoint, headers=headers, data=payload)

        if 399 < r.status_code < 452:
            raise AuthError('Access Token Error, Received ' + str(r.status_code) + ' from Outlook REST Endpoint')

    def copy_to_inbox(self):
        """Copies Message to account's Inbox"""
        self.__copy_to('Inbox')

    def copy_to_deleted(self):
        """Copies Message to account's Deleted Items folder"""
        self.__copy_to('DeletedItems')

    def copy_to_drafts(self):
        """Copies Message to account's Drafts folder"""
        self.__copy_to('Drafts')

    def copy_to(self, folder_id):
        """Copies the email to the folder specified by the folder_id.

        The folder id must match the id provided by Outlook.

        Args:
            folder_id: A string containing the folder ID the message should be copied to

        """
        self.__copy_to(folder_id)
