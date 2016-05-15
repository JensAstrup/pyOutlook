import pytest
import sys
from pyOutlook.core import main as pyoutlook
from pyOutlook.internal.errors import MiscError


def pytest_addoption(parser):
    parser.addoption("--token", action="store", default="type1", help="my option: type1 or type2")


@pytest.fixture
def cmdopt(request):
    return request.config.getoption("--token")


def get_email():
    emails = account.get_messages()

    assert isinstance(emails[0].sender_email, str)


def send_email():
    body = 'This is \\n <br> an email'
    subject = 'test subject'
    to = ['jensaiden@gmail.com']
    account.send_email(body=body, subject=subject, to=to)
    # email.to('py-test@outlook.com').set_subject('Test PyOutlook Email').set_body('Test / } \n Body').send()


if __name__ == '__main__':
    token = input('token: ')
# def test_all(token):
    global account
    account = pyoutlook.OutlookAccount(token)
    get_email()
    assert(send_email() is not MiscError)
