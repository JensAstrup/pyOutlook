import re

from pyOutlook.internal.errors import AuthError, RequestError, APIError


def get_valid_filename(s):
    """
    Shamelessly taken from Django.
    https://github.com/django/django/blob/master/django/utils/text.py

    Return the given string converted to a string that can be used for a clean
    filename. Remove leading and trailing spaces; convert other spaces to
    underscores; and remove anything that is not an alphanumeric, dash,
    underscore, or dot.
    >>> get_valid_filename("john's portrait in 2004.jpg")
    'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def get_response_data(response):
    """ Handles getting response data from the requests module where .json() can raise an error """
    try:
        return response.json()
    except ValueError:
        return response.content


def check_response(response):
    """ Checks that a response is successful, raising the appropriate Exceptions otherwise. """
    status_code = response.status_code

    if 100 < status_code < 299:
        return True

    elif status_code == 401 or status_code == 403:
        message = get_response_data(response)
        raise AuthError('Access Token Error, Received ' + str(status_code) +
                        ' from Outlook REST Endpoint with the message: {}'.format(message))

    elif status_code == 400:
        message = get_response_data(response)
        raise RequestError('The request made to the Outlook API was invalid. Received the following message: {}'.
                           format(message))
    else:
        message = get_response_data(response)
        raise APIError('Encountered an unknown error from the Outlook API: {}'.format(message))