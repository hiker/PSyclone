#!/usr/bin/env python

''' A python script to parse a Fortran source file and produce a DAG
    for each subroutine it contains. '''

from dag import DirectedAcyclicGraph
from parse2003 import walk

try:
    from iocbio.optparse_gui import OptionParser
except ImportError:
    from optparse import OptionParser
from fparser.script_options import set_f2003_options

# How many times to attempt to unroll each loop
UNROLL_FACTOR = 2


def unroll_loop(digraph, loop, mapping=None):
    ''' Unroll the body of the loop represented by the DAG in digraph '''
    import copy

    if UNROLL_FACTOR == 1:
        return

    # Create a node to represent the loop index
    loopidx_node = digraph.get_node(parent=None,
                                    mapping=mapping,
                                    name=loop.var_name)

    # Create a temporary variable in place of the loop index and assign
    # the value of the loop index to it - this just gives us a 
    # dependency.
    counter_name = "uridx"
    counter_node = digraph.get_node(loopidx_node,
                                    mapping=mapping,
                                    name=counter_name)
    loopidx_node.add_child(counter_node)

    # Rename the loop variable in the original loop body
    digraph.rename_nodes(loop.var_name, "uridx")

    # Increment the loop counter and thus create a 'new' object
    counter_name += "'"

    plus = digraph.get_node(counter_node,
                            mapping,
                            name="+",
                            unique=True,
                            node_type="+")
    one = digraph.get_node(counter_node,
                           mapping,
                           name="1",
                           unique=True,
                           node_type="constant")
    counter_node = digraph.get_node(counter_node,
                                    mapping=mapping,
                                    name=counter_name)

    # Take a copy of the loop body
    digraph2 = copy.deepcopy(digraph)
    digraph2.rename_nodes("uridx", "uridx'")
    digraph.extend(digraph2)

    return

    for unroll_count in range(1, UNROLL_FACTOR):
        # Increment loop variable
        new_node = digraph.get_node(parent=None,
                                    mapping=mapping,
                                    name=myloop.var_name)
        plus = new_node.digraph.get_node(name="+",
                                         unique=True,
                                         node_type="+")
        one = new_node.digraph.get_node(name="1",
                                        unique=True,
                                        node_type="constant")

        # Duplicate body of digraph with this new
        # 'value' of the loop variable
        pass


def dag_of_code_block(parent_node, name, loop=None):
    ''' Creates and returns a DAG for the code that is a child of the
    supplied node '''
    from fparser.Fortran2003 import Assignment_Stmt, Name
    from parse2003 import Variable

    # Create a new DAG object
    digraph = DirectedAcyclicGraph(name)

    # Keep a list of variables that are assigned to. This
    # enables us to update the name by which they are known
    # in the graph.
    # e.g.:
    #  a = b + c
    #  a = a + 1 =>  a' = a + 1
    #  a = a*a   => a'' = a' * a'
    mapping = {}

    # Find all of the assignment statements in the code block
    if hasattr(parent_node, "items"):
        assignments = walk(parent_node.items, Assignment_Stmt)
    else:
        assignments = walk(parent_node.content, Assignment_Stmt)

    if not assignments:
        # If this subroutine has no assignment statements
        # then we skip it
        print "Code {0} contains no assignment statements - skipping".\
            format(name)
        return None

    for assign in assignments:
        lhs = Variable()
        lhs.load(assign.items[0], mapping)
        var_name = str(lhs)

        # If this variable has been assigned to previously
        # then this is effectively a new variable for the
        # purposes of the graph.
        if var_name in mapping:
            node_name = mapping[var_name] + "'"
            lhs.name = node_name
        else:
            node_name = var_name
        dag = digraph.get_node(parent=None,
                               mapping=mapping,
                               variable=lhs)
        # First two items of an Assignment_Stmt are the name of
        # the var being assigned to and '='.
        digraph.make_dag(dag, assign.items[2:], mapping)

        # Only update the map once we've created a DAG of the
        # assignment statement. This is because any references
        # to this variable in that assignment are to the previous
        # version of it, not the one being assigned to.
        if var_name in mapping:
            mapping[var_name] += "'"
        else:
            mapping[var_name] = var_name

    # If this code block is the body of a loop then unroll it...
    if loop:
        unroll_loop(digraph, loop, mapping)

    # Work out the critical path through this graph
    path = digraph.calc_critical_path()

    return digraph

    
def runner(parser, options, args):
    ''' Parses the files listed in args and generates a DAG for all of the
    subroutines it finds '''
    from fparser.api import Fortran2003
    from fparser.readfortran import FortranFileReader
    from fparser.Fortran2003 import Subroutine_Subprogram, Assignment_Stmt, \
        Subroutine_Stmt, Name, Block_Nonlabel_Do_Construct, Execution_Part
    from parse2003 import Loop

    apply_fma_transformation = False

    for filename in args:
        reader = FortranFileReader(filename)
        if options.mode != 'auto':
            reader.set_mode_from_str(options.mode)
        try:
            program = Fortran2003.Program(reader)
            # Find all the subroutines contained in the file
            subroutines = walk(program.content, Subroutine_Subprogram)

            # Create a DAG for each subroutine
            for subroutine in subroutines:
                substmt = walk(subroutine.content, Subroutine_Stmt)
                sub_name = str(substmt[0].get_name())
                
                # Make a list of all Do loops in the routine
                loops = walk(subroutine.content, Block_Nonlabel_Do_Construct)
                digraphs = []
                
                if not loops:
                    # There are no Do loops in this subroutine so just
                    # generate a DAG for the body of the routine...
                    # First, find the executable section of the subroutine
                    exe_part = walk(subroutine.content, Execution_Part)
                    # Next, generate the DAG of that section
                    digraph = dag_of_code_block(exe_part[0], sub_name)
                    if digraph:
                        digraphs.append(digraph)
                else:
                    # Create a DAG for the body of each innermost loop
                    loop_count = 0
                    for loop in loops:

                        # Check that we are an innermost loop
                        inner_loops = walk(loop.content,
                                           Block_Nonlabel_Do_Construct)
                        if inner_loops:
                            # We're not so skip
                            continue

                        loop_count += 1

                        # Create a Loop object for this loop
                        myloop = Loop()
                        myloop.load(loop)

                        digraph = dag_of_code_block(
                            loop, sub_name+"_loop"+str(loop_count),
                            loop=myloop)
                        if digraph:
                            digraphs.append(digraph)

                for digraph in digraphs:
                    # Write the digraph to file
                    digraph.to_dot()
                    digraph.report()

                    # Fuse multiply-adds where possible
                    if apply_fma_transformation:
                        digraph.fuse_multiply_adds()
                        digraph.name = digraph.name + "_fused"
                        # Re-compute the critical path through this graph
                        path = digraph.calc_critical_path()
                        digraph.to_dot()
                        digraph.report()

        except Fortran2003.NoMatchError:
            print 'parsing %r failed at %s' % (filename, reader.fifo_item[-1])
            print 'started at %s' % (reader.fifo_item[0])
            print 'Quitting'
            return


def main():
    parser = OptionParser()
    set_f2003_options(parser)
    if hasattr(parser, 'runner'):
        parser.runner = runner
    options, args = parser.parse_args()
    runner(parser, options, args)
    return


if __name__=="__main__":
    main()
