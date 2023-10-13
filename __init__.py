"""
This package implements Tree and ActionTree structures.

Tree is a structure composed of nodes bound by parental bonds.
(a parent with no child has no bonds, a child always has a parent and asigned bond)
Tree allows for finding paths between nodes.
ParentalBond is weighted. A weight of a path can be calculated.

An ActionTree is a Tree of ActionNodes and is an abstraction of a tree-like structured functionality.
ActionNode is a functional node of a tree-like hierarchy.
Each Node of an ActionTree has 2 (obligatory) navigation methods:
- to (leading from the node parent to the node)
- back (leading from the node to the node parent)
Methods must be declared by user at instantiation.
Navigating the ActionTree is equal to calling navigation methods while moving between nodes.

"""
__version__ = 0.1
__author__ = 'pasttheboundaries@gmail.com'

from .models.tree import Node, Tree
from .models.actiontree import ActionTree, ActionNode, Action, CheckinError, TreeCutError, NavigationError, OwnerNode
from .models. actionargs import  ActionArg, CallableArg, PropertyArg
from .common.errors import *
