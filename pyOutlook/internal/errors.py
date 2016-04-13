class AuthError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class SendError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class MiscError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

