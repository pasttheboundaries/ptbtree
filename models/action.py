"""
Action is a callable wrapper
it works as a partial object, and is instantiated the same way.
The major difference is that all arguments will be evaluated ad the moment of call.
If argument is an instance of ActionArg it will be called first.

Action.wrap class method can be used as a decorator that produces an Action object at compiletime

OwnerNode is a proxy object that can be used in an original function (later to wrapped in an Action, or not),
that will be passed to a Node as one of action arguments (to, back, action, onreached, checkin).
At Node instantiation it will be substituted by the Node the function is passed to.
This allows pre-designing the function so it will reach for the node that owns it:
example:

#defining function with OwnerNode proxy
def nav_to_node():
    # do navigation
    loger.log(f'{OwnerNode.name} was entered')

#defining node with nav_to_node function
n = Node(to=nav_to_node, back= ..., name='FirstNode')

# will perfornm navigation
# and log 'FistNode was entered'
n.to()

"""
from .actionargs import ActionArg
from ptbtree.common.errors import *


Void = object()


class Action:
    __slots__ = ['_callable_', '_args_', '_kwargs_', '_result_', '_node_', '_actiontree_']

    def __init__(self, call, *args, **kwargs):
        if not callable(call):
            raise TypeError(f'Action first argument must be callable. Got {call}')
        if isinstance(call, Action):
            action = call
            call = action._callable_
            args = action._args_
            kwargs = action._kwargs_
        self._callable_ = call
        self._args_ = args or tuple()
        self._kwargs_ = kwargs or dict()
        self._result_ = Void
        print(self._kwargs_)

    def _activated_args(self):
        args = []
        for arg in self._args_:
            if isinstance(arg, ActionArg):
                arg = arg()
            args.append(arg)
        return args

    def _activated_kwargs(self):
        kwargs = dict()
        for k, v in self._kwargs_.items():
            if isinstance(v, ActionArg):
                v = v()
            kwargs[k] = v
        return kwargs

    def __call__(self, *args, **kwargs):
        args = args or self._activated_args()
        actkwrgs = self._activated_kwargs()
        actkwrgs.update(kwargs)  # precedence of called _kwargs_ over _kwargs_ given at instantiation
        print(*args, actkwrgs)
        self._result_ = self._callable_(*args, **actkwrgs)
        return self.result
    
    @property
    def result(self):
        if self._result_ == Void:
            raise ActionException(f'Action has no result yet. Action needs to be called first before result is attempted to be extracted.')
        return self._result_
        
    
    @classmethod
    def wrap(cls, *args, **kwargs):
        """
        this is a decorator that can be used:
        - without an argument:
            in that case the decorated function will be wrapped in Action
        - with arguments (any):
            arguments will be recorded and used in action to call the decorated function
        """
        
        def action_wrapper(*args, **kwargs):
            def partial_action(fn):
                nonlocal args
                nonlocal kwargs
                return Action(fn, *args, *kwargs)
            return partial_action
        
        
        if (len(kwargs) == 0 and
            len(args) == 1 and
            callable(args[0]) and
            not isinstance(args[0], ActionArg)
           ):
            return Action(call=args[0])
        elif len(kwargs) == 0 and len(args) == 0:
            raise NotImplemented(f'Decorator Action.wrap has been callet without arguments. This operation is illegal.')
        else:
            return action_wrapper(*args, *kwargs)
        
    def __repr__(self):
        return f'<Action ({self._callable_.__name__})>'
