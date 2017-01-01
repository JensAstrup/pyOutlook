from .errors import MiscError
import functools
import inspect
import warnings
token = 0


def jsonify_recipients(recipient_input, recipient_type, silent):

    json_return = ''
    if not silent:
        if recipient_type == "cc":
            json_return = '"CcRecipients":['
        elif recipient_type == "to":
            json_return = '"ToRecipients":['
        elif recipient_type == "bcc":
            json_return = '"BccRecipients":['
        else:
            raise MiscError('To or CC recipients not provided')

    recipients = recipient_input.split(',')
    for num in range(len(recipients)):
        recipients[num] = recipients[num].strip()

    for m in range(0, len(recipients)):
        if len(recipients) - m == 1:
            insert = recipients[m].replace('"', "'")
            json_return += '{ "EmailAddress": { "Address": "' + insert + '" } }'
        else:
            insert = recipients[m].replace('"', "'")
            json_return += '{ "EmailAddress": { "Address": "' + insert + '" } },'

    return json_return


def set_global_token__(access_token):
    global token
    token = access_token


def get_global_token():
    return token


class Deprecated(object):
    def __init__(self, reason):
        if inspect.isclass(reason) or inspect.isfunction(reason):
            raise TypeError("Reason for deprecation must be supplied")
        self.reason = reason

    def __call__(self, cls_or_func):
        if inspect.isfunction(cls_or_func):
            if hasattr(cls_or_func, 'func_code'):
                _code = cls_or_func.func_code
            else:
                _code = cls_or_func.__code__
            fmt = "Call to deprecated function or method {name} ({reason})."
            filename = _code.co_filename
            lineno = _code.co_firstlineno + 1

        elif inspect.isclass(cls_or_func):
            fmt = "Call to deprecated class {name} ({reason})."
            filename = cls_or_func.__module__
            lineno = 1

        else:
            raise TypeError(type(cls_or_func))

        msg = fmt.format(name=cls_or_func.__name__, reason=self.reason)

        @functools.wraps(cls_or_func)
        def new_func(*args, **kwargs):
            warnings.simplefilter('always', DeprecationWarning)  # turn off filter
            warnings.warn_explicit(msg, category=DeprecationWarning, filename=filename, lineno=lineno)
            warnings.simplefilter('default', DeprecationWarning)  # reset filter
            return cls_or_func(*args, **kwargs)

        return new_func