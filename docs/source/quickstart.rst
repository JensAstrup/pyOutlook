Quick Start
===========

Instantiation
-------------

pyOutlook interacts with Outlook messages and folders through the class OutlookAccount(). The OutlookAccount acts as a gatekeeper
to the other methods available, and stores the access token associated with an account.

Instantiation Example::

    account_one = pyOutlook.OutlookAccount('token 1')
    account_two = pyOutlook.OutlookAccount('token 2')

From here you can access any of the methods as documented in the 'pyOutlook' section. Here are two examples of accessing
an inbox and sending a new email.

Examples
--------

Retrieving Emails
^^^^^^^^^^^^^^^^^
Through the OutlookAccount class you can call one of many methods - get_messages(), get_inbox(), etc.
These methods return a list of :ref:`MessageAnchor` objects, allowing you to access the atrributes therein.
::
    inbox = account_one.get_inbox()
    print(inbox[0].body)

Sending Emails
^^^^^^^^^^^^^^
As above, you can send emails through the OutlookAccount class. There are two methods for sending emails - one allows
chaining of methods and the other takes all arguments upfront and immediately sends.

new_email()
"""""""""""
This returns a :ref:`NewMessageAnchor` object which allows for chaining methods. The full list of available methods is documented
under the NewMessage class.

::

    email = account_one.new_email()
    email.to('myemail@domain.com').set_subject('Hey there').set_body('I\'m sending an email through Python. <br> Best, <br>
    Me').send()

Note that HTML formatting is accepted in the message body.


send_email()
""""""""""""
This `method <pyOutlook.html#pyOutlook.core.main.OutlookAccount.send_email>`_ takes all of its arguments at once and then
sends.

::

    account_one.send_email(
    to=['myemail@domain.com'],
    subject='Hey there',
    body='I\'m sending an email through Python. <br> Best, <br> Me',
    )

