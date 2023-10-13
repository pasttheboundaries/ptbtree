

class TreeError(Exception):
    pass


class GraftingError(TreeError):
    pass


class NoRootException(TreeError):
    pass


class TreeCutError(TreeError):
    pass


class NavigationError(TreeError):
    pass


class NodeError(Exception):
    pass


class CheckinError(NodeError):
    pass


class ActionException(Exception):
    pass


class DerailFixError(NavigationError):
    pass


class DerailSafeNavigationException(Exception):
    pass