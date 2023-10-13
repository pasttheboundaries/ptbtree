##INTRO  
This package implements Tree and ActionTree structures.

Tree is a structure composed of nodes bound by parental bonds.
(a parent with no child has no bonds, 
a child always has a parent and asigned parental bond).  
Tree allows for finding paths between nodes and aggregating and extracting some info about nodes.  
Nodes of a tree are organised into tiers.    
ParentalBond is weighted. A weight of a path can be calculated.

An ActionTree is a Tree of ActionNodes and is an abstraction of a tree-like structured functionality.  
ActionNode is a functional node of a tree-like hierarchy.  
Each Node of an ActionTree has 2 (obligatory) navigation methods:
- to (leading from the node parent to the node)
- back (leading from the node to the node parent)

The navigation methods must be declared by user at instantiation.  
Navigating the ActionTree is equal to calling navigation methods while moving between nodes.

##VERSION  
0.1 is the initial commit.
It is a functional code with some significant drawbacks:
- actionnode checkin procedure is in development.
- code is not DRY yet


##CLASSES  
###ptbtree.Node  
Node of Tree.
    Is an abstract structure that represents a node of a tree graph.
    It can exist on its own but as such will not contribute any functionality over binding ability to other nodes.
    Node can have multiple child nodes but only one parent.
    A parent and children of a node must be type node.
    
Defining a child (node.set_child(child: Node)) adds the child to node.children.  
Defining a parent (node.set_parent(parent: Node)) add the node to the parents children.  
If Node instance has children (node.children : list) is considered a parent of the children nodes.  
If Node instance has a parent (node.parent) is considered to be a child of the parent.  
Node, when f added to an empty Tree becomes tree.root.     
     
All __instantiation arguments__ are keyed arguments:
- name: str - must be declared. Optionally if is set to 'int', Node.name will be index number in the tree it belongs to.
        If tree is grafted, tree nodes names will not be reindexed.
- parent: Node - if not declared, an attempt will be made to set the node the root of the declared tree
- tree: Tree - the ActionTee object the node is to be assigned to.

__methods:__
- set_child(x): adds x to node.children 
- set_parent(x): adds the node to x.children.  
Binding can be made only within Tree structure which means that parent must be asigned to Tree beforehand.
- is_leaf(): returns bool if both: node is in Tree and node has no children
- as_root(): returns a Tree object with the node as the tree root.
- copy(name, grafted:bool=True): copies the node and grafts the copy to the node parent if indicated
- explant(): removes all parental bindings of the node. Also removes all connection to the parent tree.
            descendant nodes loose theit connection to the node's parent tree. Although keep bindings with the node.
            Explantend node can be grafted to another node (as root) or another node (as child)
- graft(other: Union[Tree, Node]):
            explants the node and grafts it to an empty tree (as root) or to a node (as a child)

__attributes:__
- tree: (getter, setter) Tree the node belongs to
- parent: parent node
- children: list of children nodes
- parental_bond
        
###ptbtree.Tree  


  
