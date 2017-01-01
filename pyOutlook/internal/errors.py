class AuthError(Exception):
    def __init__(self, value):
        self.value = value


class SendError(Exception):
    def __init__(self, value):
        self.value = value


class MiscError(Exception):
    def __init__(self, value):
        self.value = value
