# pyOutlook
A Python module for connecting to the Outlook REST API, without the hassle of dealing with the JSON formatting for requests/responses and the REST endpoints and their varying requirements

## Methods
All current methods available, with descriptions, parameters, and examples.

#### Instantiation
Creating the object: Before anything can be retrieved or sent, the OutlookAccount object must be created. The only parameter required is the access token for the account. This can be changed later with the method ```set_access_token(token_input)``` where 'token_input' is the OAuth Access token you receive from Outlook. Note that this module does not handle the OAuth process, gaining an access token must be done outside of this module.

```python
token = 'OAuth Access Token Here'
new_token = 'OAuth Access Token2 Here'
my_account = pyOutlook.OutlookAccount(token)
# If our token is refreshed, or to ensure that the latest token is saved prior to calling a method. 
my_account = my_account.set_access_token(new_token)
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
email_id = get_messages()[0]
get_email = my_account.get_message(email_id)
print get_email.body
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
test_email.to('anEmailAccount@gmail.com').set_subject('This is a test subject').set_body('This is a test body. <br> Best, <br> John Smith').add_attachment('FILE_BYTES_HERE', 'FileName', 'pdf').send()
