"""
this module delivers classes and methods to reperform navigation to node if the process gets derailed at some point

The 3 major steps to manage the derailment is:
1) note the navigation has derailed, record the navigation fixed_path
2) find out which node on the navigation fixed_path is active and set it a tree.current_node
3) reconstruct fixed_path from the current node to the target

"""

from ptbtree.common.logging import get_logger
from ptbtree.common.errors import DerailFixError, DerailSafeNavigationException

logger = get_logger(__name__)


class DerailPathfinder:
    """
    navigation derailment fix
    """
    def __init__(self, tree, navigation_path):
        self.tree = tree
        self.navigation_path = navigation_path
        self.target = list(self.navigation_path.iter_nodes())[-1]

    def _find_active(self):
        """
        finds the active node of the ActionTree amongs the ones on the declared fixed_path
        and sets tree.current_node to it.
        """
        for node in self.navigation_path.iter_nodes():
            if node.checkin():
                self.tree.current_node = node
                return
            else:
                pass
        raise DerailFixError('Could not find the active node.')

    def fixed_path(self):
        """
        returns re-navigation fixed_path
        """
        logger.debug(f'attempting to create a new fixed_path')
        self._find_active()
        return self.tree.find_path(start=self.tree.current_node, target=self.target)


class DerailSafeNavigationManager:
    """manager of derail safe naviagation"""
    def __init__(self, tree, navigation_path, retry=3):
        self.tree = tree
        self.current_path = navigation_path
        self.original_path = navigation_path
        self.retry = retry
        
    def follow(self):
        """
        TODO:
        At the moment retry-fold loopped attempts is the only way to manage derail
        This call must implement more intelligent approach to derailment
        
        """
        for loop in range(self.retry):
            logger.debug(f'Derail.follow loop {loop}')
            try:
                navigation_result = self._attempt_follow()
            except Exception:
                self.current_path = DerailPathfinder(self.tree, self.original_path).fixed_path()
                logger.debug(f'found : {self.current_path}')
                continue
            else:
                return navigation_result

        # if all the looping has no result
        raise DerailSafeNavigationException('It was supposed to be derail safe. Damn it!!!. ')
                        
    def _attempt_follow(self):
        try:
            navigation_result = None
            for nav in self.current_path.iter_navigations():
                logger.debug(f'following {nav}')
                navigation_result = nav()
        except Exception:
            raise
        else:
            return navigation_result
                