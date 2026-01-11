Quick Start
===========

Instantiation
-------------

pyOutlook interacts with Outlook messages and folders through the class OutlookAccount(). The OutlookAccount acts as a gatekeeper
to the other methods available, and stores the access token associated with an account.

Instantiation Example::

    from pyOutlook import OutlookAccount
    account_one = OutlookAccount('token 1')
    account_two = OutlookAccount('token 2')

From here you can access any of the methods as documented in the :ref:`pyOutlook <pyOutlook>` section. Here are examples of accessing
an inbox and sending a new email.

Examples
--------

Retrieving Emails
^^^^^^^^^^^^^^^^^
Through the OutlookAccount class you can access the messages service, which provides methods like :code:`all()`, :code:`get()`, and :code:`from_folder()`.
The OutlookAccount also provides convenience methods like :code:`inbox()`, :code:`sent_messages()`, etc.
These methods return a list of :ref:`MessageAnchor` objects, allowing you to access the attributes therein.

::

    # Get inbox messages
    inbox = account.inbox()
    inbox[0].body
    >>> 'A very fine body'

    # Get all messages (paginated)
    messages = account.messages.all()
    messages = account.messages.all(page=2)  # Get page 2

    # Get a specific message by ID
    message = account.messages.get('message_id')
    print(message.subject)

    # Get messages from a specific folder
    drafts = account.messages.from_folder('Drafts')

Sending Emails
^^^^^^^^^^^^^^
You can send emails through the MessageService accessed via :code:`account.messages.send()`. This method takes all 
arguments upfront and immediately sends the email.

::

    from pyOutlook import OutlookAccount, Contact

    account = OutlookAccount('token')
    
    # Send a simple email
    account.messages.send(
        subject='Hey there',
        body="I'm sending an email through Python. <br> Best, <br> Me",
        to=['myemail@domain.com']
    )

    # Send with Contact objects and CC/BCC
    account.messages.send(
        subject='Project Update',
        body='<p>Here is the latest update on the project.</p>',
        to=[Contact('colleague@domain.com', name='Colleague Name')],
        cc=['manager@domain.com'],
        bcc=['archive@domain.com']
    )

Note that HTML formatting is accepted in the message body.

Sending with Attachments
"""""""""""""""""""""""""
To send attachments, create :class:`Attachment <pyOutlook.core.attachment.Attachment>` objects and pass them to the send method.

::

    import base64
    from pyOutlook import OutlookAccount, Attachment

    account = OutlookAccount('token')
    
    # Read file and encode to base64
    with open('document.pdf', 'rb') as f:
        content = base64.b64encode(f.read()).decode('utf-8')
    
    attachment = Attachment('document.pdf', content, content_type='application/pdf')
    
    account.messages.send(
        subject='Document Attached',
        body='<p>Please find the document attached.</p>',
        to=['recipient@domain.com'],
        attachments=[attachment]
    )

Contacts
^^^^^^^^
All recipients, and the sender attribute, in :class:`Messages <pyOutlook.core.message.Message>` are represented by
:class:`Contacts <pyOutlook.core.contact.Contact>`. This allows you to retrieve the name of a recipient,
if provided by Outlook.

::

    message = account.inbox()[0]
    message.sender.name
    >>> 'Dude'
    message.sender.email
    >>> 'dude@example.com'

When providing recipients to send methods, you can provide them either as a list
of strings, or a list of :class:`Contacts <pyOutlook.core.contact.Contact>`.

::

    from pyOutlook import Contact

    # Using email strings
    account.messages.send(
        subject='Hello',
        body='<p>Hi there</p>',
        to=['user1@example.com', 'user2@example.com']
    )

    # Using Contact objects
    account.messages.send(
        subject='Hello',
        body='<p>Hi there</p>',
        to=[
            Contact('user1@example.com', name='User One'),
            Contact('user2@example.com', name='User Two')
        ]
    )

Folders
^^^^^^^
You can retrieve and manage folders through the FolderService accessed via :code:`account.folders`.

::

    from pyOutlook import OutlookAccount

    account = OutlookAccount('token')

    # Get all folders
    folders = account.folders.all()
    for folder in folders:
        print(f'{folder.name}: {folder.unread_count} unread')

    # Get a specific folder by ID or well-known name
    inbox_folder = account.folders.get('Inbox')
    custom_folder = account.folders.get('folder_id_here')

    # Folder operations are methods on the Folder object
    subfolder = inbox_folder.create_child_folder('Archive 2024')
    inbox_folder.rename('My Inbox')
