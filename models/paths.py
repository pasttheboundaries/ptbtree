"""
Module provides abstract fixed_path objects that facilitate navigation between nodes of Tree.

As the Tree is navigated there are 2 directions:
- forward (leavs-ward)
- backward (root-ward).
Any fixed_path between 2 nodes can be at most 2-directional (bidirectional).

A fixed_path is calculated by TreeNavigator
The final result of TreeNavigator calculations is CompositePath
    (ActionTreeNavigator returns CompositePath).
    It consists of UnidirectionalPaths which may be either ForwardPath or BackwardPath.
    It is so because (as mentioned above) the shortest fixed_path from one node to another
    can be either:
    - unidirectional forward OR backward (as from a parent to its child), or
    - bidirectional : backward AND forward (as from a sibling to its sibling: back to farent and again forward).
In a bididrectional fixed_path, represented by CompositePath,
    a pivot node is represented by UnnavigablePathPoint.
    This is required as nodes themselves carry navigations (methods) to navigate the ActionTree:
    These methods are:
    - to - method co get to the node
    - back - method to go from the node to its parent
    In a backward fixed_path there is no need to store the final node
    as the navigation "back" is carried in its child node
    (which is included in the BackwardaPath).
    There is also no need to have access to the pivot node methods (neither to nor back)
    in a bidirectional fixed_path.
Also, parental binding weight is carried by a child node.
    The UnnavigablePathPoint (pivot node) is not included in total fixed_path weight.

All fixed_path classes inherit from collections.UserList which means paths are:
- iterable
- indexable
- ordered (first element is a start node ot a fixed_path and the last - the target node)

There are 2 generations of fixed_path classes:
- WeightedPath - is a basic fixed_path,  can read parental binding weight
    methods:
    - weights(self): returns a list of all node-to-node bindings
    - iter_nodes(self): returns an iterator of nodes

    properties:
    - weight: a float sum of weights

- CompositePath - ingerits from WeightedPath, can read nodes navigation methods (navigations)
    methods:
    - follow(self): calls the nodes navigations (either to or back method)
        returns the last node (target node), when navigation is complete
    - iter_navigations(self): returns an iterator of navigations
        This is implemented separately in ForwardPath, BackwardPatn and UnnavigablePathPoint
        (not in the base class), as:
         - ForwadPath returns node to methods,
         - BackwardPath return node back method
         - UnnavigablePathPoint returns dummy methods that dowas nothing when called

"""

from collections import UserList
from abc import ABC
from math import fsum


class WeightedPath(ABC):
    @property
    def weight(self):
        return fsum(self.weights)

    @property
    def weights(self):
        return tuple(n.parental_bond.weight for n in self)

    def iter_nodes(self):
        ...


class UnidirectionalPath(UserList):
    """
    Base class for navigable fixed_path
    """

    def iter_nodes(self):
        yield from self

    def __bool__(self):
        return bool(set(self))

    def __add__(self, other):
        if isinstance(other, type(self)):
            return self.__class__([*self, *other])
        elif isinstance(other, (UnidirectionalPath, CompositePath, UnnavigablePathPoint)):
            return CompositePath(self, other)
        else:
            raise TypeError(f'Can not add {self.__class__.__name__} to {type(other)}')

    def __eq__(self, other):
        if isinstance(other, type(self)) and all(n[0] == n[1] for n in zip(self.iter_nodes(), other.iter_nodes())):
            return True
        else:
            return False

    def __repr__(self):
        return f'<{self.__class__.__name__} nodes:{[n.name for n in self]}>'


    def __invert__(self):
        return self.invert()


class ForwardPath(UnidirectionalPath, WeightedPath):
    def invert(self):
        return BackwardPath(self[::-1])


class BackwardPath(UnidirectionalPath, WeightedPath):
    def invert(self):
        return ForwardPath(self[::-1])



class UnnavigablePathPoint(WeightedPath):
    def __init__(self, node):
        self.node = node

    @property
    def weights(self):
        return ()  # self.node.parentalbind.weight does not count towards the path weight

    def iter_nodes(self):
        yield self.node

    def invert(self):
        return self

    def __invert__(self):
        return self.invert()

    def __bool__(self):
        return True

    def __iter__(self):
        yield self.node

    def __add__(self, other):
        if isinstance(other, (UnidirectionalPath, CompositePath)):
            return CompositePath(self, other)
        elif isinstance(other, UnnavigablePathPoint):
            if self.node == other.node:
                return self
            else:
                raise ValueError(f'Could not concatenate different UnnavigablePathPoints')
        else:
            raise TypeError(f'Could not concatenate UnnavigablePathPoint and {type(other)}.')

    def __repr__(self):
        return f'<{self.__class__.__name__} node:[{self.node.name}]>'


