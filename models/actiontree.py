"""
actiontree.py
"""


from typing import Optional, Union
from types import FunctionType
from .action import Action
from .paths import ForwardActionPath, BackwardActionPath, CompositeActionPath, UnnavigableActionPathPoint
from .derail import DerailSafeNavigationManager
from ptbtree.common.errors import *
from ptbtree.common.logging import get_logger
from collections.abc import Mapping
from .tree import Tree, Node
from .navigator import ActionTreeNavigator


logger = get_logger(__name__)


OwnerNode = object()


import copy
import types
import functools


def copy_func(f, globals=None, module=None):
    """Based on https://stackoverflow.com/a/13503277/2988730 (@unutbu)"""
    if globals is None:
        globals = f.__globals__
    g = types.FunctionType(f.__code__, globals, name=f.__name__,
                           argdefs=f.__defaults__, closure=f.__closure__)
    g = functools.update_wrapper(g, f)
    if module is not None:
        g.__module__ = module
    g.__kwdefaults__ = copy.copy(f.__kwdefaults__)
    return g


def inject_node(fn, node):
    if isinstance(fn, Action):
        action = fn
        fn = action._callable_
        fn = inject_node(fn, node)
        action._callable_ = fn
        return action
        
    elif isinstance(fn, FunctionType):
        if fn.__closure__:
            for clos in fn.__closure__:
                content = clos.cell_contents
                if isinstance(content, types.FunctionType):
                    clos.cell_contents = inject_node(content, node)
        new_fn_namespace= dict(fn.__globals__)
        if new_fn_namespace.get('OwnerNode'):
            new_fn_namespace['OwnerNode'] = node
        new_fn = copy_func(fn, new_fn_namespace)
        return new_fn
    else:
        return fn


class ActionNode(Node):
    """
    ActionNode of ActionTree
    :param to: callable or Action - will be called to reach the node from its parent
    :param back: callable or Action - will be called to go back to parent
    :param name: str - must be declared. Optionally if is set to 'int', ActionNode.name will be index number in the tree it belongs to.
        If tree is grafted, tree nodes names will not be reindexed.
    :param onreached: callable or Action - will be called each time the node is reached from both ways back or to.
    :param parent: ActionNode - if not declared, an attempt will be made to set the node the root of the declared tree
    :param tree: ActionTree - the ActionTee object the node is to be assigned to.
    :param checkin: must be a callable returning bool - this is to check wheather ActionNode has been reached correctly.
    If None, a new Action Tree will be created and the ActionNode will be seeded as root.
    In that case parent must be None as well, otherwise Error ValueError will be raised.

    The namespac of a callable used in a role of to, back, action, onreached or checkin will be ammended
    so OwnerNode global variable will reference the node that the callable was applied to.

    """

    def __init__(self, to, back, *,
                 onreached=None,
                 action=None,
                 tree=None,
                 parent=None,
                 checkin=None,
                 name: Optional[str] = None):

        super().__init__(tree=tree, parent=parent, name=name)

        #setting actions
        self._to_ = Action(inject_node(to, self))
        self._back_ = Action(inject_node(back, self))

        if action:
            self.action = Action(inject_node(action, self))
        else:
            self.action = None
        
        if onreached:
            self.onreached = Action(inject_node(onreached, self))
        else:
            self.onreached = None
        
        if checkin:
            self.checkin = Action(inject_node(checkin, self))
        else:
            self.checkin = None


    def to(self):
        if not self.tree:
            raise ValueError('ActionTree-unbound ActionNode can not be entered.')
        if self != self.tree.root:
            self.tree.cutblock()
            
        try:
            result = self._to_()
        except Exception as e:
            raise NavigationError(f'Could not access node {self} from parent.') from e
        
        if self.checkin:
            try:
                self.tree.checkin(self, self._to_)
            except Exception as e:
                raise NavigationError(f'Could not perform checkin for node {self}') from e
            
        self._reached()
                
        return result

    def back(self):
        if not self.tree:
            raise ValueError('ActrionTree-unbound ActionNode can not be returned from.')
        self.tree.cutblock()
        if not self.parent:
            raise ValueError('ActionNode.back was called but node has no parent.')
        try:
            result = self._back_()
        except Exception as e:
            raise NavigationError(f'Could not return from node {self}.') from e
            
        if self.parent.checkin:
            try:
                self.tree.checkin(self.parent, self._back_)
            except Exception as e:
                raise NavigationError(f'Could not perform checkin for node {self}') from e
                
        self.parent._reached()
                
        self.tree.current_node = self.parent
        return result

    def _reached(self):
        self.tree.current_node = self
        
        if self == self.tree.root:
            self.tree._cut = False
            
        if self.onreached:
            try:
                return self.onreached()
            except Exception as e:
                raise NavigationError(f'Could not perform on-reached action for node {self}') from e

    def follow(self):
        return self.tree.follow(self)

    def add_child(self, child):
        Node.bind(self, child)

    
    def copy(self, name=None, grafted=True, _parent_copy_=None, _new_tree_=None):
        """
        returns a copy of self
        
        :param name: str
        :param grafted: bool - if True the copy of the node will be grafted into the node parent
        
        :param _parent_copy_: - solely for recursion use. Not for user.
        :param _new_tree_: - solely for recursion use. Not for user.
        
        :return: a copy of the node
        """
        name = name or self.name

        if grafted:
            _parent = _parent_copy_ or self.parent
            _tree = _new_tree_ or self.tree
        else:
            _parent = None
            _tree = ActionTree()

        self_copy = ActionNode(to=self._to_, back=self._back_, tree=_tree, parent=_parent, name=name)
        for child in self.children:
            _new_child = child.copy(grafted=True, _parent_copy_=self_copy, _new_tree_=_tree)

        return self_copy

    def __repr__(self):
        return f'<ActionNode tier:{self.tier} name:{self.name}>'


