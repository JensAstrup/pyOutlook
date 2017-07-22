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

From here you can access any of the methods as documented in the :ref:`pyOutlook <pyOutlook>` section. Here are two examples of accessing
an inbox and sending a new email.

Examples
--------

Retrieving Emails
^^^^^^^^^^^^^^^^^
Through the OutlookAccount class you can call one of many methods - :code:`get_messages()`, :code:`inbox()`, etc.
These methods return a list of :ref:`MessageAnchor` objects, allowing you to access the attributes therein.
::
    inbox = account.inbox()
    inbox[0].body
    >>> 'A very fine body'

Sending Emails
^^^^^^^^^^^^^^
As above, you can send emails through the OutlookAccount class. There are two methods for sending emails - one allows
chaining of methods and the other takes all arguments upfront and immediately sends.


Message
"""""""
You can create an instance of a :class:`Message <pyOutlook.core.message.Message>` and then send from there.

::

    from pyOutlook import *
    # or from pyOutlook.core.message import Message

    account = OutlookAccount('token')
    message = Message(account, 'A body', 'A subject', [Contact('to@email.com')])
    message.attach(bytes('some bytes', 'utf-8'), 'bytes.txt')
    message.send()


new_email()
"""""""""""
This returns a :class:`Message <pyOutlook.core.message.Message>` instance.

::

    body = 'I\'m sending an email through Python. <br> Best, <br>Me'

    email = account.new_email(body=body, subject='Hey there', to=Contact('myemail@domain.com'))
    email.sender = Contact('some_other_account@email.com')
    email.send()

Note that HTML formatting is accepted in the message body.


send_email()
""""""""""""
This `method <pyOutlook.html#pyOutlook.core.main.OutlookAccount.send_email>`_ takes all of its arguments at once and then
sends.

::

    account_one.send_email(
        to=[Contact('myemail@domain.com')],
        # or to=['myemail@domain.com')]
        subject='Hey there',
        body="I'm sending an email through Python. <br> Best, <br> Me",
    )

::

Contacts
^^^^^^^^
All recipients, and the sender attribute, in :class:`Messages <pyOutlook.core.message.Message>` are represented by
:class:`Contacts <pyOutlook.core.contact.Contact>`. Right now, this allows you to retrieve the name of a recipient,
if provided by Outlook.

::

    message = account.inbox()[0]
    message.sender.name
    >>> 'Dude'

When providing recipients to :class:`Message <pyOutlook.core.message.Message>` you can provide them either as a list
of strings, or a list of :class:`Contacts <pyOutlook.core.contact.Contact>`. I prefer the latter, as there are further
options in the Outlook API for interacting with Contacts - functionality for those may be added in the future.