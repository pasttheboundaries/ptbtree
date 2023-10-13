from collections.abc import Callable
#from ..common.decorators import none_if_none


#@none_if_none('cal')  # this will return None if callable is None
def validate_callable(cal, error_message=None):
    default_error_message = f'Invalid argument. Expected callable. Got type {type(cal)}'
    error_message = error_message or default_error_message
    if not isinstance(cal, Callable):
        raise TypeError(error_message)
    return cal
