import re

from pyOutlook.internal.errors import AuthError, RequestError, APIError


def get_valid_filename(s: str) -> str:
    """Return a sanitized filename safe for filesystem use.

    Removes leading and trailing spaces, converts other spaces to underscores,
    and removes any characters that are not alphanumeric, dash, underscore, or dot.

    Adapted from Django's ``django.utils.text.get_valid_filename``.

    :param s: The string to convert to a valid filename.
    :type s: str

    :returns: A sanitized filename string.
    :rtype: str

    Example::

        >>> get_valid_filename("john's portrait in 2004.jpg")
        'johns_portrait_in_2004.jpg'
    """
    s = str(s).strip().replace(' ', '_')
    return re.sub(r'(?u)[^-\w.]', '', s)


def get_response_data(response) -> dict | str:
    """Extract data from a requests Response object.

    Attempts to parse the response as JSON, falling back to text if JSON
    parsing fails.

    :param response: A requests Response object.

    :returns: The response data as a dictionary (if JSON) or string (if text).
    :rtype: dict or str
    """
    try:
        return response.json()
    except ValueError:
        return response.text


def check_response(response) -> bool:
    """Check that an API response is successful.

    Validates the HTTP status code and raises appropriate exceptions for
    error responses.

    :param response: A requests Response object.

    :returns: ``True`` if the response indicates success (status 100-299).
    :rtype: bool

    :raises AuthError: If the status code is 401 or 403.
    :raises RequestError: If the status code is 400.
    :raises APIError: For any other error status code.
    """
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
