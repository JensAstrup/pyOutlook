class OutlookError(Exception):
    """Base exception class for all pyOutlook errors.

    :param value: Optional error message or value.
    :type value: str or None

    :ivar value: The error message or value.
    """

    def __init__(self, value=None):
        self.value = value


class APIError(OutlookError):
    """Base class for errors received from the Outlook API.

    All API-related exceptions inherit from this class, allowing you to catch
    all API errors with a single except clause.
    """


class AuthError(APIError):
    """Raised when Outlook returns a 401 or 403 status code.

    This typically indicates an expired or invalid access token.

    :param value: Optional error message. If not provided, a default message is used.
    :type value: str or None

    :ivar value: The error message.
    """

    def __init__(self, value=None):
        if value is None:
            self.value = 'Access Token Error, double check your access token.'
        else:
            self.value = value


class RequestError(APIError):
    """Raised when Outlook returns a 400 status code.

    This indicates a bad request, typically due to invalid parameters.

    :param value: The error message from the API.
    :type value: str or None

    :ivar value: The error message.
    """

    def __init__(self, value=None):
        self.value = value


class MiscError(OutlookError):
    """Raised for miscellaneous errors not covered by other exception types.

    :param value: The error message.
    :type value: str

    :ivar value: The error message.
    """

    def __init__(self, value):
        self.value = value
