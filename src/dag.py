
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


def subgraph_matches(node1, node2):
        ''' Returns True if the two nodes (and any children they may
        have) represent the same quantity. '''
        if node1._name != node2._name:
            return False
        if len(node1._children) != len(node2._children):
            return False
        for child1 in node1._children:
            found = False
            # We can't assume that the two lists of children have the same
            # ordering...
            for child2 in node2._children:
                # Recurse down
                if child1 == child2:
                    found = True
                    break
            if not found:
                return False
        return True


class DAGError(Exception):
    ''' Class for exceptions related to DAG manipulations '''
    
    def __init__(self, value):
        self.value = "DAG Error: " + value

    def __str__(self):
        return repr(self.value)


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
        ''' The number of floating point operations in the path. This is
        NOT the same as the number of cycles required to execute the
        path. '''
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
    ''' Class that encapsulates a Directed Acyclic Graph representing a
    piece of Fortran code '''

    def __init__(self, name):
        # Dictionary of all nodes in the graph. Keys are the node names,
        # values are the corresponding DAGNode objects themselves.
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

    def get_node(self, parent, mapping=None, name=None, unique=False,
                 node_type=None, variable=None):
        ''' Looks-up or creates a node in the graph. If unique is False and
        we do not already have a node with the supplied name then we create a
        new one. If unique is True then we always create a new node. If a
        mapping is supplied then it is used to name the node. '''

        if not name and not variable:
            raise Exception("get_node: one of 'name' or 'variable' must "
                            "be supplied")
        if not name:
            name = str(variable)

        if unique:
            # Node is unique so we make a new one, no questions asked.
            if DEBUG:
                print "Creating a unique node labelled '{0}'".format(name)
            node = DAGNode(parent=parent, name=name, digraph=self,
                           variable=variable)
            # Store this node in our list using its unique ID in place of a
            # name (since a unique node has been requested). This then
            # ensures we have a list of all nodes in the graph.
            self._nodes[node.node_id] = node
        else:
            if mapping and name in mapping:
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
                node = DAGNode(parent=parent, name=node_name,
                               variable=variable)
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
        # Remove this node from any node that has it as a child (dependency)
        for pnode in node._has_as_child[:]:
            pnode.children.remove(node)
        # Finally, delete it altogether
        del node

    def delete_sub_graph(self, node):
        ''' Recursively deletes the supplied node *and all of its
        dependencies/children" '''
        node_list = node.walk()
        for child in node_list:
            if not child.is_dependent:
                self.delete_node(child)
        if not node.is_dependent:
            self.delete_node(node)

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
        # List of distinct array references
        array_refs = []
        # Loop over all nodes in the tree, looking for array references
        ancestors = self.ancestor_nodes()
        for ancestor in ancestors:
            nodes = ancestor.walk("array_ref")
            for node in nodes:
                # We care about the name of the array and the value of
                # anything other than the first index (assuming that any
                # accesses that differ only in the first index are all
                # fetched in the same cache line).
                key = node._variable.name
                for index in node.variable.indices[1:]:
                    key += "_" + index
                if key not in array_refs:
                    array_refs.append(key)
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
        from parse2003 import Variable

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
                    opnode = self.get_node(parent, mapping, name=child,
                                           unique=True, node_type=child)
                    parent.add_child(opnode)
                    parent = opnode
                    opcount += 1
        if opcount > 1:
            raise Exception("Found more than one operator amongst list of "
                            "siblings: this is not supported!")

        for child in children:
            if isinstance(child, Name):
                var = Variable()
                var.load(child, mapping)
                tmpnode = self.get_node(parent, mapping,
                                        variable=var)
                parent.add_child(tmpnode)
            elif isinstance(child, Real_Literal_Constant):
                # This is a constant and thus a leaf in the tree
                const_var = Variable()
                const_var.load(child, mapping)
                tmpnode = self.get_node(parent, mapping,
                                        variable=const_var,
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
                    tmpnode = self.get_node(parent, mapping,
                                            name=str(child.items[0]),
                                            unique=True,
                                            node_type="intrinsic")
                    parent.add_child(tmpnode)
                    # Add its dependencies
                    self.make_dag(tmpnode, child.items[1:], mapping)
                else:
                    # Assume it's an array reference
                    from parse2003 import Variable
                    arrayvar = Variable()
                    arrayvar.load(child, mapping)
                    tmpnode = self.get_node(parent, mapping,
                                            variable=arrayvar,
                                            node_type="array_ref")
                    parent.add_child(tmpnode)
                    # Include the array index expression in the DAG
                    #self.make_dag(tmpnode, child.items, mapping)
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

    def prune_duplicate_nodes(self):
        ''' Walk through the graph and remove all but-one of any
        duplicated sub-graphs that represent FLOPs'''
        # Use a dictionary of lists to store the nodes that are instances
        # of each of our types of FLOP
        op_list = {}
        for opname in OPERATORS:
            op_list[opname] = []
        # _nodes is a dictionary - we want the values, not the keys
        for node in self._nodes.itervalues():
            if node.node_type in OPERATORS:
                op_list[node.node_type].append(node)

        for opname in OPERATORS:
            for idx, node1 in enumerate(op_list[opname][:-1]):
                for node2 in op_list[opname][idx+1:]:
                    if subgraph_matches(node1, node2):
                        print "{0} matches {1}".format(str(node1), str(node2))
                        # Create a new node to store the result of this
                        # duplicated operation
                        new_node = self.get_node(node1.parent, name="andy",
                                                 unique=True)
                        # Make this new node depend on node1
                        new_node.add_child(node1)
                        # Add the new node as a dependency for those nodes
                        # that previously had either node1 or node2 as
                        # children
                        node1.parent.add_child(new_node)
                        node2.parent.add_child(new_node)
                        node1.parent.rm_child(node1)
                        node2.parent.rm_child(node2)
                        self.delete_sub_graph(node2)
                    
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

    def __init__(self, parent=None, name=None, digraph=None, variable=None):
        self._parent = parent
        # Keep a reference back to the digraph object containing
        # this node
        self._digraph = digraph
        # The list of nodes upon which this node has a dependence
        self._children = []
        # The list of nodes that have a dependence upon this node
        # TODO what is the correct name for such nodes?
        self._has_as_child = []
        # The name of this node - used to label the node in DOT
        self._name = name
        # The type of this node
        self._node_type = None
        # The variable (if any) that this node represents
        self._variable = variable
        # The inclusive weight (cost) of this node. This is the cost of
        # this node plus that of all of its descendants. This then
        # enables us to find the critical path through the graph.
        self._incl_weight = 0

    def __str__(self):
        return self.name

    @property
    def node_id(self):
        ''' Returns a unique string identifying this node in the graph '''
        return "node"+str(id(self))

    @property
    def name(self):
        ''' Returns the name (label) of this node '''
        if self._variable:
            return str(self._variable)
        else:
            return self._name

    @name.setter
    def name(self, new_name):
        ''' Set (or change) the name/label of this node. Note that if there
        is a Variable associated with this node then the name of that
        object overrides this. '''
        self._name = new_name

    def display(self, indent=0):
        ''' Prints a textual representation of this node to stdout '''
        print indent*INDENT_STR, self.name
        for child in self._children:
            child.display(indent=indent+1)

    def add_child(self, child):
        ''' Add a child to this node '''
        self._children.append(child)
        child.depended_on_by(self)

    def rm_child(self, child):
        ''' Remove a child from this node '''
        if child not in self._children:
            raise DAGError("Node {0} is not a child of this node ({1}".
                           format(str(child), str(self)))
        # Remove it from the list of children
        self._children.remove(child)
        # Modify the object itself now that this one no longer has it
        # as a child (dependency)
        child._has_as_child.remove(self)

    def depended_on_by(self, node):
        ''' Add the supplied node to the list of nodes that have this one as
        a dependency (child) '''
        if node not in self._has_as_child:
            self._has_as_child.append(node)

    def is_dependent(self):
        ''' Returns true if one or more nodes have this node as a
        dependency '''
        if self._has_as_child:
            return True
        return False

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

    @property
    def variable(self):
        ''' Return the Variable object associated with this node or None
        if there isn't one '''
        return self._variable

    def walk(self, node_type=None):
        ''' Walk down the tree from this node and generate a list of all
        nodes of type node_type. If no node type is supplied then return
        all descendents '''
        local_list = []
        for child in self._children:
            local_list += child.walk(node_type)
            if not node_type or child.node_type == node_type:
                local_list.append(child)
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
                                                    self.name,
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
        if self._children:
            fileobj.write(self.node_id+" -> {\n")
            for child in self._children:
                fileobj.write(" "+child.node_id)
            fileobj.write("}\n")
