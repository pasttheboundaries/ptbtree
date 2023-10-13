"""
TreeNavigator is an object that navigates Tree object
ActionTreeNavigator is an object that navigates ActionTree
"""

from typing import Union
from ptbtree.common.errors import NoRootException, NavigationError
from ptbtree.models.paths import (ForwardPath, BackwardPath, CompositePath, UnnavigablePathPoint,
                                 ForwardActionPath,BackwardActionPath, CompositeActionPath,
                                 UnnavigableActionPathPoint)


class TreeNavigator:
    """
    Tree navigator
    - finds paths from node to node.
    """
    COMPOSITE_PATH_TYPE = CompositePath
    FORWARD_PATH_TYPE = ForwardPath
    BACKWARD_PATH_TYPE = BackwardPath
    UNNAVIGAVLE_PP_TYPE = UnnavigablePathPoint

    def __init__(self, tree):
        self.tree = tree
        self.current_node = None
        self.history = list()
        self.current_node = tree.root

    def tree_navigable(self):
        if self.tree.root is None:
            raise NoRootException(self.tree)
        return True

    def find_path(self, target, start=None):
        self.tree_navigable()
        if target not in self.tree:
            raise NavigationError(f'{target} not in {self.tree}')
        current = start or self.tree.root

        if target == current:
            return self.COMPOSITE_PATH_TYPE(self.UNNAVIGAVLE_PP_TYPE(current))
        if forward := self._search_forward_path(current, target):
            return forward
        elif backward := self._search_backward_path(current, target):
            return backward
        else:
            raise NavigationError(f'Could not find fixed_path to node {target}')

    def _search_forward_path(self, current, target) -> CompositePath:
        forward_path = self._search_forward(current=current, target=target)
        #return self.COMPOSITE_PATH_TYPE(self.FORWARD_PATH_TYPE(forward_path[1:]))
        return self.UNNAVIGAVLE_PP_TYPE(current) + self.FORWARD_PATH_TYPE(forward_path[1:])


    def _search_forward(self, current, target) -> ForwardPath:
        if target == current:
            return self.FORWARD_PATH_TYPE([current])
        children_paths = [self._search_forward(child, target) for child in current.children]
        children_paths = [child_path for child_path in children_paths if child_path]
        if children_paths:
            if len(children_paths) != 1:
                raise RuntimeError(f'{len(children_paths)} paths found')
            return self.FORWARD_PATH_TYPE([current]) + children_paths.pop()
        else:
            return self.FORWARD_PATH_TYPE()

    def _search_backward_path(self, current, target) -> Union[CompositePath, BackwardPath, UnnavigablePathPoint]:
        if current == target:  # end of backward_path
            return self.COMPOSITE_PATH_TYPE(self.UNNAVIGAVLE_PP_TYPE(current))
        if not current.parent:  # can not build backward
            return self.COMPOSITE_PATH_TYPE()
        if current.parent == target:  # parent is target
            return self.COMPOSITE_PATH_TYPE(self.BACKWARD_PATH_TYPE([current])
                                            + self.UNNAVIGAVLE_PP_TYPE(current.parent))

        # continue searching forward
        parent_forward_path = self._search_forward_path(current.parent, target)  # searching forward from parent
        if parent_forward_path:
            return self.COMPOSITE_PATH_TYPE(
                self.BACKWARD_PATH_TYPE([current])
                + self.UNNAVIGAVLE_PP_TYPE(current.parent)
                + parent_forward_path)

        # take another step backward
        backward_path = self._search_backward_path(current.parent, target)  # searching backward from parent
        if backward_path:
            return self.COMPOSITE_PATH_TYPE(self.BACKWARD_PATH_TYPE([current]) + backward_path)
        else:
            return self.COMPOSITE_PATH_TYPE()


class ActionTreeNavigator(TreeNavigator):
    COMPOSITE_PATH_TYPE = CompositeActionPath
    FORWARD_PATH_TYPE = ForwardActionPath
    BACKWARD_PATH_TYPE = BackwardActionPath
    UNNAVIGAVLE_PP_TYPE = UnnavigableActionPathPoint
