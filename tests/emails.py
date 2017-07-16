import base64
import time
import unittest

from pyOutlook.core.main import OutlookAccount
from pyOutlook.core.message import Message
from pyOutlook.internal.errors import AuthError
from tests.config import AUTH_TOKEN, EMAIL_ACCOUNT


class Read(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        account = OutlookAccount(AUTH_TOKEN)
        # Send a test email that we can refer to
        cls.email_one_subject = 'Test Subject4'
        account.send_email('Test Body', cls.email_one_subject, EMAIL_ACCOUNT)
        cls.account = account

        # Delay for a bit so that the email is in the inbox for our tests
        time.sleep(8)

    def test_inbox(self):
        """
        Test that the email is in the inbox
        """
        inbox = self.account.inbox()
        email_subjects = [x.subject for x in inbox]
        self.assertTrue(self.email_one_subject in email_subjects)

    def test_move_to_deleted(self):
        """
        Test that the email can be moved to, and retrieved from, the deleted items folder
        """
        inbox = self.account.inbox()
        # Filter to our email
        email = [email for email in inbox if email.subject == self.email_one_subject]

        # Move to deleted
        email[0].move_to_deleted()

        # Retrieve deleted items folder
        deleted = self.account.deleted_messages()
        email_subjects = [x.subject for x in deleted]

        self.assertTrue(self.email_one_subject in email_subjects)

        # Move back to inbox for further testing
        email = [email for email in deleted if email.subject == self.email_one_subject]
        email[0].move_to_inbox()

    def test_move_to_drafts(self):
        """
        Test that the email can be moved to, and retrieved from, the drafts folder
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]

        email[0].move_to_drafts()

        drafts = self.account.draft_messages()
        email_subjects = [x.subject for x in drafts]

        self.assertTrue(self.email_one_subject in email_subjects)

        # Move back to inbox for further testing
        email = [email for email in drafts if email.subject == self.email_one_subject]
        email[0].move_to_inbox()

    def test_retrieve_message_by_id(self):
        """
        Test that we can retrieve the message ID, and that the message is the correct email
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]
        email_id = email[0].message_id  # type: Message
        retrieved_email = self.account.get_message(email_id)

        self.assertEqual(retrieved_email.subject, self.email_one_subject)

    @classmethod
    def tearDownClass(cls):
        inbox = cls.account.inbox()
        emails = [email for email in inbox if email.subject == cls.email_one_subject]

        for email in emails:
            email.delete_message()


class Delete(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        account = OutlookAccount(AUTH_TOKEN)
        # Send a test email that we can refer to
        cls.email_one_subject = 'Test Subject5'
        account.send_email('Test Body', cls.email_one_subject, EMAIL_ACCOUNT)
        cls.account = account

        # Delay for a bit so that the email is in the inbox for our tests
        time.sleep(8)

    def test_delete_email(self):
        """
        Test that an email can be deleted successfully
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]

        email = email[0]  # type: Message
        email.delete()

    def test_delete_email_deprecation(self):
        """
        Test that an email can be deleted successfully, but that a DeprecationWarning is raised
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]

        email = email[0]  # type: Message
        with self.assertWarns(DeprecationWarning):
            email.delete_message()


