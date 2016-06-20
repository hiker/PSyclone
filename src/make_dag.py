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
UNROLL_FACTOR = 3


def dag_of_assignments(digraph, assignments, mapping):
    ''' Add to the existing DAG using the supplied list of assignments '''
    from parse2003 import Variable

    for assign in assignments:
        lhs_var = Variable()
        lhs_var.load(assign.items[0], mapping=mapping, lhs=True)
        var_name = str(lhs_var)

        dag = digraph.get_node(parent=None,
                               variable=lhs_var)
        # First two items of an Assignment_Stmt are the name of
        # the var being assigned to and '='.
        digraph.make_dag(dag, assign.items[2:], mapping)

        # Only update the map once we've created a DAG of the
        # assignment statement. This is because any references
        # to this variable in that assignment are to the previous
        # version of it, not the one being assigned to.
        if lhs_var.orig_name in mapping:
            mapping[lhs_var.orig_name] += "'"
        else:
            mapping[lhs_var.orig_name] = lhs_var.orig_name


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
 
    if loop:
        # Put the loop variable in our mapping
        mapping[loop.var_name] = loop.var_name

    dag_of_assignments(digraph, assignments, mapping)
    print mapping

    if loop:
        for repeat in range(1, UNROLL_FACTOR):
            # Increment the loop counter and then add to the DAG again
            mapping[loop.var_name] += "+1"
            print "New loop variable is '{0}'".format(mapping[loop.var_name])
            dag_of_assignments(digraph, assignments, mapping)
            print mapping

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
