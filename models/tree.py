"""
classes constituting tree structure:
Node and Tree
with all the side code
"""

from typing import Optional
from itertools import chain

import numpy as np
from ptbtree.models.navigator import TreeNavigator
from ptbtree.common.errors import *
from ptbtree.support.validation import validate_str
from collections.abc import Iterable


class ChildrenCollection(set):
    pass


class ChildrenHolder:
    def __get__(self, instance, owner):
        if not hasattr(instance, '_children_'):
            instance._children_ = ChildrenCollection()
        return instance._children_


class ParentHolder:
    def __get__(self, instance, owner):
        if not hasattr(instance, '_parent_'):
            return None
        return instance._parent_

    def __set__(self, instance, parent_node):
        if hasattr(instance, '_parent_') and isinstance(instance._parent_, Node):
            raise NodeError('Node Parent can be only set once. '
                                 'To subscribe node to another parent, create the node copy with grafted=False.')
        if not isinstance(parent_node, Node):
            raise TypeError(f'Could not set parent with type {type(parent_node)}. Valid type is Node only.')
        instance.set_parent(parent_node)


class NodeBinderMethods:
    """
    This class provides Node methods to facilitate node binding.
    """

    def negotiate_bond(self, parent, child, weight):
        if parent.tree is None:
            raise NodeError('Nodes can not be bound outside Tree. Parent Node must be asigned to Tree, beforehand.')
        parent.children.add(child)
        child._parent_ = parent
        child.parental_bond = ParentalBond(weight)
        # asigning to tree must go after binding nodes
        #  otherwise a child without a parent will attempt to be set as a root of the parent tree
        child.tree = parent.tree


    def set_parent(self, parent_node, weight=1, _bidirect=True):

        if hasattr(self, '_parent_') and isinstance(self._parent_, Node):
            raise NodeError('Node Parent can be only set once. '
                                 'To subscribe node to another parent, use method graft.')
        if not isinstance(parent_node, Node):
            raise TypeError(f'Could not set parent with type {type(parent_node)}. Valid type is Node only.')

        self.negotiate_bond(parent_node, self, weight)


    def set_child(self, child_node, weight=1, _bidirect=True):
        if not isinstance(child_node, Node):
            raise TypeError (f'Can not set Node child with tyle {type(child_node)}')
        if child_node in self.children:
            raise NodeError(f'{child_node} already in {self} children.')

        self.negotiate_bond(self, child_node, weight)


class TreeHolder:
    def __get__(self, instance, owner):
        if not hasattr(instance, '_tree_'):
            instance._tree_ = None
        return instance._tree_

    def __set__(self, instance, tree):
        # def tree(self, t):
        if not isinstance(tree, Tree):
            raise TypeError(f'Could not set tree with type {type(tree)}. Valid type is Tree only.')
        if instance.tree and not instance.tree is tree:
            raise NodeError(f'Node already in Tree. A new tree can only be applied by grafting the node.')
        instance._tree_ = tree
        for desc in instance.children:
            desc.tree = tree
        instance._tree_.add_node(instance)


class ParentalBond():
    def __init__(self, weight=1):
        self.weight = weight


