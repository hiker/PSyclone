
''' This module provides support for the construction of a Directed
    Acyclic Graph. '''

from fparser.Fortran2003 import \
    Add_Operand, Level_2_Expr, Level_2_Unary_Expr, Real_Literal_Constant, \
    Name, Section_Subscript_List, Parenthesis, Part_Ref

from dag_node import DAGNode, DAGError
from config_ivy_bridge import OPERATORS, CACHE_LINE_BYTES, EXAMPLE_CLOCK_GHZ, \
    FORTRAN_INTRINSICS

DEBUG = False


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
    matches = True
    if node1.name != node2.name:
        matches = False
    if len(node1.producers) != len(node2.producers):
        matches = False
    if node1.node_type != node2.node_type:
        matches = False
    # TODO correct the code that stores the denominator of any division
    # operations
    # if node1.node_type == "/":
    #    if node1.operands[0] != node2.operands[0]:
    #        matches = False
    elif node1.node_type == "FMA":
        # Check that the two nodes being multiplied are the same
        if node1.operands[0] not in node2.operands or \
           node1.operands[1] not in node2.operands:
            matches = False
    for child1 in node1.producers:
        found = False
        # We can't assume that the two lists of children have the same
        # ordering...
        for child2 in node2.producers:
            # Recurse down
            if subgraph_matches(child1, child2):
                found = True
                break
        if not found:
            matches = False
    return matches


