from  typing import Any
from abc import ABC


class ActionArg(ABC):
    def __call__(self):
        ...


class CallableArg(ActionArg):
    """
    This is a wrapper to encase a callable that will be called dynamically at the runtime.
    Every callable that needs to be called at the moment of action execotion to get the current result
     needs to be passed throu this wrapper.

    """
    def __init__(self, call, *args, **kwargs) -> None:
        self.callable = call
        self.args = args
        self.kwargs = kwargs or dict()

    def __call__(self, *args, **kwargs) -> Any:
        args = args or self.args
        self.kwargs.update(kwargs)
        return self.callable(*args, **self.kwargs)


class PropertyArg(ActionArg):
    """
    This is a wrapper to encase object which property is to be returned, at the moment of action axecution.
    This allows for retrieving the most current value of the wrapped object
    """
    def __init__(self, obj: Any, property_name: str) -> None:
        if not isinstance(property_name, str):
            raise TypeError('property_name argument must be a string')
        self.obj = obj
        self.propperty_name = property_name

    def __call__(self) -> Any:
        return self.obj.__getattribute__(self.propperty_name)