class Node(NodeBinderMethods):
    """
    Node of Tree.
    Is an abstract structure that represents a node of a tree graph.
    It can exist on its own but as such will not contribute any functionality over binding ability to other nodes.
    Node can have multiple child nodes but only one parent.
    A parent and children of a node must be type node.

    Defining a child (node.set_child(child: Node)) adds the child to node.children.
    Defining a parent (node.set_parent(parent: Node)) add the node to the parents children.
    If Node instance has children (node.children : list) is considered a parent of the children nodes.
    If Node instance has a parent (node.parent) is considered to be a child of the parent.

    All instantiation arguments are keyed arguments.
    :param name: str - must be declared. Optionally if is set to 'int', Node.name will be index number in the tree it belongs to.
        If tree is grafted, tree nodes names will not be reindexed.
    :param parent: Node - if not declared, an attempt will be made to set the node the root of the declared tree
    :param tree: Tree - the ActionTee object the node is to be assigned to.


    methods:
        set_child(x): adds x to node.children
        set_parent(x): adds the node to x.children
        is_leaf(): returns bool if both: node is in Tree and node has no children
        as_root(): returns a Tree object with the node as the tree root.
        copy(name, grafted:bool=True): copies the node and grafts the copy to the node parent if indicated
        explant(): removes all parental bindings of the node. Also removes all connection to the parent tree.
            descendant nodes loose theit connection to the node's parent tree. Although keep bindings with the node.
            Explantend node can be grafted to another node (as root) or another node (as child)
        graft(other: Union[Tree, Node]):
            explants the node and grafts it to an empty tree (as root) or to a node (as a child)

    attributes:
        tree: (getter, setter) Tree the node belongs to
        parent: parent node
        children: list of children nodes
        parental_bond

    """
    children = ChildrenHolder()
    parent = ParentHolder()
    tree = TreeHolder()

    def __init__(self, *, tree=None, parent=None, bond_weight=1, name: Optional[str] = None):
        self.tier = None
        self.parental_bond = None

        if parent:
            self.set_parent(parent, weight=bond_weight)

        if tree:
            self.tree = tree
        # else if parent - parent will deal with ascribing tree to children

        if not name:
            if self.tree:
                name = len(self.tree.nodes) - 1  # This is intentional. At this point the node is already added to a tree
            else:
                raise NodeError('Can not use ordinal number for name as the node has not been ascribed to a tree.')
        self.name = name

    @property
    def descendants(self):
        return list(chain(self.children, *[child.descendants for child in self.children]))

    @property
    def ancestors(self):
        if self.parent:
            return list(chain([self.parent], self.parent.ancestors))
        else:
            return tuple()

    # this is to be removed as it duplicates functionality of descendants (DOUBLE CHECK before removing)
    def in_descendants(self, item):
        if not isinstance(item, Node):
            raise TypeError(f'Descendants of Node are type Node, not {type(item)}.')
        if self.children:
            return item in self.children or any(child.in_descendants(item) for child in self.children)
        else:
            return False

    def is_leaf(self):
        return bool(self.tree) and not bool(self.children)

    @classmethod
    def bind(cls, parent, child):
        parent.set_child(child)

    def as_root(self):
        """Creates a new Tree and puts self as a root"""
        self.explant()
        self.tree = Tree(root=self)
        return self

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
            _tree = Tree()

        self_copy = Node(tree=_tree, parent=_parent, name=name)
        for child in self.children:
            _new_child = child.copy(grafted=True, _parent_copy_=self_copy, _new_tree_=_tree)

        return self_copy

    def explant(self):
        self.parent.children.remove(self)
        self._parent_ = None
        self.parental_bond = None
        self._tree_ = None
        for descendant in self.descendants:
            descendant._tree_ = None
        return self

    def graft(self, other, bind_weight=1):
        if isinstance(other, Tree):
            if len(other.nodes) == 0:
                self.explant()
                other.add_node(self)
                return self
            else:
                raise ValueError('Node can not be grafted to not empty tree. Try grafting to a specific node.')
        elif isinstance(other, Node):
            self.explant()
            self.set_parent(other, weight=bind_weight)
        else:
            raise TypeError(f'Node can only be grafted to Tree another Node')


    def __eq__(self, other):
        if isinstance(other, Node):
            return self is other
        elif isinstance(other, str):
            return bool(self.name and self.name == other)
        else:
            raise TypeError(f'Could not compare Node to {type(other)}')

    def __repr__(self):
        return f'<Node tier:{self.tier} name:{self.name} children:{len(self.children)}>'

    def __hash__(self):
        return hash(id(self))


class TreeInstances(list):
    pass


