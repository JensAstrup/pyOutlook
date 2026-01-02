class OutlookError(Exception):
    def __init__(self, value=None):
        self.value = value


class APIError(OutlookError):
    """ Any error received from the Outlook API """


class AuthError(APIError):
    """ Raised when Outlook returns a 401 or 403, generally caused by expired or invalid access tokens """
    def __init__(self, value=None):
        if value is None:
            self.value = 'Access Token Error, double check your access token.'
        else:
            self.value = value


class RequestError(APIError):
    """ Raised from 400 response status codes"""
    def __init__(self, value=None):
        self.value = value


class MiscError(OutlookError):
    def __init__(self, value):
        self.value = value
