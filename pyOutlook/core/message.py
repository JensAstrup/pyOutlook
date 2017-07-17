import base64
import logging
import json
from typing import List

import dateutil.parser
import requests

from pyOutlook.core.contact import Contact
from pyOutlook.internal.errors import AuthError, MiscError
from pyOutlook.internal.utils import get_valid_filename

log = logging.getLogger('pyOutlook')

__all__ = ['Message']


class Message(object):
    """An object representing an email inside of the OutlookAccount.

        Attributes:
            message_id: A string provided by Outlook identifying this specific email
            body: The body content of the email, including HTML formatting
            subject: The subject of the email
            sender_email: The email of the person who sent this email
            sender_name: The name of the person who sent this email, as provided by Outlook
            to: A list of :class:`Contacts <pyOutlook.core.contact.Contact>`

        """

    def __init__(self, account, body: str, subject: str, to_recipients: List[Contact],
                 sender: Contact = None, cc: List[Contact] = list, bcc: List[Contact]=list,
                 message_id: str = None, **kwargs):
        self.account = account
        self.message_id = message_id

        self.body = body
        self.subject = subject

        self.sender = sender
        self.to = to_recipients
        self.cc = cc
        self.bcc = bcc

        self.__is_read = kwargs.get('is_read', False)
        self.time_created = kwargs.get('time_created', None)

        self._attachments = []

    def __str__(self):
        return self.subject

    def __repr__(self):
        return str(self)

    @classmethod
    def _json_to_messages(cls, account, json_value):
        return [cls._json_to_message(account, message) for message in json_value['value']]

    @classmethod
    def _json_to_message(cls, account, api_json: dict):
        uid = api_json['Id']
        subject = api_json.get('Subject', '')

        sender = api_json.get('Sender', {})
        sender = Contact._json_to_contact(sender)

        body = api_json.get('Body', {}).get('Content', '')

        to_recipients = api_json.get('ToRecipients', [])
        to_recipients = Contact._json_to_contacts(to_recipients)

        is_read = api_json['IsRead']

        time_created = api_json.get('CreatedDateTime', None)

        if time_created is not None:
            time_created = dateutil.parser.parse(time_created, ignoretz=True)

        return_message = Message(account, body, subject, to_recipients, sender=sender, message_id=uid, is_read=is_read,
                                 time_created=time_created)
        return return_message

    @property
    def is_read(self):
        """ Set the 'Read' status of an email """
        return self.__is_read

    @is_read.setter
    def is_read(self, boolean):
        endpoint = 'https://outlook.office.com/api/v2.0/me/messages/{}'.format(self.message_id)
        payload = dict(IsRead=boolean)

        self._make_api_call('patch', endpoint, data=json.dumps(payload))
        self.__is_read = boolean

    def _make_api_call(self, http_type: str, endpoint: str, extra_headers: dict = None, data=None):
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

        if r.status_code == 401:
            log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
            raise AuthError('Access Token Error, Received 401 from Outlook REST Endpoint')
        elif r.status_code > 299:
            log.error('Error received from Outlook. Status: {} Body: {}'.format(r.status_code, r.json()))
            raise MiscError('Unhandled error received from Outlook. Check logging output.')
        else:
            log.debug('Response from Outlook Status: {} Body: {}'.format(r.status_code, r.content))

    def send(self, content_type='HTML'):
        """ Takes the recipients, body, and attachments of the Message and sends.

        Args:
            content_type: Can either be 'HTML' or 'Text', defaults to HTML.

        """
        payload = dict()

        payload.update(Subject=self.subject, Body=dict(ContentType=content_type, Content=self.body))

        recipients = [contact._api_representation() for contact in self.to]

        payload.update(ToRecipients=recipients)

        if self._attachments:
            payload.update(Attachments=self._attachments)

        payload = dict(Message=payload)

        endpoint = 'https://outlook.office.com/api/v1.0/me/sendmail'
        self._make_api_call('post', endpoint=endpoint, data=json.dumps(payload))

    def forward(self, to_recipients, forward_comment=None):
        """Forward Message to recipients with an optional comment.

        Args:
            to_recipients: A list of recipients to send the email to.
            forward_comment: String comment to append to forwarded email.

        Examples:
            >>> email = Message()
            >>> email.forward(['john.doe@domain.com', 'betsy.donalds@domain.com'])
            >>> email.forward('john.doe@domain.com', 'Hey Joe')
        """
        payload = dict()

        if forward_comment is not None:
            payload.update(Comment=forward_comment)

        # Contact() will handle turning itself into the proper JSON format for the API
        to_recipients = [Contact(email)._api_representation() for email in to_recipients]

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

    def move_to(self, folder_id):
        """Moves the email to the folder specified by the folder_id.

        The folder id must match the id provided by Outlook.

        Args:
            folder_id: A string containing the folder ID the message should be moved to

        """
        self._move_to(folder_id)

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
            file_bytes: The bytes of the file to send
            file_name: The name of the file, as a string and leaving out the extension, that should be sent

        Returns:
            Message

        """

        file_bytes = base64.b64encode(file_bytes)
        self._attachments.append({
            '@odata.type': '#Microsoft.OutlookServices.FileAttachment',
            'Name': get_valid_filename(file_name),
            'ContentBytes': file_bytes
        })
        return self