class TreePandasPlugin:
    DF_STOP_VALUES = [np.nan,]

    @classmethod
    def from_df(cls, df, weights=None):

        """
        Creates Tree form DataFrame.

        Assumption:
        DataFrame object is assumed to contained data for Tree
        Columns would represent tiers:
            The first column would represent root so it must contain the same value in all rows
            The subsequent columns might contain varying values.
        Rows would represent paths from root to leaf nodes.
        Each row will be followed to crate nodes (values will be set as names of nodes),
            so the right column value will become the child node of the left column value.

        DataFrame:
            1, 2, 3
            1, 2, 4
            1, 5, 6
        wil produce Tree:
            1:
            - 2:
                - 3 (leaf)
                - 4 (leaf)
            - 5:
                - 6 (leaf)

        if multiple values are found in column 0 en Error will be thrown

        If a numpy.nan is found the df, a branch creation will be stopped and the parent value will create a leaf node.
        The row processing stops at this point.
        DataFrame:
            1, 2, np.nan
            1, np.nan, 4
            1, 5, 6
        wil produce Tree:
            1:
            - 2 (leaf)
            - 5:
                - 6 (leaf)

        :param df: DataFrame
        :return: Tree
        """

        import pandas as pd

        # checking df
        if isinstance(df, str):
            df = pd.read_csv(df)
        elif isinstance(df, pd.DataFrame):
            pass
        else:
            raise TypeError('Expected pandas.DataFrame or valid fixed_path to csv.')
        root_values = df.iloc[:, 0].unique()
        if len(root_values) != 1:
            raise TreeError(f'Found {len(root_values)} different values in column 0. Unable to compile Tree.')

        # weights
        if isinstance(weights, np.ndarray):
            expected_shape = (df.shape[0], df.shape[1] - 1)
            if weights.shape == expected_shape:
                pass
            else:
                raise ValueError (f'Invalid weights array. Expected shape {expected_shape}, got {weights.shape}')
        elif isinstance(weights, Iterable):
            weights = np.array(weights).flatten().reshape(1,-1)
            if weights.shape[1] != df.shape[1] - 1:
                raise ValueError(
                    f'Weights apply to parenent-child bindings. Expected number is {df.shape[1] - 1}.'
                    f' Got {len(weights)}')
            else:
                pass
        elif isinstance(weights, float):
            weights = (np.ones(df.shape[1] - 1) * weights).reshape(1,-1)
        elif weights is None:
                weights = np.ones(df.shape[1] - 1).reshape(1,-1)
        else:
            raise ValueError (f'Could not parse weights{weights}')

        tree = Tree()
        root = Node(name=root_values[0])
        tree.root = root

        return cls._read_rows(df, tree, weights)

    @classmethod
    def _read_rows(cls, df, tree, weights):
        for ind in range(df.shape[0]):
            row = df.iloc[ind, :]
            tree = cls._read_row(row, tree, ind, weights)
        return tree

    @classmethod
    def _read_row(cls, row, tree, ind, weights):
        for col in range(1, len(row)):
            parent_tier_index = col - 1
            df_parent_value = row.iat[parent_tier_index]
            df_child_value = row.iat[col]
            if df_child_value in cls.DF_STOP_VALUES:
                return tree
            try:
                parent = [n for n in tree.tier(col - 1) if n.name == df_parent_value].pop()
            except IndexError:
                raise RuntimeError('Code error')

            try:
                [n for n in tree.tier(col) if n.name == df_child_value].pop()
            except IndexError:
                child = Node(name=df_child_value)
            else:
                continue


            weight = weights[min(ind, weights.shape[0] - 1), parent_tier_index]

            parent.set_child(child, weight=weight)
        return tree