class Write(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.account = OutlookAccount(AUTH_TOKEN)
        # Send a test email that we can refer to
        cls.email_one_subject = 'Test Subject5'
        cls.account.send_email('Test Body', cls.email_one_subject, EMAIL_ACCOUNT)

        # Delay for a bit so that the email is in the inbox for our tests
        time.sleep(8)

    @classmethod
    def tearDownClass(cls):
        inbox = OutlookAccount(AUTH_TOKEN).inbox()
        emails = [email for email in inbox if email.subject == 'Test Subject5']

        for email in emails:
            email.delete_message()

    def test_to_field_str_or_list(self):
        """
        Test that an email can be sent with the recipients provided as a list or string
        """
        self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT)
        self.account.send_email('Test body', self.email_one_subject, [EMAIL_ACCOUNT])

        # To field _must_ be a str or list though
        with self.assertRaises(ValueError):
            self.account.send_email('Test body', 'test subject', {'email': EMAIL_ACCOUNT})
            self.account.send_email('Test body', 'test subject', 2)

    def test_cc_field_str_or_list(self):
        """
        Test that an email can be sent with the cc recipients provided as a list or string
        """
        self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT, cc=EMAIL_ACCOUNT)
        self.account.send_email('Test body', self.email_one_subject, [EMAIL_ACCOUNT], cc=[EMAIL_ACCOUNT])

        # To field _must_ be a str or list though
        with self.assertRaises(ValueError):
            self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT, cc={'email': EMAIL_ACCOUNT})

        with self.assertRaises(ValueError):
            self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT, cc=2)

    def test_bcc_field_str_or_list(self):
        """
        Test that an email can be sent with the cc recipients provided as a list or string
        """
        self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT, bcc=EMAIL_ACCOUNT)
        self.account.send_email('Test body', self.email_one_subject, [EMAIL_ACCOUNT], bcc=[EMAIL_ACCOUNT])

        # To field _must_ be a str or list though
        with self.assertRaises(ValueError):
            self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT, bcc={'email': EMAIL_ACCOUNT})

        with self.assertRaises(ValueError):
            self.account.send_email('Test body', self.email_one_subject, EMAIL_ACCOUNT, bcc=2)

    def test_send_attachment_new_email(self):
        email = self.account.new_email()

        email.to(EMAIL_ACCOUNT)
        email.set_subject(self.email_one_subject)
        email.set_body('Attachment body')
        with open('.gitignore', 'rb') as file:
            email.attach(file.read(), 'testattachment', 'txt')

        email.send()

    def test_attachment_parameters_required_new_email(self):
        email = self.account.new_email()

        email.to(EMAIL_ACCOUNT)
        email.set_subject(self.email_one_subject)
        email.set_body('Attachment body')

        with self.assertRaises(TypeError):
            email.attach('testattachment', 'txt').send()

    def test_attachment_send_email(self):
        with self.assertRaises(TypeError):
            self.account.send_email('Attachment body', self.email_one_subject, EMAIL_ACCOUNT,
                                    attachment={'bytes': b'bytes'})

    def test_attachment_parameters_required_send_email(self):
        with open('.gitignore', 'rb') as file:
            self.account.send_email('Attachment body', self.email_one_subject, EMAIL_ACCOUNT,
                                    attachment=dict(bytes=base64.b64encode(file.read()),
                                                    name='testattachment', ext='txt'))

    def test_reply_to_all(self):
        """
        Test that an email can be replied to all
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if 'test' in email.subject.lower()]
        email = email[0]  # type: Message
        email.reply_all('test response')

    def test_reply(self):
        """
        Test that an email can be replied to
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]
        email = email[0]  # type: Message
        email.reply('test response')

    def test_forward(self):
        """
        Test that an email can forwarded
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]
        email = email[0]  # type: Message
        email.forward_message([EMAIL_ACCOUNT])

    def test_forward_with_comment(self):
        """
        Test that an email can forwarded
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]
        email = email[0]  # type: Message
        email.forward_message([EMAIL_ACCOUNT], 'Test comment')

    def test_is_read(self):
        """
        Test that an email's is_read status comes back correctly
        """
        inbox = self.account.inbox()
        email = inbox[0]  # type: Message
        self.assertFalse(email.is_read())

    def test_set_is_read(self):
        """
        Test that an email's is_read status can be set correctly
        """
        inbox = self.account.inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]
        email = email[0]  # type: Message
        email.is_read(True)
        self.assertTrue(email.is_read())


class Exceptions(unittest.TestCase):

    def test_auth_error(self):
        """
        Test that an invalid auth token raises an AuthError
        """
        account = OutlookAccount('NOT A TOKEN')
        with self.assertRaises(AuthError):
            account.inbox()

if __name__ == '__main__':
    unittest.main()
