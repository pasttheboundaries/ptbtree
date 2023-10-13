import unittest
from ptbtree.models.tree import Node, Tree


class TestNode(unittest.TestCase):
    def setUp(self) -> None:
        self.parent = Node(name='0')
        self.tree = Tree()

    def test_init_no_tree(self):
        node = Node(name='example')
        self.assertEqual(node, 'example', 'name not set')
        self.assertIs(node.tree, None)

    def test_init_with_tree(self):
        node = Node(tree=self.tree, name='example')
        self.assertEqual(node, 'example', 'name not set')
        self.assertEqual(node.tree, self.tree, 'tree declared but not asigned')
        self.assertIs(self.tree.root, node, 'rot not mounted as tree root')
        self.assertEqual(node.tier, 0, 'node tier not calculated')

    def test_parental_bond(self):
        parent = Node(name='parent', tree=Tree())
        node = Node(parent=parent)
        self.assertEqual(node.parent, parent)
        self.assertIn(node, parent.children)
        self.assertEqual(node.parental_bond.weight, 1)

    def test_tree_coopt_by_parent(self):
        parent = Node(tree=Tree(), name='parent')
        node = Node(parent=parent)  # name is not needed for this test
        node_1 = Node(parent=parent, name ='over')
        self.assertEqual(node.tier, 1, ' tiers wrongly applied')
        self.assertIs(node.tree, parent.tree, 'parent.tree is not equal to child tree')
        self.assertEqual(len(parent.descendants), 2, 'child not in descendants')
        self.assertEqual(len(parent.children), 2, 'child not in children')
        self.assertEqual(len(parent.tree.tiers[1]), 2, 'child not in its tier')
        self.assertEqual(node.name, 1, 'counted name wrongly applied')
        self.assertEqual(node_1.name, 'over', 'name wrongly applied')



if __name__ == '__main__':
    unittest.main()

