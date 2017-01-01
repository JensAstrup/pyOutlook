import base64

from pyOutlook.internal.errors import SendError, MiscError
from pyOutlook.internal.utils import jsonify_recipients, Deprecated
import requests


class NewMessage(object):
    """ A constructor for new emails.

    Each method, excluding send(), returns the NewMessage object allowing chaining of methods.

    """

    def __init__(self, token):
        self.__access_token = token
        self.__subject = None
        self.__body = ''
        self.__to_line = None
        self.__cc_line = None
        self.__bcc_line = None
        self.__send_as = None
        self.__file_bytes = None
        self.__file_name = None
        self.__file_extension = None

    def __send_email(self):
        json_send = '{ "Message": {"'
        json_cc = None
        json_bcc = None

        if self.__to_line is not None:
            json_to = jsonify_recipients(self.__to_line, "to", False)

        else:
            raise SendError('Error, to must be specified.')

        if self.__cc_line is not None:
            json_cc = jsonify_recipients(self.__cc_line, "cc", False)

        if self.__bcc_line is not None:
            json_bcc = jsonify_recipients(self.__bcc_line, "bcc", False)

        if self.__subject is not None:
            json_send += 'Subject": "' + self.__subject + '",'
        else:
            raise SendError('Error, subject must be specified.')

        json_send += '"Body": { "ContentType": "HTML", "Content": "' + self.__body + '"}'
        # set the recipients
        json_send += ',' + json_to + ']'
        if json_cc is not None:
            json_send += ',' + json_cc + ']'

        if json_bcc is not None:
            json_send += ',' + json_bcc + ']'

        if self.__send_as is not None:
            json_send += ',"From":{ "EmailAddress": { "Address": "' + self.__send_as + '" } }'

        if type(self.__file_bytes) is not None:
            if self.__file_name is not None and self.__file_extension is not None:
                file_name = str(self.__file_name).replace('/', '-').replace('.', '-')
                full_file_name = '{}.{}'.format(file_name, str(self.__file_extension))
                json_send += (',"Attachments": [ {{ "@odata.type": "#Microsoft.OutlookServices.FileAttachment", '
                              '"Name": "{}", "ContentBytes": "{}" }} ]'.
                              format(full_file_name, str(self.__file_bytes, 'UTF8')))

        json_send += '}}'

        headers = {"Authorization": "Bearer " + self.__access_token, "Content-Type": "application/json"}
        r = requests.post('https://outlook.office.com/api/v1.0/me/sendmail', headers=headers, data=json_send)
        if r.status_code != 202:
            raise MiscError('Did not receive status code 202 from Outlook REST Endpoint. Ensure that your access token '
                            'is current. STATUS CODE: ' + str(r.status_code) + '. RESPONSE: ' + str(r.content))

    def set_subject(self, subject):
        """Sets the subject for the email.

        This method is required in order to send the email.

        Args:
            subject: str

        Returns:
            NewMessage

        """
        self.__subject = subject
        return self

    def set_body(self, body):
        """Sets the body of the email.

        Args:
            body: str

        Returns:
            NewMessage

        """
        self.__body = body
        return self

    def to(self, recipients):
        """The list of email addresses this email should be sent to.

        This method is required in order to send the email. The recipients parameter can either be a single address
        string or a comma separated list of addresses provided as a string.

        Examples:
            >>> email.to('john@domain.com')
            >>> email.to('john@domain.com, jane@domain.com')

        Args:
            recipients: A comma separated string of email addresses, or a list of strings.

        Returns:
            NewMessage

        """
        if isinstance(recipients, str):
            self.__to_line = recipients
        elif isinstance(recipients, list):
            self.__to_line = ', '.join(recipients)
        else:
            raise ValueError('The recipients argument must be of type str or list')
        return self

    def cc(self, recipients):
        """The list of email addresses that should be copied on this email.

        Args:
            recipients: A comma separated string of email addresses, or a list of strings.

        Returns:
            NewMessage

        """
        if isinstance(recipients, str):
            self.__cc_line = recipients
        elif isinstance(recipients, list):
            self.__cc_line = ', '.join(recipients)
        else:
            raise ValueError('The recipients argument must be of type str or list')
        return self

    def bcc(self, recipients):
        """The list of email addresses that should be 'blind' copied on this email.

        Args:
            recipients: A comma separated string of email addresses, or a list of strings.

        Returns:
            NewMessage

        """
        if isinstance(recipients, str):
            self.__bcc_line = recipients
        elif isinstance(recipients, list):
            self.__bcc_line = ', '.join(recipients)
        else:
            raise ValueError('The recipients argument must be of type str or list')
        return self

    def send_as(self, email):
        """Send the email via a separate email address, which the OutlookAccount has access to.

        Args:
            email: A string providing the secondary email address that this email should be sent through.

        Returns:
            NewMessage

        """
        self.__send_as = email
        return self

    @Deprecated('NewMessage.add_attachment is deprecated. Use NewMessage.attach() instead')
    def add_attachment(self, file_bytes, file_name, file_extension):
        """Adds an attachment to the email.

        Warnings:
            This method is deprecated, use NewMessage.attach() instead. If using this method, you must base64 encode the
            file_bytes.

        """
        self.__file_bytes = file_bytes
        self.__file_name = file_name
        self.__file_extension = file_extension
        return self

    def attach(self, file_bytes, file_name, file_extension):
        """Adds an attachment to the email.

        Warnings:
            This method does minimal escaping of input for the file_name. Slashes and periods will both be replaced by
            dashs (/), (.) > (-). Outlook may cut off portions of the file name due to some characters, if you encounter
            one, please create an issue on this module's GitHub: https://github.com/JensAstrup/pyOutlook/issues.

        Notes:
            You can send any file with this method, so long as the content is provided in bytes. Not doing so may lead
            to malformed attachments.
            You can also send bytes in a format that was not created in the same extension as the one provided to this
            method. For example, CSV bytes sent through with an xlsx extension will be attached and usable as an Excel
            document.

        Args:
            file_bytes: The bytes of the file to send
            file_name: The name of the file, as a string and leaving out the extension, that should be sent
            file_extension: The extension type (pdf, csv, etc) of the attachment. Do not include the '.' in the string.

        Returns:
            NewMessage

        """
        self.__file_bytes = base64.b64encode(file_bytes)
        self.__file_name = file_name
        self.__file_extension = file_extension
        return self

    def send(self):
        """Sends the email containing the information provided in the other methods.

        Raises:
            SendError: Occurs if a subject or to recipients are not defined
            MiscError: Occurs if Outlook responds with anything other than a 202, generally as a result of an expired
            or invalid access token.

        """
        self.__send_email()
