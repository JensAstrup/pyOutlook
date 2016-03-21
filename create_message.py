from types import *
import requests
from internal_methods import jsonify_receps
from internal_methods import MiscError


class SendError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class Message(object):
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
            json_to = jsonify_receps(self.__getattribute__('__to_line'), "to")

        else:
            raise SendError('Error, to must be specified.')

        if hasattr(self, '__cc_line'):
            json_cc = jsonify_receps(self.__getattribute__('__cc_line'), "cc")

        else:
            json_cc = None

        if hasattr(self, '__bcc_line'):
            json_bcc = jsonify_receps(self.__getattribute__('__bcc_line'), "bcc")

        else:
            json_bcc = None

        if hasattr(self, 'subject'):
            json_send += 'Subject": "' + self.subject + '",'
        else:
            raise SendError('Error, subject must be specified.')

        # now we can set the body
        json_send += '"Body": { "ContentType": "HTML", "Content": "' + self.body + '"}'
        # set the receipients
        json_send += ',' + json_to + ']'

        if type(json_cc) is not NoneType:
            json_send += ',' + json_cc + ']'

        if type(json_bcc) is not NoneType:
            json_send += ',' + json_bcc + ']'

        if hasattr(self, '__send_as'):
            json_send += ',"From":{ "EmailAddress": { "Address": "' + self.__send_as + '" } }'

        if type(self.__file_bytes) is not NoneType:
            if self.__file_name is not NoneType and self.__file_extension is not NoneType:
                full_file_name = str(self.__file_name) + '.' + str(self.__file_extension)
                json_send += ',"Attachments": [ { "@odata.type": "#Microsoft.OutlookServices.FileAttachment", ' \
                             '"Name": "' + full_file_name + '", "ContentBytes": "' + self.__file_bytes + '" } ]'

        json_send += '}}'

        headers = {"Authorization": "Bearer " + self.__access_token, "Content-Type": "application/json"}
        r = requests.post('https://outlook.office.com/api/v1.0/me/sendmail', headers=headers, data=json_send)
        if r.status_code != 202:
            raise MiscError('Did not receive status code 202 from Outlook REST Endpoint. Ensure that your access token '
                            'is current. STATUS CODE: ' + str(r.status_code))

###
# Get and Set Functions
###

    def set_subject(self, subject):
        self.subject = subject
        return self

    def set_body(self, body):
        self.body = body
        return self

    def to(self, receipients):
        receps = receipients.split(',')

        for num in range(len(receps)):
            receps[num] = receps[num].strip()

        self.__setattr__('__to_line', receps)
        return self

    def cc(self, receipients):
        receps = receipients.split(',')

        for num in range(len(receps)):
            receps[num] = receps[num].strip()

        self.__setattr__('__cc_line', receps)
        return self

    def bcc(self, receipients):
        receps = receipients.split(',')

        for num in range(len(receps)):
            receps[num] = receps[num].strip()

        self.__setattr__('__bcc_line', receps)
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

        # pyOutlook
A Python module for connecting to the Outlook REST API, without the hassle of dealing with the JSON formatting for requests/responses and the REST endpoints and their varying requirements

## Methods
All current methods available, with descriptions, parameters, and examples.

#### Instantiation
Creating the object: Before anything can be retrieved or sent, the OutlookAccount object must be created. Following that, the access token should be provided using ```set_access_token(token_input)``` where 'token_input' is the OAuth Access token you receive from Outlook. Note that this module does not handle the OAuth process, gaining an access token must be done outside of this module.

```python
token = 'OAuth Access Token Here'
my_account = pyOutlook.OutlookAccount()
my_account = my_account.set_access_token(token)
```
### Retrieving Messages

#### get_messages()
This method retrieves the five most recent emails, returning the message IDs for each.
```python
my_account.get_messages()
```
#### get_message(message_id)
This method retrieves the information for the message matching the id provided
```python
get_email = my_account.get_messages()
print get_email[0].body
```
Sample Output
```
This is a test message body. <br> Best, <br> John Smith
```
#### get_inbox()
This method is identical to get_messages(), however it returns only the five most recent message in the inbox (ignoring messages that were put into seperate folders by an Outlook rule, junk email, etc)

```python
my_account.get_inbox()
```

### Sending Emails
After creating an email object, there are several methods which can be (or must be) used prior to sending which allow you to specify various pieces of the message to be sent ranging from the subject to attachments.

Example:
```python
test_email = my_account.new_email
test_email.to('anEmailAccount@gmail.com).set_subject('This is a test subject').set_body('This is a test body. <br> Best, <br> John Smith').add_attachment('FILE_BYTES_HERE', 'FileName', 'pdf'