class Tree(TreePandasPlugin):
    """
    Parent structure for Nodes.
    It holds the root Node (Tree.root)

    methods:
    find_path(targetm, start=None) : returns from start node (or root node) to target node
    follow(target, start=None): performs find_path and performs method follow in the fixed_path found.
    graft(node), grafts the whole tree to another tree by indicated node
    size - return s the number of nodes

    """
    instances = TreeInstances()

    def __init__(self, root: Optional[Node] = None, name: Optional[str] = None):
        self.name = name

        if root:
            self.add_node(root)

        self.instances.append(self)
        self.navigator = TreeNavigator(self)
        self.ntier = 0

    @property
    def root(self):
        if hasattr(self, '_root'):
            return self._root

    @root.setter
    def root(self, node):
        if not isinstance(node, Node):
            raise TypeError(f'Tree root must be type Node. Got {type(node)}')
        self._root = node
        node.tree = self

    def add_node(self, node):
        """
        Adding nodes to tree is done by nodes
        Tree must be only informed which node is root - this is done here
        If Node parent is in tree then node is considered added
        In that case re-asigning tiers is done
        :param node: Node
        :return: None
        """

        if not isinstance(node, Node):
            raise TypeError(f'Could not add {type(node)} to Tree. Only type Node is allowed.')
        if node.parent is not None:
            if node.parent in self:
                if node.tree != self:
                    node.tree = self
                self.asign_tiers(node.parent, node.parent.tier)
            else:
                raise ValueError('Node parent not in the Tree. Add parent to the Tree first.')
        else:
            if self.root:
                if self.root != node:
                    raise ValueError(f'Can not add root node to the Tree because it has one. '
                                     f'Please reconfigure the tree or fix the parent of the node being added.')
                else:
                    self.asign_tiers()
            else:
                self._root = node
                if self.root.tree != self:
                    self.root.tree = self
                self.asign_tiers()

    def asign_tiers(self, node=None, tier=0):
        """

        :param node: asingning start point
        :param tier: asigning start value
        :return: self
        """
        self.ntier = tier + 1
        if node is None:
            node = self.root
            tier = 0
        node.tier = tier
        for child in node.children:
            self.asign_tiers(child, tier=tier + 1)
        return self

    def graft(self, node):
        """
        grafts Tree (self) to an existing Node, which must belong to another Tree
        :param node:
        :return:
        """
        if not isinstance(node, Node):
            raise GraftingError(f'Could not graft Tree to {type(node)}. '
                                f'Tree can be grafted to Node of another Tree only.')
        if node.tree is self:
            raise GraftingError(f'Tree can not be grated to itself.')
        if node.tree is None:
            raise GraftingError(f'Could not graft Tree to unbound Node '
                                f'Tree can be grafted to Node of another Tree only.')

        self.root.parent = node
        # node.add_child(self.root)
        for desc in node.descendants:
            desc.tree = node.tree
        node.tree.asign_tiers()
        return node.tree

    @property
    def size(self):
        if self.root:
            root_descendants = len(self.root.descendants)
        else:
            root_descendants = 0
        return 1 + root_descendants

    @property
    def nodes(self):
        if self.root:
            return [self.root] + self.root.descendants
        else:
            return tuple()

    def tier(self, n):
        self.asign_tiers()
        return [node for node in self.nodes if node.tier == n]

    @property
    def tiers(self):
        ts = []
        ind = 0
        while True:
            indexed_ts = [n for n in self.nodes if n.tier == ind]
            if indexed_ts:
                ts.append(indexed_ts)
            else:
                break
            ind += 1
        return ts

    def iter_leaves(self):
        return (n for n in self.nodes if not n.children)

    def iter_branches(self):
        return (self.find_path(leaf, self.root) for leaf in self.iter_leaves())

    @property
    def nleaf(self):
        return len(tuple(self.iter_leaves()))

    @property
    def nbond(self):
        return len([n for n in self.nodes if n.parental_bond])

    def get_node(self, *names, ignorecase=True, start=None):
        """
        Returns a node by its name.
        If multiple names are given they are treated as names of nodes to climb to get the final node,
        so always the last name node is returned.
        This allows climbing the tree even if multiple nodes of one tier have descendants of the same name.
        like in:
        get_node('family', 'father', 'room')
        # will return 'room' which is descendant of 'father'
        # whilst also other members of the family might have 'room' node.
        """
        start = start or self.root
        if not names:
            raise ValueError('names not declared.')

        name = names[0]
        others = names[1:]

        for node in [start, *start.descendants]:
            if node.name == name or (ignorecase and node.name.lower() == name.lower()):
                break
        else:
            return None

        if others:
            return self.get_node(*others, ignorecase=ignorecase, start=node)
        else:
            return node

    def find_path(self, target, start=None):
        return self.navigator.find_path(target, start)

    def __contains__(self, item):
        if not isinstance(item, Node):
            raise TypeError(f'Action tree contains Nodes and can not check membership of type {type(item)}')
        return item == self.root or item in self.root.descendants

    def __repr__(self):
        return f'<Tree nodes:{self.size}>'
