[![PyPI version](https://badge.fury.io/py/pyOutlook.svg)](https://badge.fury.io/py/pyOutlook)
[![Code Health](https://landscape.io/github/JensAstrup/pyOutlook/master/landscape.svg?style=flat)](https://landscape.io/github/JensAstrup/pyOutlook/master)
[![coverage report](https://gitlab.com/jensastrup/pyOutlook/badges/master/coverage.svg)](https://gitlab.com/jensastrup/pyOutlook/commits/master)

[![PyPI](https://img.shields.io/pypi/status/pyOutlook.svg?maxAge=2592000)]()
[![PyPI](https://img.shields.io/pypi/pyversions/pyOutlook.svg?maxAge=2592000)]()
[![Documentation Status](https://readthedocs.org/projects/pyoutlook/badge/?version=latest)](http://pyoutlook.readthedocs.io/en/latest/?badge=latest)

# Maintained on GitLab
This project is maintained on [GitLab](https://gitlab.com/jensastrup/pyOutlook) and mirrored to [GitHub](https://github.com/JensAstrup/pyOutlook). Issues opened on the latter are still addressed.

# pyOutlook
A Python module for connecting to the Outlook REST API, without the hassle of dealing with the JSON formatting for requests/responses and the REST endpoints and their varying requirements

The most up to date documentation can be found on [pyOutlook's pypi docs page](http://pythonhosted.org/pyOutlook).

## Instantiation
Creating the object: Before anything can be retrieved or sent, the OutlookAccount object must be created. The only parameter required is the access token for the account. This can be changed later with the method ```set_access_token(token_input)``` where 'token_input' is the OAuth Access token you receive from Outlook. Note that this module does not handle the OAuth process, gaining an access token must be done outside of this module.

```python
token = 'OAuth Access Token Here'
new_token = 'OAuth Access Token2 Here'
my_account = pyOutlook.OutlookAccount(token)
# If our token is refreshed, or to ensure that the latest token is saved prior to calling a method. 
my_account = my_account.set_access_token(new_token)
```


## Retrieving Messages

### get_messages()
This method retrieves the five most recent emails, returning a list of Message objects. 
```python
my_account.get_messages()
```
### get_more_messages(page)
This method returns additional messages, allowing you to select which page you'd like to pull. Note that get_messages() is page 1. This returns a list of Message objects as well.
```python
my_account.get_more_messages(5)
```
### get_message(message_id)
This method retrieves the information for the message matching the id provided
```python
email_id = get_messages()[0]
get_email = my_account.get_message(email_id)
print(get_email.body)
```
Sample Output
```
This is a test message body. <br> Best, <br> John Smith
```
### inbox()
This method is identical to get_messages(), however it returns only the ten most recent message in the inbox (ignoring messages that were put into seperate folders by an Outlook rule, junk email, etc)

```python
my_account.inbox()
```
Identical methods for additional folders: `sent_messages()`, `deleted_messages()`, `draft_messages()`.

## Interacting with Message objects
Message objects deal with the JSON returned by Outlook, and provide only the useful details. These Messages can be forwarded, replied to, deleted, etc. 

### forward_message(to_recipients, forward_comment)
This method forwards a message to the list of recipients, along with an optional 'comment' which is sent along with the message. The forward_comment parameter can be left blank to just forward the message.
```python
email = my_account.get_message(id)
email.forward_message('John.Adams@domain.com, Nice.Guy@domain.com')
email.forward_message('John.Smith@domain.com', 'Read the message below')
```

### reply(reply_comment)
This method allows you to respond to the sender of an email with a comment appended. 
```python
email = my_account.get_message(id)
email.reply('That was a nice email Lisa')
```
### reply_all(reply_comment)
This method allows you to respond to all recipients an email with a comment appended (use this wisely). 
```python
email = my_account.get_message(id)
email.reply_all('I am replying to everyone, which will likely annoy 9/10 of those who receive this')
```
### move_to*
You can move a message from one folder to another via several methods. For default folders, there are specific methods - for everything else there is a method to move to a folder designated by its id. 
```python
message.move_to_ibox()
message.move_to_deleted()
message.move_to_drafts()
message.move_to(my_folder_id)
```
### delete_message()
Deletes the email. Note that the email will still exist in the user's 'Deleted Items' folder. 
```python
message.delete_message()
```
## Sending Emails
After creating an email object, there are several methods which can be (or must be) used prior to sending which allow you to specify various pieces of the message to be sent ranging from the subject to attachments.

Example:
```python
test_email = my_account.new_email()
test_email.to('anEmailAccount@gmail.com').set_subject('This is a test subject').set_body('This is a test body. <br> Best, <br> John Smith').add_attachment('FILE_BYTES_HERE', 'FileName', 'pdf').send()
```
Alternatively, you can send an email with one method instead of chaining:
```python
account_one.send_email(
to=['myemail@domain.com'],
subject='Hey there',
body='I\'m sending an email through Python. <br> Best, <br> Me',
)
```
## Folders
Folders can be created, retrieved, moved, copied, renamed, and deleted. You can also retrieve child folders that are nested within another folder. All Folder objects contain the folder ID, the folder name, the folder's unread count, the number of child folders within it, and the total items inside the folder. 

### 'Well Known' Folders
Folder ID parameters can be replaced with the following strings where indicated:
'Inbox', 'Drafts', 'SentItems', or 'DeletedItems'

### get_folders()
This methods returns a list of Folder objects representing each folder in the user's account. 
```python
folder = my_account.get_folders()[0]
folder.name
>>> 'Inbox'
```
### get_folder(folder_id)
If you have the id of a folder, you can get a Folder object for it with this method
```python
folder = my_account.get_folder(the_folder_id)
folder.name
>>> 'My Folder'
```
Note that you can replace the folder ID parameter with the name of a 'well known' folder such as: 'Inbox', 'Drafts', SentItems', and 'DeletedItems'
```python
folder = my_account.get_folder('Drafts')
folder.name
>>> 'Drafts'
```

## The Folder Object

### rename_folder(new_folder_name)
This method renames the folder object in Outlook, and returns a new Folder object representing that folder.
```python 
folder = my_account.get_folder('My Folder')
folder = folder.rename_folder('My New Folder v2')
folder.name
>>> 'My New Folder v2'
```

### get_subfolders()
Returns a list of Folder objects, representing all child Folders within the Folder provided. 
```python 
for subfolder in folder.get_subfolders():
  print(subfolder.name)

>>> 'My New Folder v2'
>>> 'Some Other Folder'
```

### delete_folder()
Self-explanatory, deletes the provided folder in Outlook
```python
folder.delete_folder()
# and now it doesn't exist
```

### move_folder(destination_folder)
Move the Folder provided into a new folder. The new folder parameter can either be a folder id, or a 'well known' folder name. 
```python
folder.move_folder('Drafts')
folder1.move_folder(folder_id)
```

### copy_folder(destination_folder)
Copies the folder and its contents to the designated folder which can be either a folder ID or well known folder name.

### create_child_folder(new_folder_name)
This creates a [folder within a folder](http://dab1nmslvvntp.cloudfront.net/wp-content/uploads/2014/03/1394332737Go-Deeper-Inception-Movie.jpg), with a title provided in the `new_folder_name` argument.
```python
folder = my_account.get_folders()[0]
new_folder = folder.create_folder('My New Folder')
new_folder.unread_count
>>> 0
```
