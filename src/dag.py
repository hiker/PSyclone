
''' This module provides support for the construction of a Directed
    Acyclic Graph. '''

INDENT_STR = "     "
DEBUG = False
VALID_NODE_TYPES = ["operator", "constant", "array_ref"]

class DirectedAcyclicGraph(object):

    def __init__(self, name):
        # Dictionary of all referenceable nodes in the graph.
        self._nodes = {}
        # Name of this DAG
        self._name = name

    def get_node(self, name, parent, mapping, unique=False, node_type=None):
        ''' Looks-up or creates a node in the graph. If unique is False and
        we do not already have a node with the supplied name then we create a
        new one. If unique is True then we always create a new node. '''
        if unique:
            # Node is unique so we make a new one, no questions
            # asked. Since it is unique it will not be referred to again
            # and therefore we don't store it in the list of
            # cross-referenceable nodes.
            if DEBUG:
                print "Creating a unique node labelled '{0}'".format(name)
            node = DAGNode(parent=parent, name=name)
        else:
            if name in mapping:
                node_name = mapping[name]
            else:
                node_name = name
            # Node is not necessarily unique so check whether we
            # already have one with the supplied name
            if node_name in self._nodes:
                if DEBUG:
                    print "Matched node with name: ", node_name
                node = self._nodes[node_name]
                # If this node does not already have a parent then
                # set it now (it may not have had a parent when
                # first created)
                if not node.parent:
                    node.parent = parent
                return node
            else:
                if DEBUG:
                    print "No existing node with name: ", node_name
                # Create a new node and store it in our list so we
                # can refer back to it in future if needed
                node = DAGNode(parent=parent, name=node_name)
                self._nodes[node_name] = node
        if node_type:
            node.node_type = node_type

        return node

    def ancestor_nodes(self):
        ''' Returns a list of all nodes that do not have a parent '''
        node_list = []
        for node in self._nodes.itervalues():
            if node.parent is None:
                node_list.append(node)
        return node_list

    def count_nodes(self, node_type):
        ''' Count the number of nodes in the graph that are of the
        specified type '''
        ancestors = self.ancestor_nodes()
        print "Have {0} ancestor nodes.".format(len(ancestors))
        node_list = []
        for node in ancestors:
            nodes = node.walk(node_type)
            for new_node in nodes:
                if new_node not in node_list:
                    node_list.append(new_node)

        return len(node_list)


class DAGNode(object):
    ''' Base class for a node in a Directed Acyclic Graph '''
    
    def __init__(self, parent=None, name=None):
        self._parent = parent
        self._children = []
        self._name = name
        self._node_type = None

    def __str__(self):
        return self._name

    @property
    def _node_id(self):
        ''' Returns a unique string identifying this node in the graph '''
        return "node"+str(id(self))

    def display(self, indent=0):
        print indent*INDENT_STR, self._name
        for child in self._children:
            child.display(indent=indent+1)

    def add_child(self, child):
        self._children.append(child)

    @property
    def children(self):
        return self._children

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, node):
        self._parent = node

    @property
    def node_type(self):
        return self._node_type

    @node_type.setter
    def node_type(self, mytype):
        ''' Set the type of this node '''
        if mytype not in VALID_NODE_TYPES:
            raise Exception("node_type must be one of {0} but "
                            "got '{1}'".format(VALID_NODE_TYPES, mytype))
        self._node_type = mytype

    def walk(self, node_type):
        ''' Walk down the tree from this node and generate a list of all
        nodes of type node_type '''
        local_list = []
        for child in self._children:
            if child.node_type == node_type:
                local_list.append(child)
            local_list += child.walk(node_type)
        return local_list

    def to_dot(self, fileobj):
        ''' Generate representation in the DOT language '''
        for child in self._children:
            child.to_dot(fileobj)

        nodestr = "{0} [label=\"{1}\"".format(self._node_id, self._name)
        if self._node_type:
            if self._node_type == "operator":
                node_colour = "red"
            elif self._node_type == "constant":
                node_colour = "green"
            elif self._node_type == "array_ref":
                node_colour = "blue"
            nodestr += ", color=\"{0}\"".format(node_colour)
        nodestr += "]\n"
        
        fileobj.write(nodestr)
        fileobj.write(self._node_id+" -> {\n")
        for child in self._children:
            fileobj.write(" "+child._node_id)
        fileobj.write("}\n")

