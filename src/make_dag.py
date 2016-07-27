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


def dag_of_code_block(parent_node, name, loop=None, unroll_factor=1):
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

    if loop:
        for repeat in range(1, unroll_factor):
            # Increment the loop counter and then add to the DAG again
            mapping[loop.var_name] += "+1"
            dag_of_assignments(digraph, assignments, mapping)

    # Correctness check - if we've ended up with e.g. my_var' as a key
    # in our name-mapping dictionary then something has gone wrong.
    for name in mapping:
        if "'" in name:
            raise ParseError(
                "Found {0} in name map but names with ' characters "
                "appended should only appear in the value part of "
                "the dictionary")

    return digraph

    
def runner(parser, options, args):
    ''' Parses the files listed in args and generates a DAG for all of the
    subroutines it finds '''
    from fparser.api import Fortran2003
    from fparser.readfortran import FortranFileReader
    from fparser.Fortran2003 import Subroutine_Subprogram, Assignment_Stmt, \
        Subroutine_Stmt, Name, Block_Nonlabel_Do_Construct, Execution_Part
    from parse2003 import Loop

    apply_fma_transformation = not options.no_fma
    prune_duplicate_nodes = not options.no_prune
    unroll_factor = int(options.unroll_factor)
    rm_scalar_temporaries = options.rm_scalar_tmps
    show_weights = options.show_weights

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

                        # Create a Loop object for this loop
                        myloop = Loop()
                        myloop.load(loop)

                        # Generate a suitable name for this DAG
                        name = sub_name + "_loop" + str(loop_count)
                        if unroll_factor > 1:
                            name += "_unroll" + str(unroll_factor)

                        digraph = dag_of_code_block(
                            loop, name,
                            loop=myloop,
                            unroll_factor=unroll_factor)
                        if digraph:
                            digraphs.append(digraph)

                        # Increment count of (inner) loops found
                        loop_count += 1


                for digraph in digraphs:

                    if prune_duplicate_nodes:
                        digraph.prune_duplicate_nodes()

                    if rm_scalar_temporaries:
                        digraph.rm_scalar_temporaries()

                    # Work out the critical path through this graph
                    digraph.calc_critical_path()

                    # Write the digraph to file
                    digraph.to_dot(show_weights=show_weights)
                    digraph.report()

                    # Fuse multiply-adds where possible
                    if apply_fma_transformation:
                        num_fused = digraph.fuse_multiply_adds()
                        if num_fused:
                            digraph.name = digraph.name + "_fused"
                            # Re-compute the critical path through this graph
                            digraph.calc_critical_path()
                            digraph.to_dot()
                            digraph.report()
                        else:
                            print "No opportunities to fuse multiply-adds"

        except Fortran2003.NoMatchError:
            print 'parsing %r failed at %s' % (filename, reader.fifo_item[-1])
            print 'started at %s' % (reader.fifo_item[0])
            print 'Quitting'
            return


def main():
    parser = OptionParser()
    set_f2003_options(parser)
    parser.add_option("--no-prune",
                      help="Do not attempt to prune duplicate operations "
                      "from the graph",
                      action="store_true",
                      dest="no_prune",
                      default=False)
    parser.add_option("--no-fma",
                      help="Do not attempt to generate fused multiply-add "
                      "operations",
                      action="store_true",
                      dest="no_fma",
                      default=False)
    parser.add_option("--rm-scalar-tmps",
                      help="Remove scalar temporaries from the DAG",
                      action="store_true",
                      dest="rm_scalar_tmps",
                      default=False)
    parser.add_option("--show-weights",
                      help="Display node weights in the DAG",
                      action="store_true",
                      dest="show_weights",
                      default=False)
    parser.add_option("--unroll",
                      help="No. of times to unroll a loop. (Applied to every "
                      "loop that is encountered.)",
                      metavar="UNROLL_FACTOR",
                      action="store",
                      type="int",
                      dest="unroll_factor",
                      default=1)
    if hasattr(parser, 'runner'):
        parser.runner = runner
    options, args = parser.parse_args()

    runner(parser, options, args)
    return


if __name__=="__main__":
    main()
