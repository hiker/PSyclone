
''' This module provides support for the construction of a Directed
    Acyclic Graph. '''

INDENT_STR = "     "
DEBUG = False
VALID_NODE_TYPES = ["operator", "constant", "array_ref"]

class DirectedAcyclicGraph(object):

    def __init__(self, name):
        self._nodes = {}
        self._name = name

    def get_node(self, name, parent, mapping, unique=False, node_type=None):
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
                return self._nodes[node_name]
            else:
                if DEBUG:
                    print "No existing node with name: ", node_name
                node = DAGNode(parent=parent, name=node_name)
                self._nodes[node_name] = node
        if node_type:
            node.node_type = node_type
        return node


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
        ''' Returns a unique string identify this node in the graph '''
        return "node"+str(id(self))

    def display(self, indent=0):
        print indent*INDENT_STR, self._name
        for child in self._children:
            child.display(indent=indent+1)

    def add_child(self, child):
        self._children.append(child)

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

