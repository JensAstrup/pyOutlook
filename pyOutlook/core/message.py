import base64
import logging
import json

import six
from typing import List, TYPE_CHECKING, Union, Any

from dateutil import parser
import requests

from pyOutlook.core.contact import Contact
from pyOutlook.internal.utils import get_valid_filename, check_response

if TYPE_CHECKING:
    from pyOutlook import OutlookAccount, Folder

log = logging.getLogger('pyOutlook')

__all__ = ['Message']


class Message(object):
    """An object representing an email inside of the OutlookAccount.

        Attributes:
            message_id: A string provided by Outlook identifying this specific email
            body: The body content of the email, including HTML formatting
            body_preview: "The first 255 characters of the body"
            subject: The subject of the email
            sender: The :class:`Contact <pyOutlook.core.contact.Contact>` who sent this email. You can set this
                before sending an email to change which account the email comes from (so long as the
                :class:`OutlookAccount <pyOutlook.core.main.OutlookAccount>` specified has access to the email.
            to: A list of :class:`Contacts <pyOutlook.core.contact.Contact>`. You can also provide a list of strings,
                however these will be turned into :class:`Contacts <pyOutlook.core.contact.Contact>` after sending the
                email.
            cc: A list of :class:`Contacts <pyOutlook.core.contact.Contact>` in the CC field. You can also provide a
                list of strings, however these will be turned into :class:`Contacts <pyOutlook.core.contact.Contact>`
                after sending the email.
            bcc: A list of :class:`Contacts <pyOutlook.core.contact.Contact>` in the BCC field. You can also provide a
                list of strings, however these will be turned into :class:`Contacts <pyOutlook.core.contact.Contact>`
                after sending the email.
            is_draft: Whether or not the email is a draft.
            importance: The importance level of the email; with 0 indicating low, 1 indicating normal, and 2 indicating
                high. ``Message.IMPORTANCE_LOW``, ``Message.IMPORTANCE_NORMAL``, & ``Message.IMPORTANCE_HIGH`` can be
                used to reference the levels.
            categories: A list of strings, where each string is the name of a category.
            time_created: A datetime representing the time the email was created
            time_sent: A datetime representing the time the email was sent

        """

    IMPORTANCE_LOW = 0
    IMPORTANCE_NORMAL = 1
    IMPORTANCE_HIGH = 2

    def __init__(self, account, body, subject, to_recipients, sender=None,
                 cc=None, bcc=None, message_id=None, **kwargs):
        # type: (OutlookAccount, str, str, Union[List[Contact], List[str]], Contact, List[Contact], List[Contact], str) -> None
        self.account = account
        self.message_id = message_id

        self.body = body
        self.body_preview = kwargs.get('body_preview', '')
        self.subject = subject

        self.is_draft = kwargs.get('is_draft', None)
        self.importance = kwargs.get('Importance', self.IMPORTANCE_NORMAL)
        self.categories = kwargs.get('categories', [])

        self.sender = sender
        self.to = to_recipients
        self.cc = cc or []
        self.bcc = bcc or []

        self.time_created = kwargs.get('time_created', None)
        self.time_sent = kwargs.get('time_sent', None)

        self._attachments = []

        self.__is_read = kwargs.get('is_read', False)
        self.__parent_folder_id = kwargs.get('parent_folder_id', None)
        self.__parent_folder = None

    def __str__(self):
        return self.subject

    def __repr__(self):
        return str(self)

    @classmethod
    def _json_to_messages(cls, account, json_value):
        return [cls._json_to_message(account, message) for message in json_value['value']]

    @classmethod
    def _json_to_message(cls, account, api_json):
        uid = api_json['Id']
        subject = api_json.get('Subject', '')

        sender = api_json.get('Sender', {})
        sender = Contact._json_to_contact(sender)

        body = api_json.get('Body', {}).get('Content', '')
        body_preview = api_json.get('BodyPreview', '')

        to_recipients = api_json.get('ToRecipients', [])
        to_recipients = Contact._json_to_contacts(to_recipients)

        is_read = api_json['IsRead']

        time_created = api_json.get('CreatedDateTime', None)
        if time_created is not None:
            time_created = parser.parse(time_created, ignoretz=True)

        time_sent = api_json.get('SentDateTime', None)
        if time_sent is not None:
            time_sent = parser.parse(time_sent, ignoretz=True)

        parent_folder_id = api_json.get('ParentFolderId', None)
        is_draft = api_json.get('IsDraft', None)
        importance = api_json.get('Importance', cls.IMPORTANCE_NORMAL)

        categories = api_json.get('Categories', [])

        return_message = Message(account, body, subject, to_recipients, sender=sender, message_id=uid, is_read=is_read,
                                 time_created=time_created, time_sent=time_sent, parent_folder_id=parent_folder_id,
                                 is_draft=is_draft, importance=importance, body_preview=body_preview,
                                 categories=categories)
        return return_message

    @property
    def is_read(self):
        """ Set and retrieve the 'Read' status of an email

            >>> message = Message()
            >>> message.is_read
            >>> False
            >>> message.is_read = True
        """
        return self.__is_read

    @is_read.setter
    def is_read(self, boolean):
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}'.format(self.message_id)
        payload = dict(IsRead=boolean)

        self._make_api_call('patch', endpoint, data=json.dumps(payload))
        self.__is_read = boolean

    @property
    def parent_folder(self):
        # type: () -> Folder
        """ Returns the :class:`Folder <pyOutlook.core.folder.Folder>` this message is in

            >>> account = OutlookAccount('')
            >>> message = account.get_messages()[0]
            >>> message.parent_folder
            Inbox
            >>> message.parent_folder.unread_count
            19

        Returns: :class:`Folder <pyOutlook.core.folder.Folder>`

        """
        if self.__parent_folder is None:
            self.__parent_folder = self.account.get_folder_by_id(self.__parent_folder_id)

        return self.__parent_folder

    def _make_api_call(self, http_type, endpoint, extra_headers = None, data=None):
        # type: (str, str, dict, Any) -> None
        """
        Internal method to handle making calls to the Outlook API and logging both the request and response
        Args:
            http_type: (str) 'post' or 'delete'
            endpoint: (str) The endpoint the request will be made to
            headers: A dict of headers to send to the requests module in addition to Authorization and Content-Type
            data: The data to provide to the requests module

        Raises:
            MiscError: For errors that aren't a 401
            AuthError: For 401 errors

        """

        headers = {"Authorization": "Bearer " + self.account.access_token, "Content-Type": "application/json"}

        if extra_headers is not None:
            headers.update(extra_headers)

        log.debug('Making Outlook API request for message (ID: {}) with Headers: {} Data: {}'
                  .format(self.message_id, headers, data))

        if http_type == 'post':
            r = requests.post(endpoint, headers=headers, data=data)
        elif http_type == 'delete':
            r = requests.delete(endpoint, headers=headers)
        elif http_type == 'patch':
            r = requests.patch(endpoint, headers=headers, data=data)
        else:
            raise NotImplemented

        check_response(r)

    def _api_representation(self, content_type):
        payload = dict(Subject=self.subject, Body=dict(ContentType=content_type, Content=self.body))

        if self.sender is not None:
            payload.update(Sender=self.sender._api_representation())

        # A list of strings can also be provided for convenience. If provided, convert them into Contacts
        if any(isinstance(item, str) for item in self.to):
            self.to = [Contact(email=email) for email in self.to]

        # Turn each contact into the JSON needed for the Outlook API
        recipients = [contact._api_representation() for contact in self.to]

        payload.update(ToRecipients=recipients)

        # Conduct the same process for CC and BCC if needed
        if self.cc:
            if any(isinstance(email, str) for email in self.cc):
                self.cc = [Contact(email) for email in self.cc]

            cc_recipients = [contact._api_representation() for contact in self.cc]
            payload.update(CcRecipients=cc_recipients)

        if self.bcc:
            if any(isinstance(email, str) for email in self.bcc):
                self.bcc = [Contact(email) for email in self.bcc]

            bcc_recipients = [contact._api_representation() for contact in self.bcc]
            payload.update(BccRecipients=bcc_recipients)

        if self._attachments:
            payload.update(Attachments=self._attachments)

        return dict(Message=payload)

    def send(self, content_type='HTML'):
        """ Takes the recipients, body, and attachments of the Message and sends.

        Args:
            content_type: Can either be 'HTML' or 'Text', defaults to HTML.

        """

        payload = self._api_representation(content_type)

        endpoint = 'https://outlook.office.com/api/v1.0/me/sendmail'
        self._make_api_call('post', endpoint=endpoint, data=json.dumps(payload))

    def forward(self, to_recipients, forward_comment=None):
        # type: (Union[List[Contact], List[str]], str) -> None
        """Forward Message to recipients with an optional comment.

        Args:
            to_recipients: A list of :class:`Contacts <pyOutlook.core.contact.Contact>` to send the email to.
            forward_comment: String comment to append to forwarded email.

        Examples:
            >>> john = Contact('john.doe@domain.com')
            >>> betsy = Contact('betsy.donalds@domain.com')
            >>> email = Message()
            >>> email.forward([john, betsy])
            >>> email.forward([john], 'Hey John')
        """
        payload = dict()

        if forward_comment is not None:
            payload.update(Comment=forward_comment)

        # A list of strings can also be provided for convenience. If provided, convert them into Contacts
        if any(isinstance(recipient, str) for recipient in to_recipients):
            to_recipients = [Contact(email=email) for email in to_recipients]

        # Contact() will handle turning itself into the proper JSON format for the API
        to_recipients = [contact._api_representation() for contact in to_recipients]

        payload.update(ToRecipients=to_recipients)

        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}/forward'.format(self.message_id)

        self._make_api_call('post', endpoint=endpoint, data=json.dumps(payload))

    def reply(self, reply_comment):
        """Reply to the Message.

        Notes:
            HTML can be inserted in the string and will be interpreted properly by Outlook.

        Args:
            reply_comment: String message to send with email.

        """
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/reply'

        self._make_api_call('post', endpoint, data=payload)

    def reply_all(self, reply_comment):
        """Replies to everyone on the email, including those on the CC line.

        With great power, comes great responsibility.

        Args:
            reply_comment: The string comment to send to everyone on the email.

        """
        payload = '{ "Comment": "' + reply_comment + '"}'
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}/replyall'.format(self.message_id)

        self._make_api_call('post', endpoint, data=payload)

    def delete(self):
        """Deletes the email"""
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id
        self._make_api_call('delete', endpoint)

    def _move_to(self, destination):
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/move'
        payload = '{ "DestinationId": "' + destination + '"}'
        self._make_api_call('post', endpoint, data=payload)

    def move_to_inbox(self):
        """Moves the email to the account's Inbox"""
        self._move_to('Inbox')

    def move_to_deleted(self):
        """Moves the email to the account's Deleted Items folder"""
        self._move_to('DeletedItems')

    def move_to_drafts(self):
        """Moves the email to the account's Drafts folder"""
        self._move_to('Drafts')

    def move_to(self, folder):
        """Moves the email to the folder specified by the folder parameter.

        Args:
            folder: A string containing the folder ID the message should be moved to, or a Folder instance

        """
        if isinstance(folder, Folder):
            self.move_to(folder.id)
        else:
            self._move_to(folder)

    def _copy_to(self, destination):
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/' + self.message_id + '/copy'
        payload = '{ "DestinationId": "{}"}'.format(destination)

        self._make_api_call('post', endpoint, data=payload)

    def copy_to_inbox(self):
        """Copies Message to account's Inbox"""
        self._copy_to('Inbox')

    def copy_to_deleted(self):
        """Copies Message to account's Deleted Items folder"""
        self._copy_to('DeletedItems')

    def copy_to_drafts(self):
        """Copies Message to account's Drafts folder"""
        self._copy_to('Drafts')

    def copy_to(self, folder_id):
        """Copies the email to the folder specified by the folder_id.

        The folder id must match the id provided by Outlook.

        Args:
            folder_id: A string containing the folder ID the message should be copied to

        """
        self._copy_to(folder_id)

    def attach(self, file_bytes, file_name):
        """Adds an attachment to the email. The filename is passed through Django's get_valid_filename which removes
        invalid characters. From the documentation for that function:

        >>> get_valid_filename("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'

        Args:
            file_bytes: The bytes of the file to send (if you send a string, ex for CSV, pyOutlook will attempt to
                convert that into bytes before base64ing the content).
            file_name: The name of the file, as a string and leaving out the extension, that should be sent

        """
        try:
            file_bytes = base64.b64encode(file_bytes)
        except TypeError:
            file_bytes = base64.b64encode(bytes(file_bytes, 'utf-8'))

        self._attachments.append({
            '@odata.type': '#Microsoft.OutlookServices.FileAttachment',
            'Name': get_valid_filename(file_name),
            'ContentBytes': file_bytes.decode('utf-8')
        })

    def add_category(self, category_name):
        # type: (str) -> None
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}'.format(self.message_id)
        self.categories.append(category_name)
        self._make_api_call('patch', endpoint, data=json.dumps(dict(Categories=self.categories)))