class ActionTree(Tree):
    """
    Parent structure for Nodes.
    It holds the root ActionNode (ActionTree.root)

    methods:
    find_path(targetm, start=None) : returns from start node (or root node) to target node
    follow(target, start=None): performs find_path and performs method follow in the fixed_path found.
    graft(node), grafts the whole tree to another tree by indicated node
    size - return s the number of nodes

    """
    
    def __init__(self, root: Optional[ActionNode] = None, name: Optional[str] = None, checkin_persist=3):
        super().__init__(root=root, name=name)

        self.nodes_activation_history = []
        self._cut = True  # flag
        self.checkin_persist = checkin_persist
        self.last_checkin = None
        self.navigator = ActionTreeNavigator(self)

    # TODO continue class reduction from here

    @staticmethod
    def _search_forward_path(current: ActionNode, target: Union[ActionNode, str]) -> CompositeActionPath:
        forward_path = ActionTree._search_forward(current=current, target=target)
        return CompositeActionPath(ForwardActionPath(forward_path[1:]))

    @staticmethod
    def _search_forward(current: ActionNode, target: ActionNode) -> ForwardActionPath:
        if target == current:
            return ForwardActionPath([current])
        children_paths = [ActionTree._search_forward(child, target) for child in current.children]
        children_paths = [child_path for child_path in children_paths if child_path]
        if children_paths:
            return ForwardActionPath([current]) + children_paths.pop()
        else:
            return ForwardActionPath()

    @staticmethod
    def _search_backward_path(current: ActionNode, target: Union[ActionNode, str]) -> \
            Union[CompositeActionPath, BackwardActionPath, UnnavigableActionPathPoint]:
        if current == target:  # end of backward_path
            return CompositeActionPath(UnnavigableActionPathPoint(current))
        if not current.parent:  # can not build backward
            return CompositeActionPath()
        if current.parent == target:  # parent is target
            return CompositeActionPath(BackwardActionPath([current]) + UnnavigableActionPathPoint(current.parent))

        parent_forward_path = ActionTree._search_forward_path(current.parent, target)  # searching forward from parent
        if parent_forward_path:
            return CompositeActionPath(BackwardActionPath([current]) + UnnavigableActionPathPoint(current.parent) + parent_forward_path)

        backward_path = ActionTree._search_backward_path(current.parent, target)  # searching backward from parent
        if backward_path:
            return CompositeActionPath(BackwardActionPath([current]) + backward_path)
        else:
            return CompositeActionPath()

    def find_path(self, target, start=None):
        return self.navigator.find_path(target, start=start)

    def follow(self, target, start=None):
        self.cutblock()
        start = start or self.current_node or self.root
        path = self.find_path(target, start)
        return DerailSafeNavigationManager(self, path).follow()  # navigation result

    def internalize(self, namespace: Mapping):
        if not isinstance(namespace, Mapping):
            raise TypeError(f'ActionTree can not internalize namespace. Required type is Mapping (eg. dict).')
        namespace = dict(namespace)
        for key in namespace.keys():
            if hasattr(self, key):
                raise ValueError(f'ActionTree can not internalize {key}, because this attribute is already owned.')
        self.__dict__.update(namespace)

    def seed(self, namespace=None):
        """
        performs ActionTree.root.to action
        """
        if namespace:
            self.internalize(namespace)
        
        if self.root is None:
            raise ValueError('ActionTree could not be seeded as root node has not been defined.')
        result =  self.root.to()
        self._cut = False
        return result
    
    def cut(self):
        self.cutblock()
        if self.root is None:
            raise ValueError('ActionTree could not be cut as root node has not been defined.')
        
        # attempting graceful root follow
        try:
            self.follow(self.root)
        except Exception:
            pass
        
        # attpempting gracefull cut
        try:
            result = self.root._back_()
            return result
        except Exception:
            pass
        finally:
            self._cut = True
        
    def cutblock(self):
        """
        raises if the tree has been cut
        """
        if self._cut:
            raise TreeCutError('The tree is cut. Method can not be called at the moment. Needs to reseed the tree.')

    @property
    def current_node(self):
        if self.nodes_activation_history:
            return self.nodes_activation_history[-1]
    
    @current_node.setter
    def current_node(self, node):
        if not isinstance(node, ActionNode):
            raise TypeError(f'Expected type ActionNode, got {node}')
        if not (node in self.nodes):
            raise ValueError(f'Setting current node requires ActionTree bound node.')
        
        self.nodes_activation_history.append(node)

    def checkin(self, target_node, navigation, checkin_persist=None):
        checkin_persist = checkin_persist or self.checkin_persist
        if not isinstance(target_node, ActionNode):
            raise TypeError(f'ActionTree.chcekin argument mus be type ActionNode. Got {type(target_node)}')
        
        self.last_checkin = CheckIn(self, target_node, navigation, checkin_persist)
        return self.last_checkin.check()
        
    def __contains__(self, item):
        if not isinstance(item, ActionNode):
            raise TypeError(f'Action tree contains Nodes and can not check membership of type {type(item)}')
        return item == self.root or self.root.in_descendants(item)

    def __repr__(self):
        cut = self._cut and ' CUT' or ''
        return f'<ActionTree nodes:{self.size}{cut}>'
    
    
class CheckIn:
    def __init__(self, tree, node, navigation: Optional=None, checkin_persist: Optional = None):
        self.tree = tree
        self.node = node
        self.navigation = navigation
        self.checkin_persist = checkin_persist or 1
        self.exceptions = []
        
    def check(self, _checkin_persist=0) -> bool:
        if _checkin_persist >= self.checkin_persist:
            logger.debug('checkin FALSE')
            return False
        # checkin confiramation
        try:
            check = self.node.checkin()
            if check:
                logger.debug('checkin TRUE')
                return True
            else:
                raise CheckinError('Checkin is False')
        except Exception as e:
            self.exceptions.append(e)

        # logger.debug('retrying NAVIGATION')
        # self._retry_navigation()
        return self.check(_checkin_persist + 1)

    def _retry_navigation(self):
        try:
            """blind attempt
            if anything fails there is no consequences"""
            return self.navigation()
        except Exception as e:  
            
            self.exceptions.append(e)
            # raise e # TODO - is this necessary at all
            
                