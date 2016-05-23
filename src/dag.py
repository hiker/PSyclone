
''' This module provides support for the construction of a Directed
    Acyclic Graph. '''

from fparser.Fortran2003 import \
    Add_Operand, Level_2_Expr, Level_2_Unary_Expr, Real_Literal_Constant, \
    Name, Section_Subscript_List, Parenthesis, Part_Ref

DEBUG = False
INDENT_STR = "     "

# Types of floating-point operation with their cost in cycles
# (from http://www.agner.org/optimize/instruction_tables.pdf)
# TODO these costs are microarchitecture specific.
OPERATORS = {"+":1, "-":1, "/":40, "*":1}

# Valid types for a node in the DAG
VALID_NODE_TYPES = OPERATORS.keys() + ["intrinsic", "constant", "array_ref"]

# Fortran intrinsics that we recognise, with their cost in cycles
# (as obtained from micro-benchmarks: dl_microbench).
# TODO these costs are microarchitecture (and compiler?) specific.
FORTRAN_INTRINSICS = {"SIGN":3, "SIN":49, "COS":49}

def is_subexpression(expr):
    ''' Returns True if the supplied node is itself a sub-expression. '''
    if isinstance(expr, Add_Operand) or \
       isinstance(expr, Level_2_Expr) or \
       isinstance(expr, Level_2_Unary_Expr) or \
       isinstance(expr, Parenthesis):
        return True
    return False


def is_intrinsic_fn(obj):
    ''' Checks whether the supplied object is a call to a Fortran
        intrinsic '''
    if not isinstance(obj.items[0], Name):
        raise Exception("is_intrinsic_fn: expects first item to be Name")
    if str(obj.items[0]) in FORTRAN_INTRINSICS:
        return True
    return False


def str_to_node_name(astring):
    ''' Hacky method that takes a string containing a Fortran array reference
    and returns a string suitable for naming a node in the graph '''
    new_string = astring.replace(" ", "")
    new_string = new_string.replace(",", "_")
    new_string = new_string.replace("+", "p")
    new_string = new_string.replace("-", "m")
    new_string = new_string.replace("(", "_")
    new_string = new_string.replace(")", "")
    return new_string


# TODO: would it be better to inherit from the built-in list object?
class Path(object):
    ''' Class to encapsulate functionality related to a specifc path
    through a DAG '''

    def __init__(self):
        self._nodes = []

    def load(self, obj_list):
        ''' Populate this object using the supplied list of nodes '''
        self._nodes = obj_list

    def add_node(self, obj):
        self._nodes.append(obj)

    def cycles(self):
        ''' The length of the path in cycles '''
        cost = 0
        for node in self._nodes:
            cost += node.weight
        return cost

    def flops(self):
        ''' The number of floating point operations in the path '''
        flop_count = 0
        for node in self._nodes:
            if node.node_type in OPERATORS:
                flop_count += 1
        return flop_count

    def __len__(self):
        ''' Over-load the built-in len operation so that it behaves as
        expected '''
        return len(self._nodes)

    def to_dot(self, fileobj):
        ''' Write this path to the supplied DOT file '''
        pathstr = self._nodes[0].node_id
        for node in self._nodes[1:]:
            pathstr += " -> {0}".format(node.node_id)
        pathstr += "[color=red,penwidth=3.0];"
        fileobj.write(pathstr)


