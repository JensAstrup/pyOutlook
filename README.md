[![PyPI version](https://badge.fury.io/py/pyOutlook.svg)](https://badge.fury.io/py/pyOutlook)
[![coverage report](https://gitlab.com/jensastrup/pyOutlook/badges/master/coverage.svg)](https://gitlab.com/jensastrup/pyOutlook/commits/master)

[![PyPI](https://img.shields.io/pypi/pyversions/pyOutlook.svg?maxAge=2592000)]()
[![Documentation Status](https://readthedocs.org/projects/pyoutlook/badge/?version=latest)](http://pyoutlook.readthedocs.io/en/latest/?badge=latest)

# Maintained on GitLab
This project is maintained on [GitLab](https://gitlab.com/jensastrup/pyOutlook) and mirrored to [GitHub](https://github.com/JensAstrup/pyOutlook). Issues opened on the latter are still addressed.

# pyOutlook
A Python module for connecting to the Outlook REST API, without the hassle of dealing with the JSON formatting for requests/responses and the REST endpoints and their varying requirements

The most up to date documentation can be found on [pyOutlook's RTD page](http://pyoutlook.readthedocs.io/en/latest/).

## Instantiation
Before anything can be retrieved or sent, an instance of  OutlookAccount must be created. 
The only parameter required is the access token for the account. 

Note that this module does not handle the OAuth process, gaining an access token must be done outside of this module.

```python
from pyOutlook import *

token = 'OAuth Access Token Here'
my_account = OutlookAccount(token)

# If our token is refreshed, or to ensure that the latest token is saved prior to calling a method. 
my_account.access_token = 'new access token'
```


## Retrieving Messages

### get_messages()
This method retrieves the five most recent emails, returning a list of Message objects.
You can optionally specify the page of results to retrieve - 1 is the default. 
```python
from pyOutlook import *
account = OutlookAccount('')
account.get_messages()
account.get_messages(2)
```

### get_message(message_id)
This method retrieves the information for the message matching the id provided
```python
from pyOutlook import *
account = OutlookAccount('')

email = account.get_message('message_id')
print(email.body)
```

### inbox()
This method is identical to get_messages(), however it returns only the ten most recent message in the inbox (ignoring messages that were put into seperate folders by an Outlook rule, junk email, etc)

```python
from pyOutlook import *
account = OutlookAccount('')

account.inbox()
```
Identical methods for additional folders: `sent_messages()`, `deleted_messages()`, `draft_messages()`.

## Interacting with Message objects
Message objects deal with the JSON returned by Outlook, and provide only the useful details. These Messages can be forwarded, replied to, deleted, etc. 

### forward(to_recipients, forward_comment)
This method forwards a message to the list of recipients, along with an optional 'comment' which is sent along with the message. The forward_comment parameter can be left blank to just forward the message.
```python
from pyOutlook import *
account = OutlookAccount('')

email = account.get_message('id')
email.forward([Contact('John.Adams@domain.com'), Contact('Nice.Guy@domain.com')])
email.forward(['John.Smith@domain.com'], 'Read the message below')
```

### reply(reply_comment)
This method allows you to respond to the sender of an email with a comment appended. 
```python
from pyOutlook import *
account = OutlookAccount('')

email = account.get_message(id)
email.reply('That was a nice email Lisa')
```
### reply_all(reply_comment)
This method allows you to respond to all recipients an email with a comment appended. 
```python
from pyOutlook import *
account = OutlookAccount('')

email = account.get_message(id)
email.reply_all('I am replying to everyone, which will likely annoy 9/10 of those who receive this')
```
### move_to*
You can move a message from one folder to another via several methods. 
For default folders, there are specific methods - for everything else there is a method to move 
to a folder designated by its id - or you can pass a ```Folder``` instance. 
```python
from pyOutlook import *
account = OutlookAccount('')

message = Message()

message.move_to_inbox()
message.move_to_deleted()
message.move_to_drafts()
message.move_to('my_folder_id')

folders = account.get_folders()

message.move_to(folders[0])
```
### delete()
Deletes the email. Note that the email will still exist in the user's 'Deleted Items' folder. 
```python
from pyOutlook import *
account = OutlookAccount('')

message = account.inbox()[0]

message.delete()
```
## Sending Emails
There are a couple of ways to create new emails. You can either use ``new_email()`` to get a ``Message()``
instance, which you can alter before sending. Alternatively, you can use ``send_email()`` where you pass in 
commonly used parameters and the email gets sent once called.

Example:
```python
from pyOutlook import *
account = OutlookAccount('')

test_email = account.new_email('This is a test body. <br> Best, <br> John Smith', 'This is a test subject', [Contact('anEmailAccount@gmail.com')])
test_email.attach('FILE_BYTES_HERE', 'FileName.pdf')
test_email.send()
```
Or:
```python
from pyOutlook import *
account = OutlookAccount('')

account.send_email(
"I'm sending an email through Python. <br> Best, <br> Me",
'A subject',
to=['myemail@domain.com'],
# or to=[Contact('myemail@domain.com']
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
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folders()[0]
print(folder.name)
>>> 'Inbox'
```
### get_folder_by_id(folder_id)
If you have the id of a folder, you can get a Folder object for it with this method
```python
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folder_by_id('id')
print(folder.name)
>>> 'My Folder'
```
Note that you can replace the folder ID parameter with the name of a 'well known' folder such as: 'Inbox', 'Drafts', SentItems', and 'DeletedItems'
```python
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folder_by_id('Drafts')
print(folder.name)
>>> 'Drafts'
```
## The Folder Object

### rename(new_folder_name)
This method renames the folder object in Outlook, and returns a new Folder object 
representing that folder.
``` 
from pyOutlook import *
account = OutlookAccount('')

folder = my_account.get_folders()[0]
folder = folder.rename('My New Folder v2')
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

### delete()
Self-explanatory, deletes the provided folder in Outlook
```python
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folders()[0]
folder.delete()
# and now it doesn't exist
```

### move_into(destination_folder)
Move the Folder provided into a new folder. 

```python
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folders()[0]
folder_1 = account.get_folders()[1]

folder.move_into(folder_1)
```

### copy(destination_folder)
Copies the folder and its contents to the designated folder which can be either a folder ID or well known folder name.
```python
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folders()[0]
folder_1 = account.get_folders()[1]

folder.copy_into(folder_1)
```

### create_child_folder(new_folder_name)
This creates a [folder within a folder](http://dab1nmslvvntp.cloudfront.net/wp-content/uploads/2014/03/1394332737Go-Deeper-Inception-Movie.jpg), with a title provided in the `new_folder_name` argument.
```python
from pyOutlook import *
account = OutlookAccount('')

folder = account.get_folders()[0]
new_folder = folder.create_child_folder('New Folder')
new_folder.unread_count
>>> 0
```