class CompositePath(UserList, WeightedPath):
    def __init__(self, *paths):
        initlist = CompositePath._unravel(paths)
        super().__init__(initlist)

    @staticmethod
    def _unravel(paths) -> list:
        unidirect_paths_list = []
        for path in paths:
            if isinstance(path, (UnidirectionalPath, UnnavigablePathPoint)):
                unidirect_paths_list.append(path)
            elif isinstance(path, CompositePath):
                for pth in CompositePath._unravel(path):
                    unidirect_paths_list.append(pth)
            else:
                raise TypeError(
                    f'CompositePath can not accept type {type(path)}. '
                    f'Valid types are UnidirectionalPath and CompositePath')
        return CompositePath._reduce(unidirect_paths_list)

    @staticmethod
    def _reduce(unidirect_paths_list):
        reduced_paths_list = []
        for ind in range(len(unidirect_paths_list)):
            current = unidirect_paths_list[ind]
            if ind == 0:
                reduced_paths_list.append(current)
                continue

            last_unidicrect = reduced_paths_list[-1]
            last_type = type(last_unidicrect)
            if last_type == UnnavigablePathPoint:
                if isinstance(current, UnnavigablePathPoint):
                    try:
                        last_unidicrect + current
                    except ValueError:
                        raise RuntimeError('Different adjacent UnnavigablePathPoints found.')
                else:
                    reduced_paths_list.append(current)
                continue
            if isinstance(current, last_type):
                new_unidirect = last_unidicrect + current
                reduced_paths_list[-1] = new_unidirect
            else:
                reduced_paths_list.append(current)
        return reduced_paths_list

    def iter_nodes(self):
        """
        generator of nodes from the CompositePath
        """
        for unidirect_path in self:
            for node in unidirect_path:
                yield node

    @property
    def weights(self):
        return tuple(w for unidirectional_path in self for w in unidirectional_path.weights)

    def invert(self):
        return CompositePath(*[unidirect_path.invert() for unidirect_path in tuple(self)[::-1]])

    def __invert__(self):
        return self.invert()

    def __bool__(self):
        return all(unidirect for unidirect in self)

    def __add__(self, other):
        if isinstance(other, (CompositePath, UnidirectionalPath, UnnavigablePathPoint)):
            return CompositePath(self, other)
        else:
            raise TypeError(f'Can not add {self.__class__.__name__} to {type(other)}')

    def __repr__(self):
        return f'<{self.__class__.__name__} uni_paths:{list(self)}>'


# action paths

class ActionPath(ABC):
    def follow(self):
        """
        a generator of fixed_path nodes
        """
        ...

    def iter_navigations(self):
        """
        a generator of navigation methods
        """
        ...


class ForwardActionPath(ForwardPath, ActionPath):

    def follow(self):
        node = None
        for node in self:
            node.to()
        return node  # returns last node of the fixed_path

    def iter_navigations(self):
        for node in self:
            yield node.to

    def invert(self):
        return BackwardActionPath(self[::-1])


class BackwardActionPath(BackwardPath, ActionPath):
    def follow(self):
        node = None
        for node in self:
            node.back()
        return node  # returns last node of the fixed_path

    def iter_navigations(self):
        """
        a generator of navigation methods
        """
        for node in self:
            yield node.back

    def invert(self):
        return ForwardActionPath(self[::-1])


class UnnavigableActionPathPoint(UnnavigablePathPoint, ActionPath):

    def follow(self, *args, **kwargs):
        # calls no navigation
        return self.node

    def iter_navigations(self):
        # returns dummy callable
        yield lambda *x: None

    def __iter__(self):
        """
        this mimics Iterable behaviour
        """
        yield self.node

    def __add__(self, other):
        if isinstance(other, (UnidirectionalPath, CompositeActionPath)):
            return CompositeActionPath(self, other)
        else:
            raise TypeError(f'Could not concatenate UnnavigableActionPathPoint and {type(other)}.')


class CompositeActionPath(CompositePath, ActionPath):
    def __init__(self, *paths):
        initlist = CompositePath._unravel(paths)
        super().__init__(initlist)

    def follow(self):
        node = None
        for unidirect_path in self:
            node = unidirect_path.follow()
        return node  # returns last node of the last fixed_path

    def iter_navigations(self):
        """
        generator of navigation methods from the CompositeActionPath
        """
        for unidirect_path in self:
            for nav in unidirect_path.iter_navigations():
                yield nav

    def invert(self):
        return CompositeActionPath(*[unidirect_path.invert() for unidirect_path in tuple(self)[::-1]])

    def __add__(self, other):
        if isinstance(other, ActionPath):
            return CompositeActionPath(self, other)
        else:
            raise TypeError(f'Can not add {self.__class__.__name__} to {type(other)}')

    def __repr__(self):
        return f'<{self.__class__.__name__}>{list(self)}'