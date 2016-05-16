
''' This module provides support for the construction of a Directed
    Acyclic Graph. '''

INDENT_STR = "     "
DEBUG = False

class DirectedAcyclicGraph(object):

    def __init__(self, name):
        self._nodes = {}
        self._name = name

    def get_node(self, name, parent, unique=False):
        if unique:
            # Node is unique so we make a new one, no questions
            # asked...
            if DEBUG:
                print "Creating a unique node labelled '{0}'".format(name)
            return DAGNode(parent=parent, name=name)
        else:
            # Node is not necessarily unique so check whether we
            # already have one with the supplied name
            if name in self._nodes:
                if DEBUG:
                    print "Matched node with name: ", name
                return self._nodes[name]
            else:
                if DEBUG:
                    print "No existing node with name: ", name
                newnode = DAGNode(parent=parent, name=name)
                self._nodes[name] = newnode
                return newnode


class DAGNode(object):
    ''' Base class for a node in a Directed Acyclic Graph '''
    
    def __init__(self, parent=None, name=None):
        self._parent = parent
        self._children = []
        self._name = name

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

    def to_dot(self):
        ''' Generate representation in the DOT language '''
        for child in self._children:
            child.to_dot()
        print "{0} [label=\"{1}\"]".format(self._node_id, self._name)
        print self._node_id, " -> {"
        for child in self._children:
            print child._node_id
        print "}"

