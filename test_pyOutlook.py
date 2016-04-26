import pytest
from pyOutlook.core import main as pyoutlook
from pyOutlook.internal.errors import MiscError
global account


def pytest_addoption(parser):
    parser.addoption("--token", action="store", default="type1", help="my option: type1 or type2")

@pytest.fixture
def cmdopt(request):
    return request.config.getoption("--cmdopt")

def get_email():
    emails = account.get_messages()

    assert isinstance(emails[0].sender_email, str)


def send_email():
    email = account.new_email()
    email.to('py-test@outlook.com').set_subject('Test PyOutlook Email').set_body('Test Body').send()


# if __name__ == '__main__':
def test_all(token):
    global account
    account = pyoutlook.OutlookAccount(token)
    get_email()
    assert(send_email() is not MiscError)
