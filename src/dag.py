
''' This module provides support for the construction of a Directed
    Acyclic Graph. '''

INDENT_STR = "     "

class DAGNode(object):
    ''' Base class for a node in a Directed Acyclic Graph '''
    
    def __init__(self, parent=None, name=None):
        self._parent = parent
        self._children = []
        self._name = name

    def __str__(self):
        return self._name

    def display(self, indent=0):
        print indent*INDENT_STR, self._name
        for child in self._children:
            child.display(indent=indent+1)

    def add_child(self, child):
        self._children.append(child)

    def to_dot(self):
        ''' Generate representation in the DOT language '''
        pass
