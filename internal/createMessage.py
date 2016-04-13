import requests
from pyOutlook.internal.internalMethods import jsonify_receps
from pyOutlook.internal.errors import SendError, MiscError


class NewMessage(object):
    def __init__(self, token):
        self.__access_token = token
        self.subject = None
        self.body = None
        self.__to_line = None
        self.__cc_line = None
        self.__bcc_line = None
        self.__send_as = None
        self.__file_bytes = None
        self.__file_name = None
        self.__file_extension = None

    ###
    # Send Email Function
    ###
    def __send_email(self):
        global json_send
        json_send = '{ "Message": {"'

        if hasattr(self, '__to_line'):
            json_to = jsonify_receps(self.__getattribute__('__to_line'), "to", False)

        else:
            raise SendError('Error, to must be specified.')

        if hasattr(self, '__cc_line'):
            json_cc = jsonify_receps(self.__getattribute__('__cc_line'), "cc", False)

        else:
            json_cc = None

        if hasattr(self, '__bcc_line'):
            json_bcc = jsonify_receps(self.__getattribute__('__bcc_line'), "bcc", False)

        else:
            json_bcc = None

        if hasattr(self, 'subject'):
            json_send += 'Subject": "' + self.subject + '",'
        else:
            raise SendError('Error, subject must be specified.')

        # now we can set the body
        json_send += '"Body": { "ContentType": "HTML", "Content": "' + self.body + '"}'
        # set the recipients
        json_send += ',' + json_to + ']'

        if json_cc is not None:
            json_send += ',' + json_cc + ']'

        if json_bcc is not None:
            json_send += ',' + json_bcc + ']'

        if hasattr(self, '__send_as'):
            json_send += ',"From":{ "EmailAddress": { "Address": "' + self.__send_as + '" } }'

        if type(self.__file_bytes) is not None:
            if self.__file_name is not None and self.__file_extension is not None:
                full_file_name = str(self.__file_name) + '.' + str(self.__file_extension)
                json_send += ',"Attachments": [ { "@odata.type": "#Microsoft.OutlookServices.FileAttachment", ' \
                             '"Name": "' + full_file_name + '", "ContentBytes": "' + self.__file_bytes + '" } ]'

        json_send += '}}'

        headers = {"Authorization": "Bearer " + self.__access_token, "Content-Type": "application/json"}
        r = requests.post('https://outlook.office.com/api/v1.0/me/sendmail', headers=headers, data=json_send)
        if r.status_code != 202:
            raise MiscError('Did not receive status code 202 from Outlook REST Endpoint. Ensure that your access token '
                            'is current. STATUS CODE: ' + str(r.status_code) + '. RESPONSE: ' + r.content)

        ###
        # Get and Set Functions
        ###

    def set_subject(self, subject):
        self.subject = subject
        return self

    def set_body(self, body):
        self.body = body
        return self

    def to(self, recipients):
        self.__setattr__('__to_line', recipients)
        return self

    def cc(self, recipients):
        self.__setattr__('__cc_line', recipients)
        return self

    def bcc(self, recipients):
        self.__setattr__('__bcc_line', recipients)
        return self

    def send_as(self, email):
        self.__setattr__('__send_as', email)
        return self

    def add_attachment(self, file_bytes, file_name, file_extension):
        self.__file_bytes = file_bytes
        self.__file_name = file_name
        self.__file_extension = file_extension
        return self

    def send(self):
        self.__send_email()
