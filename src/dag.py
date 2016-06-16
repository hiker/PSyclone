
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
OPERATORS = {"+":1, "-":1, "/":14, "*":1, "FMA":1}

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
    ''' Class that encapsulates a Directed Acyclic Graph as a whole '''

    def __init__(self, name):
        # Dictionary of all nodes in the graph.
        self._nodes = {}
        # Name of this DAG
        self._name = name
        # Those nodes that have no parents in the tree
        self._ancestors = None
        # The critical path through the graph
        self._critical_path = Path()

    @property
    def name(self):
        ''' Returns the name of this DAG. This is (normally) derived from
        the subroutine containing the Fortran code from which it is
        generated. '''
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name

    def get_node(self, name, parent, mapping, unique=False, node_type=None):
        ''' Looks-up or creates a node in the graph. If unique is False and
        we do not already have a node with the supplied name then we create a
        new one. If unique is True then we always create a new node. '''
        if unique:
            # Node is unique so we make a new one, no questions
            # asked.
            if DEBUG:
                print "Creating a unique node labelled '{0}'".format(name)
            node = DAGNode(parent=parent, name=name, digraph=self)
            # Store this node in our list using its unique ID in place of a
            # name (since a unique node has been requested). This then
            # ensures we have a list of all nodes in the graph.
            self._nodes[node.node_id] = node
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

    def delete_node(self, node):
        ''' Removes the supplied node from the list of nodes in
        this graph and then deletes it altogether '''
        # We don't know the key with which this node was stored in the
        # dictionary - it might have been the name or, for a 'unique' node,
        # its node_id.
        if node.name in self._nodes and self._nodes[node.name] == node:
            self._nodes.pop(node.name)
        elif node.node_id in self._nodes and self._nodes[node.node_id] == node:
            self._nodes.pop(node.node_id)
        else:
            raise Exception("Object {0} not in list of nodes in graph!".
                            format(str(node)))
        del node

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

    def total_cost(self):
        ''' Calculate the total cost of the graph by summing up the cost of
        each node '''
        sum = 0
        for node in self._nodes.itervalues():
            sum += node.weight
        return sum

    def fuse_multiply_adds(self):
        ''' Processes the existing graph and creates FusedMultiplyAdds
        where possible '''
        ancestors = self.ancestor_nodes()
        for node in ancestors:
            node.fuse_multiply_adds()

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
                # This may be either a function call or an array reference
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
                    from parse2003 import Variable
                    arrayvar = Variable()
                    arrayvar.load(child, mapping)
                    name = str(arrayvar)
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

    def calc_critical_path(self):
        ''' Calculate the critical path through the graph '''
        paths = []

        # Compute inclusive weights for each node
        self.calc_costs()

        # Each of the ancestor (output) nodes represents a starting
        # point for a critical path. The longest of the resulting set
        # of paths is then the critical path of the DAG as a whole.
        for node in self.ancestor_nodes():
            path = Path()
            node_list = []
            node.critical_path(node_list)
            if node_list:
                path.load(node_list)
                paths.append(path)

        # Find the longest of these paths
        max_cycles = 0
        for path in paths:
            if path.cycles() > max_cycles:
                max_cycles = path.cycles()
                crit_path = path

        self._critical_path = crit_path

    @property
    def critical_path(self):
        return self._critical_path
    
    def to_dot(self):
        ''' Write the DAG to file in DOT format. If a critical path has
        been computed then it is also written to the file. '''

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

    def report(self):
        ''' Report the properties of this DAG to stdout '''
        # Compute some properties of the graph
        num_plus = self.count_nodes("+")
        num_minus = self.count_nodes("-")
        num_mult = self.count_nodes("*")
        num_div = self.count_nodes("/")
        num_fma = self.count_nodes("FMA")
        num_ref = self.count_nodes("array_ref")
        num_cache_ref = self.cache_lines()
        total_cycles = self.total_cost()
        # An FMA may only cost 1 (?) cycle but still does 2 FLOPs
        total_flops = num_plus + num_minus + num_mult + num_div + 2*num_fma
        print "Stats for DAG {0}:".format(self._name)
        print "  {0} addition operators.".format(num_plus)
        print "  {0} subtraction operators.".format(num_minus)
        print "  {0} multiplication operators.".format(num_mult)
        print "  {0} division operators.".format(num_div)
        print "  {0} fused multiply-adds.".format(num_fma)
        print "  {0} FLOPs in total.".format(total_flops)
        print "  {0} array references.".format(num_ref)
        print "  {0} distinct cache-line references.".\
            format(num_cache_ref)
        # Performance estimate using whole graph
        print "  Sum of cost of all nodes = {0} (cycles)".format(total_cycles)
        print "  {0} FLOPs in {1} cycles => {2:.4f}*CLOCK_SPEED FLOPS".\
            format(total_flops, total_cycles,
                   float(total_flops)/float(total_cycles))

        if num_cache_ref > 0:
            flop_per_byte = total_flops / (num_cache_ref*8.0)
            # This is naive because all FLOPs are not equal - a division
            # costs ~20-40x as much as an addition.
            print "  Naive FLOPs/byte = {:.3f}".format(flop_per_byte)
        else:
            print "  Did not find any array/memory references"

        # Performance estimate using critical path
        ncycles = self._critical_path.cycles()
        print ("  Critical path contains {0} nodes, {1} FLOPs and "
               "is {2} cycles long".format(len(self._critical_path),
                                           self._critical_path.flops(),
                                           ncycles))
        # Graph contains total_flops and will execute in at
        # least path.cycles() CPU cycles. A cycle has duration
        # 1/CLOCK_SPEED (s) so kernel will take at least
        # path.cycles()*1/CLOCK_SPEED (s).
        # Theoretical max FLOPS = total_flops*CLOCK_SPEED/path.cycles()
        flops_per_hz = float(total_flops)/float(ncycles)
        print ("  Theoretical max FLOPS (ignoring memory accesses) = "
               "{:.4f}*CLOCK_SPEED".format(flops_per_hz))
        print ("  (e.g. at 3.8 GHz, this gives {:.2f} GFLOPS)".
               format(flops_per_hz*3.0))


class DAGNode(object):
    ''' Base class for a node in a Directed Acyclic Graph '''

    def __init__(self, parent=None, name=None, digraph=None):
        self._parent = parent
        # Keep a reference back to the digraph object containing
        # this node
        self._digraph = digraph
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

    def fuse_multiply_adds(self):
        ''' Recursively take any opportunities to fuse multiplication and
        addition operations '''
        for child in self._children:
            child.fuse_multiply_adds()
        fusable_operations = ["+", "*"]
        # If this node is an addition or a multiplication
        if self._node_type in fusable_operations:
            # Loop over a copy of the list of children as this loop
            # modifies the original
            for child in self._children[:]:
                if child._node_type != self._node_type and \
                   child._node_type in fusable_operations:
                    # We can create an FMA. This replaces the addition
                    # operation and inherits the children of the 
                    # multiplication operation
                    for grandchild in child.children:
                        self.add_child(grandchild)
                        grandchild.parent = self
                    # Delete the multiplication/addition node
                    self._children.remove(child)
                    self._digraph.delete_node(child)

                    # Change the type of this node
                    self._name = "FMA"
                    self._node_type = "FMA"
                    if len(self._children) != 3:
                        raise Exception("An FMA node must have 3 children "
                                        "but found {0}".
                                        format(len(self._children)))
                    break

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