# TODO: would it be better to inherit from the built-in list object?
class Path(object):
    ''' Class to encapsulate functionality related to a specifc path
    through a DAG '''

    def __init__(self):
        self._nodes = []

    @property
    def nodes(self):
        ''' Returns the list of nodes in this Path '''
        return self._nodes

    def load(self, obj_list):
        ''' Populate this object using the supplied list of nodes '''
        self._nodes = obj_list

    def add_node(self, obj):
        ''' Add a node to this path '''
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
        # The critical path through the graph
        self._critical_path = Path()
        # Counter for duplicate sub-expressions (for naming the node
        # used to store the result)
        self._sub_exp_count = 0

    @property
    def name(self):
        ''' Returns the name of this DAG. This is (normally) derived from
        the subroutine containing the Fortran code from which it is
        generated. '''
        return self._name

    @name.setter
    def name(self, new_name):
        ''' Set the name of this DAG '''
        self._name = new_name

    def get_node(self, parent=None, mapping=None, name=None, unique=False,
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
                # Record the fact that the parent now has a dependence
                # on this node and that this node is consumed by the parent
                if parent:
                    parent.add_producer(node)
                    node.add_consumer(parent)
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
        # Remove this node from any node that has it as a producer (dependency)
        for pnode in node.consumers[:]:
            pnode.rm_producer(node)
        # Finally, delete it altogether
        del node

    def delete_sub_graph(self, node):
        ''' Recursively deletes the supplied node *and all of its
        dependencies/children* '''
        node_list = node.walk(top_down=True)
        if not node.has_consumer:
            self.delete_node(node)
        for child in node_list:
            # We only delete the node if no other node has it as a
            # dependency (child)
            if not child.has_consumer:
                self.delete_node(child)
            else:
                if DEBUG:
                    print "Not deleting child {0}. Has consumers:".\
                        format(str(child))
                    for dep in child.consumers:
                        print str(dep)

    def output_nodes(self):
        ''' Returns a list of all nodes that do not have a a node
        that is dependent upon them - i.e. a consumer.
        These are outputs of the DAG. '''
        node_list = []
        for node in self._nodes.itervalues():
            if not node.has_consumer:
                node_list.append(node)
        return node_list

    def input_nodes(self):
        ''' Returns a list of all nodes that do not have any producers
        (dependencies). These are inputs to the DAG. '''
        node_list = []
        for node in self._nodes.itervalues():
            if not node.has_producer:
                node_list.append(node)
        return node_list

    def count_nodes(self, node_type):
        ''' Count the number of nodes in the graph that are of the
        specified type '''
        ancestors = self.output_nodes()
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
        ancestors = self.output_nodes()
        for ancestor in ancestors:
            nodes = ancestor.walk("array_ref")
            for node in nodes:
                # We care about the name of the array and the value of
                # anything other than the first index (assuming that any
                # accesses that differ only in the first index are all
                # fetched in the same cache line).
                key = node.variable.name
                for index in node.variable.indices[1:]:
                    key += "_" + index
                if key not in array_refs:
                    array_refs.append(key)
        return len(array_refs)

    def calc_costs(self):
        ''' Analyse the DAG and calculate a weight for each node. '''
        ancestors = self.output_nodes()
        for node in ancestors:
            node.calc_weight()

    def total_cost(self):
        ''' Calculate the total cost of the graph by summing up the cost of
        each node '''
        cost = 0
        for node in self._nodes.itervalues():
            cost += node.weight
        return cost

    def fuse_multiply_adds(self):
        ''' Processes the existing graph and creates FusedMultiplyAdds
        where possible. Returns the number of FMAs created. '''
        num_fma = 0
        ancestors = self.output_nodes()
        for node in ancestors:
            num_fma += node.fuse_multiply_adds()
        return num_fma

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
        is_division = False
        for child in children:
            if isinstance(child, str):
                if child in OPERATORS:
                    # This is the operator which is then the parent
                    # of the DAG of this subexpression. All operators
                    # are unique nodes in the DAG.
                    opnode = self.get_node(parent, mapping, name=child,
                                           unique=True, node_type=child)
                    parent = opnode
                    is_division = (child == "/")
                    opcount += 1
        if opcount > 1:
            raise Exception("Found more than one operator amongst list of "
                            "siblings: this is not supported!")

        for idx, child in enumerate(children):
            if isinstance(child, Name):
                var = Variable()
                var.load(child, mapping)
                tmpnode = self.get_node(parent, mapping,
                                        variable=var)
                if is_division and idx == 2:
                    parent.operands.append(tmpnode)
            elif isinstance(child, Real_Literal_Constant):
                # This is a constant and thus a leaf in the tree
                const_var = Variable()
                const_var.load(child, mapping)
                tmpnode = self.get_node(parent, mapping,
                                        variable=const_var,
                                        unique=True,
                                        node_type="constant")
                if is_division and idx == 2:
                    parent.operands.append(tmpnode)
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
                    if is_division and idx == 2:
                        parent.operands.append(tmpnode)
                    # Add its dependencies
                    self.make_dag(tmpnode, child.items[1:], mapping)
                else:
                    # Assume it's an array reference
                    arrayvar = Variable()
                    arrayvar.load(child, mapping)
                    tmpnode = self.get_node(parent, mapping,
                                            variable=arrayvar,
                                            node_type="array_ref")
                    if is_division and idx == 2:
                        parent.operands.append(tmpnode)
                    # Include the array index expression in the DAG
                    # self.make_dag(tmpnode, child.items, mapping)
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
        for node in self.output_nodes():
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

    def nodelist_by_type(self, ntype):
        ''' Returns a list of all nodes in this DAG that have the
        specified type '''
        from dag_node import VALID_NODE_TYPES
        if ntype not in VALID_NODE_TYPES:
            raise DAGError("Got a node type of {0} but expected one of {1}".
                           format(ntype, VALID_NODE_TYPES))
        op_list = []
        # _nodes is a dictionary - we want the values, not the keys
        for node in self._nodes.itervalues():
            if node.node_type == ntype:
                op_list.append(node)
        return op_list

    def rm_scalar_temporaries(self):
        ''' Remove any nodes that represent scalar temporaries. These are
        identified as any node that is not an operator and has just
        one consumer and one producer. '''
        dead_nodes = []
        # _nodes is a dictionary - we want the values, not the keys
        for node in self._nodes.itervalues():
            if node.node_type not in OPERATORS:
                if len(node.producers) == 1 and \
                   len(node.consumers) == 1:
                    cnode = node.consumers[0]
                    pnode = node.producers[0]
                    # Remove the refs to this node in the consumer and producer
                    cnode.rm_producer(node)
                    pnode.rm_consumer(node)
                    # Make the consumer depend on the producer
                    cnode.add_producer(pnode)
                    pnode.add_consumer(cnode)
                    # Remove the dependencies from this node
                    node.rm_producer(pnode)
                    node.rm_consumer(cnode)
                    # Add this node to our list to remove - saves
                    # attempting to modify the contents of the dict
                    # while iterating over it.
                    dead_nodes.append(node)

        # Finally, remove all of the nodes marked for deletion.
        for node in dead_nodes:
            self.delete_node(node)

    def prune_duplicate_nodes(self):
        ''' Walk through the graph and remove all but one of any
        duplicated sub-graphs that represent FLOPs'''

        for opname in OPERATORS:

            op_list = self.nodelist_by_type(opname)
            if not op_list or len(op_list) == 1:
                continue
            found_duplicate = True

            # Keep looping until we no longer find duplicate sub-expressions
            # involving the current operator
            while found_duplicate:

                for idx, node1 in enumerate(op_list[:-1]):
                    # Construct a list of nodes (sub-graphs really) that
                    # match node1
                    matching_nodes = []
                    for node2 in op_list[idx+1:]:
                        if subgraph_matches(node1, node2):
                            matching_nodes.append(node2)

                    if matching_nodes:
                        found_duplicate = True

                        # Create a new node to store the result of this
                        # duplicated operation
                        new_node = self.get_node(
                            name="sub_exp"+str(self._sub_exp_count),
                            unique=True)
                        # Increment the count of duplicate sub-expressions
                        self._sub_exp_count += 1

                        # Make this new node depend on node1
                        new_node.add_producer(node1)
                        # Each node that had node1 as a dependency must now
                        # have that replaced by new_node...
                        for pnode in node1.consumers[:]:
                            pnode.add_producer(new_node)
                            pnode.rm_producer(node1)
                            node1.rm_consumer(pnode)

                        for node2 in matching_nodes:
                            # Add the new node as a dependency for those nodes
                            # that previously had node2 as a child
                            for pnode in node2.consumers[:]:
                                pnode.add_producer(new_node)
                                pnode.rm_producer(node2)
                                node2.rm_consumer(pnode)

                            # Delete node2 and all of its dependencies
                            # (children)
                            self.delete_sub_graph(node2)

                        # Need to re-generate list of nodes for this operator
                        op_list = self.nodelist_by_type(opname)

                        # Break out to re-start search for duplicates
                        break
                    else:
                        found_duplicate = False

    @property
    def critical_path(self):
        return self._critical_path

    def to_dot(self, name=None):
        ''' Write the DAG to file in DOT format. If a critical path has
        been computed then it is also written to the file. '''

        if name:
            filename = name
        else:
            filename = self._name + ".gv"

        # Create a file for the graph of this subroutine
        outfile = open(filename, "w")
        outfile.write("strict digraph {\n")

        for node in self.output_nodes():
            node.to_dot(outfile)

        # Write the critical path
        if len(self._critical_path):
            self._critical_path.to_dot(outfile)

        outfile.write("}\n")
        print "Wrote DAG to {0}".format(outfile.name)
        outfile.close()

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
        # TODO how do we count FLOPs for e.g. sin() and cos()?
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

        if num_cache_ref > 0:
            flop_per_byte = total_flops / (num_cache_ref*8.0)
            # This is naive because all FLOPs are not equal - a division
            # costs ~20-40x as much as an addition.
            print "  Naive FLOPs/byte = {:.3f}".format(flop_per_byte)
        else:
            print "  Did not find any array/memory references"

        # Execution of the DAG requires that num_cache_ref cache lines
        # be fetched from (somewhere in) the memory hierarchy...
        mem_traffic_bytes = num_cache_ref * CACHE_LINE_BYTES

        # Performance estimate using whole graph. This is a lower bound
        # since it ignores all Instruction-Level Parallelism apart from
        # FMAs...
        min_flops_per_hz = float(total_flops)/float(total_cycles)
        print "  Lower bound:"
        print "    Sum of cost of all nodes = {0} (cycles)".\
            format(total_cycles)
        print "    {0} FLOPs in {1} cycles => {2:.4f}*CLOCK_SPEED FLOPS".\
            format(total_flops, total_cycles, min_flops_per_hz)
        if num_cache_ref:
            min_mem_bw = float(mem_traffic_bytes) / float(total_cycles)
            print ("    Associated mem bandwidth = {0:.2f}*CLOCK_SPEED "
                   "bytes/s".format(min_mem_bw))

        # Performance estimate using critical path - this is an upper
        # bound (assumes all other parts of the graph can somehow be
        # computed in parallel to the critical path).
        print "  Upper bound:"
        ncycles = self._critical_path.cycles()
        print ("    Critical path contains {0} nodes, {1} FLOPs and "
               "is {2} cycles long".format(len(self._critical_path),
                                           self._critical_path.flops(),
                                           ncycles))
        # Graph contains total_flops and will execute in at
        # least path.cycles() CPU cycles. A cycle has duration
        # 1/CLOCK_SPEED (s) so kernel will take at least
        # path.cycles()*1/CLOCK_SPEED (s).
        # Theoretical max FLOPS = total_flops*CLOCK_SPEED/path.cycles()
        max_flops_per_hz = float(total_flops)/float(ncycles)
        print ("    Theoretical max FLOPS (ignoring memory accesses) = "
               "{:.4f}*CLOCK_SPEED".format(max_flops_per_hz))

        if num_cache_ref:
            # Kernel/DAG will take at least ncycles/CLOCK_SPEED (s)
            max_mem_bw = float(mem_traffic_bytes) / float(ncycles)
            print ("    Associated mem bandwidth = {0:.2f}*CLOCK_SPEED "
                   "bytes/s".format(max_mem_bw))

        # Print out example performance figures using the clock speed
        # in EXAMPLE_CLOCK_GHZ
        eg_string = ("  e.g. at {0} GHz, this gives {1:.2f}-{2:.2f} GFLOPS".
                     format(EXAMPLE_CLOCK_GHZ,
                            min_flops_per_hz*EXAMPLE_CLOCK_GHZ,
                            max_flops_per_hz*EXAMPLE_CLOCK_GHZ))
        if num_cache_ref:
            eg_string += (" with associated BW of {0:.2f}-{1:.2f} GB/s".format(
                      min_mem_bw*EXAMPLE_CLOCK_GHZ,
                      max_mem_bw*EXAMPLE_CLOCK_GHZ))
        print eg_string

        # Which execution port each f.p. operation is mapped to on the CPU
        # TODO this is microarchitecture specific
        exec_port = {"/": 0, "*": 0, "+": 1, "-": 1}
        num_ports = 2

        output_dot_schedule = True

        if output_dot_schedule:
            self.to_dot(name=self._name+"_step0.gv")

        # Flag all input nodes as being ready
        input_nodes = self.input_nodes()
        for node in input_nodes:
            node._ready = True

        # Construct a schedule
        step = 0
        # We have one slot per execution port at each step in the schedule.
        # Each port then has its own schedule (list) with entries being the
        # DAGNodes representing the operations to be performed or None
        # if a slot is empty (nop).
        slot = []
        for port in range(num_ports):
            slot.append([None])

        # Generate a list of all operations that have their dependencies
        # satisfied and are thus ready to go
        available_ops = self.operations_ready()

        while available_ops:

            if output_dot_schedule:
                self.to_dot(name=self._name+"_step{0}.gv".format(step+1))

            # Attempt to schedule each operation
            for operation in available_ops:
                if not slot[exec_port[operation.node_type]][step]:
                    # Put this operation into next slot on appropriate port
                    slot[exec_port[operation.node_type]][step] = operation
                    # Mark the operation as done (executed)
                    operation._ready = True
            for port in range(num_ports):
                # Prepare the next slot in the schedule on this port
                slot[port].append(None)

            # Update all dependencies in the graph following the
            # execution of one or more operations
            # TODO could just update the consumers of those operations
            self.update_status()

            # Update our list of operations that are now ready to be
            # executed
            available_ops = self.operations_ready()
            # Move on to the next step in the schedule that we are
            # constructing
            step += 1

            if step > 500:
                raise Exception("Unexpectedly long schedule - this is "
                                "probably a bug.")

        nsteps = step
        print "Schedule contains {0} steps:".format(nsteps)
        for step in range(0, nsteps):
            sched_str = str(step)
            for port in range(num_ports):
                sched_str += " {0}".format(slot[port][step])
            print sched_str
            

    def update_status(self):
        ''' Examine all the nodes in the graph and mark as 'ready' all
        those quantities whose producers are now 'ready'. '''
        for node in self._nodes.itervalues():
            if not node._ready and \
               node.node_type not in OPERATORS:
                # Operators only become ready by being executed (put in
                # the schedule) and so their status is not updated here
                node._ready = node.dependencies_satisfied

    def operations_ready(self):
        ''' Create a list of all operations in the DAG that are ready to
        be executed (all producers are 'ready') '''
        available_ops = []
        for node in self._nodes.itervalues():
            if (not node._ready and
                node.node_type in OPERATORS and
                node.dependencies_satisfied and
                node not in available_ops):
                available_ops.append(node)
        return available_ops