class DirectedAcyclicGraph(object):

    def __init__(self, name):
        # Dictionary of all referenceable nodes in the graph.
        self._nodes = {}
        # Name of this DAG
        self._name = name
        # Those nodes that have no parents in the tree
        self._ancestors = None
        # The critical path through the graph
        self._critical_path = Path()

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
        if self._ancestors:
            return self._ancestors

        node_list = []
        for node in self._nodes.itervalues():
            if node.parent is None:
                node_list.append(node)
        return node_list

    def count_nodes(self, node_type):
        ''' Count the number of nodes in the graph that are of the
        specified type '''
        ancestors = self.ancestor_nodes()
        node_list = []
        for node in ancestors:
            nodes = node.walk(node_type)
            for new_node in nodes:
                if new_node not in node_list:
                    node_list.append(new_node)
        return len(node_list)

    def cache_lines(self):
        ''' Count the number of cache lines accessed by the graph. This
        is the number of distinct memory references. We assume that
        any array reference of the form u(i+1,j) will have been fetched
        when u(i,j) was accessed. '''
        array_refs = []
        # Loop over all nodes in the tree, looking for array references
        ancestors = self.ancestor_nodes()
        for ancestor in ancestors:
            nodes = ancestor.walk("array_ref")
            for node in nodes:
                # TODO replace this hack with a nice way of identifying
                # neighbouring array references.
                # TODO extend to i+/-n where n > 1.
                # Map any reference to xxx(i+/-1, j) back on to xxx(i,j)
                name = node.name.replace("ip1_","i_")
                name = name.replace("im1_", "i_")
                if name not in array_refs:
                    array_refs.append(name)
        return len(array_refs)

    def calc_costs(self):
        ''' Analyse the DAG and calculate a weight for each node. '''
        ancestors = self.ancestor_nodes()
        for node in ancestors:
            node.calc_weight()

    def make_dag(self, parent, children, mapping):
        ''' Makes a DAG from the RHS of a Fortran assignment statement '''

        if DEBUG:
            for child in children:
                if isinstance(child, str):
                    print "String: ", child
                elif isinstance(child, Part_Ref):
                    print "Part ref", str(child)
                else:
                    print type(child)
            print "--------------"

        opcount = 0
        for child in children:
            if isinstance(child, str):
                if child in OPERATORS:
                    # This is the operator which is then the parent
                    # of the DAG of this subexpression. All operators
                    # are unique nodes in the DAG.
                    opnode = self.get_node(child, parent, mapping, unique=True,
                                           node_type=child)
                    parent.add_child(opnode)
                    parent = opnode
                    opcount += 1
        if opcount > 1:
            raise Exception("Found more than one operator amongst list of "
                            "siblings: this is not supported!")

        for child in children:
            if isinstance(child, Name):
                var_name = str(child)
                tmpnode = self.get_node(var_name, parent, mapping)
                parent.add_child(tmpnode)
            elif isinstance(child, Real_Literal_Constant):
                # This is a constant and thus a leaf in the tree
                tmpnode = self.get_node(str(child), parent, mapping,
                                        unique=True,
                                        node_type="constant")
                parent.add_child(tmpnode)
            elif isinstance(child, Part_Ref):
                # This can be either a function call or an array reference
                # TODO sub_class Part_Ref and implement a proper method to
                # generate a string!
                if is_intrinsic_fn(child):
                    if DEBUG:
                        print "found intrinsic: {0}".\
                            format(str(child.items[0]))
                    # Create a unique node to represent the intrinsic call
                    tmpnode = self.get_node(str(child.items[0]), parent,
                                            mapping, unique=True,
                                            node_type="intrinsic")
                    parent.add_child(tmpnode)
                    # Add its dependencies
                    self.make_dag(tmpnode, child.items[1:], mapping)
                else:
                    name = str_to_node_name(str(child))
                    tmpnode = self.get_node(name, parent, mapping,
                                            node_type="array_ref")
                    parent.add_child(tmpnode)
            elif is_subexpression(child):
                # We don't make nodes to represent sub-expresssions - just
                # carry-on down to the children
                self.make_dag(parent, child.items, mapping)
            elif isinstance(child, Section_Subscript_List):
                # We have a list of arguments
                self.make_dag(parent, child.items, mapping)

    def critical_path(self):
        ''' Calculate the critical path through the graph '''
        path = []

        # Compute inclusive weights for each node
        self.calc_costs()

        for node in self.ancestor_nodes():
            node.critical_path(path)

        # Use the resulting list of nodes to populate our Path object
        self._critical_path.load(path)

        return self._critical_path

    def to_dot(self):
        ''' Write the DAG to file in DOT format. If a list of nodes is
        provided then that path is also written to the file. '''

        # Create a file for the graph of this subroutine
        fo = open(self._name+".gv", "w")
        fo.write("strict digraph {\n")

        for node in self.ancestor_nodes():
            node.to_dot(fo)

        # Write the critical path
        if len(self._critical_path):
            self._critical_path.to_dot(fo)

        fo.write("}\n")
        print "Wrote DAG to {0}".format(fo.name)
        fo.close()


