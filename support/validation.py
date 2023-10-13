from collections.abc import Callable


def validate_callable(cal: Callable, error_message=None):
    default_error_message = f'Invalid argument. Expected callable. Got type {type(cal)}'
    error_message = error_message or default_error_message
    if not isinstance(cal, Callable):
        raise TypeError(error_message)
    return cal


def validate_str(s):
    if not isinstance(s, str):
        raise TypeError(f'Expected str type. Got {type(s)}.')
    return s