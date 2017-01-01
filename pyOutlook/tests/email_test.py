import unittest
import time
from pyOutlook.tests.config import AUTH_TOKEN, EMAIL_ACCOUNT
from pyOutlook.core.main import OutlookAccount
from pyOutlook.core.message import Message


class Read(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        account = OutlookAccount(AUTH_TOKEN)
        # Send a test email that we can refer to
        cls.email_one_subject = 'Test Subject4'
        account.send_email('Test Body', cls.email_one_subject, [EMAIL_ACCOUNT])
        cls.account = account

        # Delay for a bit so that the email is in the inbox for our tests
        time.sleep(8)

    def test_inbox(self):
        """
        Test that the email is in the inbox
        """
        inbox = self.account.get_inbox()
        email_subjects = [x.subject for x in inbox]
        self.assertTrue(self.email_one_subject in email_subjects)

    def test_move_to_deleted(self):
        """
        Test that the email can be moved to, and retrieved from, the deleted items folder
        """
        inbox = self.account.get_inbox()
        # Filter to our email
        email = [email for email in inbox if email.subject == self.email_one_subject]

        # Move to deleted
        email[0].move_to_deleted()

        # Retrieve deleted items folder
        deleted = self.account.get_deleted_messages()
        email_subjects = [x.subject for x in deleted]

        self.assertTrue(self.email_one_subject in email_subjects)

        # Move back to inbox for further testing
        email = [email for email in deleted if email.subject == self.email_one_subject]
        email[0].move_to_inbox()

    def test_move_to_drafts(self):
        """
        Test that the email can be moved to, and retrieved from, the drafts folder
        """
        inbox = self.account.get_inbox()
        email = [email for email in inbox if email.subject == self.email_one_subject]

        email[0].move_to_drafts()


if __name__ == '__main__':
    unittest.main()