class DAGNode(object):
    ''' Base class for a node in a Directed Acyclic Graph '''

    def __init__(self, parent=None, name=None):
        self._parent = parent
        self._children = []
        # The name of this node - used to label the node in DOT
        self._name = name
        # The type of this node
        self._node_type = None
        # The inclusive weight (cost) of this node. This is the cost of
        # this node plus that of all of its descendants. This then
        # enables us to find the critical path through the graph.
        self._incl_weight = 0

    def __str__(self):
        return self._name

    @property
    def node_id(self):
        ''' Returns a unique string identifying this node in the graph '''
        return "node"+str(id(self))

    @property
    def name(self):
        ''' Returns the name (label) of this node '''
        return self._name

    def display(self, indent=0):
        ''' Prints a textual representation of this node to stdout '''
        print indent*INDENT_STR, self._name
        for child in self._children:
            child.display(indent=indent+1)

    def add_child(self, child):
        ''' Add a child to this node '''
        self._children.append(child)

    @property
    def children(self):
        ''' Returns the list of children belonging to this node '''
        return self._children

    @property
    def parent(self):
        ''' Returns the parent of this node (or None if it doesn't
        have one) '''
        return self._parent

    @parent.setter
    def parent(self, node):
        ''' Set the parent of this node '''
        self._parent = node

    @property
    def node_type(self):
        ''' Returns the type of this node (one of VALID_NODE_TYPES) '''
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

    @property
    def weight(self):
        ''' Returns the (exclusive) weight/cost of this node '''
        if not self._node_type:
            return 0
        else:
            if self._node_type in OPERATORS:
                return OPERATORS[self._node_type]
            elif self._node_type == "intrinsic":
                return FORTRAN_INTRINSICS[self._name]
            else:
                return 0

    def calc_weight(self):
        ''' Calculate the inclusive weight of this node by recursing
        down the tree and summing the weight of all descendants '''
        self._incl_weight = self.weight
        for child in self._children:
            self._incl_weight += child.calc_weight()
        return self._incl_weight

    def critical_path(self, path):
        ''' Compute the critical (most expensive) path from this node '''
        # Add ourself to the path
        path.append(self)
        # Find the child with the greatest inclusive weight
        max_weight = 0.0
        node = None
        for child in self._children:
            if child._incl_weight > max_weight:
                max_weight = child._incl_weight
                node = child
        # Move down to that child
        if node:
            node.critical_path(path)

    def to_dot(self, fileobj):
        ''' Generate representation in the DOT language '''
        for child in self._children:
            child.to_dot(fileobj)

        nodestr = "{0} [label=\"{1} w={2}\"".format(self.node_id,
                                                    self._name,
                                                    str(self._incl_weight))
        if self._node_type:
            node_size = None
            if self._node_type in OPERATORS:
                node_colour = "red"
                node_shape = "box"
                node_size = str(0.5 + 0.01*self.weight)
            elif self._node_type == "constant":
                node_colour = "green"
                node_shape = "ellipse"
            elif self._node_type == "array_ref":
                node_colour = "blue"
                node_shape = "ellipse"
            elif self._node_type == "intrinsic":
                node_colour = "gold"
                node_shape = "ellipse"
            else:
                node_colour = "black"
                node_shape = "elipse"
            nodestr += ", color=\"{0}\", shape=\"{1}\"".format(node_colour,
                                                               node_shape)
            if node_size:
                nodestr += ", height=\"{0}\"".format(node_size)
        nodestr += "]\n"

        fileobj.write(nodestr)
        fileobj.write(self.node_id+" -> {\n")
        for child in self._children:
            fileobj.write(" "+child.node_id)
        fileobj.write("}\n")
