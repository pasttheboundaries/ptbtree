from functools import wraps, partial
from types import FunctionType, MethodType
from inspect import signature

class Void:
    """
    Void represents lack of parameter where None is ia valid parameter.
    """
    pass


class MultipleCallsBlockException(Exception):
    pass


def once_decorator(fn, default=Void):
    called = False
    
    @wraps(fn)
    def wrapper(*args, **kwargs):
        
        nonlocal called
        nonlocal default
        
        if called:
            if default == Void:
                raise MultipleCallsBlockException(f'Function {fn.__name__} had been programmed to be called only once, but was called twice.')
            else:
                return default
        else:
            called = True
            return fn(*args, **kwargs)
    return wrapper
        


def once(arg):
    if callable(arg):
        return once_decorator(arg)
    else:
        return partial(once_decorator, default=arg)




def signature_parameters(obj):
    return tuple(signature(obj).parameters)


def none_if_none(*dargs):

    """
    this decorator protexts decorated call from throwing an error
    if one of the passed arguments is None
    - if bare decorator is used for decoration, this will stand for any argument to the call
    - if arguments are passed to the decorator - those must be str type and names of the parameters to be protected

    dowside of this approach is:
    if protected argument is indeed None but decorated call throws an error in unrelated case - this will be masked,
    as the decorator does not know the cause of the error, which might be unrelated to the protected parameter being None
    :param dargs: decorator arguments
    :return:
    """

    if len(dargs) == 1 and isinstance(dargs[0], (FunctionType, MethodType)):
        fn = dargs[0]

        @wraps(fn)
        def wrapper(*args, **kwargs):
            if any(a is None for a in args) or any(v is None for v in kwargs.values()):
                protect = True
            else:
                protect = False

            try:
                return fn(*args, **kwargs)
            except Exception as e:
                if protect:
                    return None
                else:
                    raise e

        return wrapper

    elif len(dargs) > 0 and all(isinstance(a, str) for a in dargs):

        def decorator(fn):
            fn_args = signature_parameters(fn)

            if any(darg not in fn_args for darg in dargs):
                raise ValueError(f'One of the passed arguments not in decorated call signature')
            which_index = [fn_args.index(param) for param in dargs]

            @wraps(fn)
            def wrapper(*args, **kwargs):
                protect = False

                for ind in which_index:
                    if ind < len(args) and args[ind] is None:
                        protect = True
                for key in kwargs:
                    if kwargs[key] is None and key in dargs:
                        protect = True

                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if protect:
                        return None
                    else:
                        raise e

            return wrapper

        return decorator