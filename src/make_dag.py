#!/usr/bin/env python

''' A python script to parse a Fortran source file and produce a DAG
    for each subroutine it contains. '''

from fparser.Fortran2003 import Subroutine_Subprogram, Assignment_Stmt, \
    Subroutine_Stmt, Name
from dag import DirectedAcyclicGraph, str_to_node_name

try:
    from iocbio.optparse_gui import OptionParser
except ImportError:
    from optparse import OptionParser
from fparser.script_options import set_f2003_options


def walk(children, my_type):
    '''' Walk down the tree produced by the f2003 parser where children
    are listed under 'content'.  Returns a list of all nodes with the
    specified type. '''
    local_list = []
    for child in children:
        if isinstance(child, my_type):
            local_list.append(child)
        try:
            local_list += walk(child.content, my_type)
        except AttributeError:
            pass
    return local_list

def walk_items(children, my_type):
    ''' Walk down tree produced by f2003 parser where child nodes are listed
    under items '''
    from fparser.Fortran2003 import Section_Subscript_List
    ignore_types = [Section_Subscript_List]
    local_list = []
    # children is a tuple
    for idx, child in enumerate(children):
        # Drop anything that is a child of any of our
        # ignored types
        if type(child) in ignore_types:
            continue
        if isinstance(child, Name):
            suffix = ""
            if idx < len(children)-1 and isinstance(children[idx+1],
                                                   Section_Subscript_List):
                # This is an array reference
                suffix = "_" + str_to_node_name(str(children[idx+1]))
            local_list.append(str(child)+suffix)
        try:
            local_list += walk_items(child.items, my_type)
        except AttributeError:
            # Catch case where child does not have items member
            pass
    return local_list


def runner(parser, options, args):
    ''' Parses the files listed in args and generates a DAG for all of the
    subroutines it finds '''
    from fparser.api import Fortran2003
    from fparser.readfortran import FortranFileReader
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

                # Create a file for the graph of this subroutine
                fo = open(sub_name+".gv", "w")

                digraph = DirectedAcyclicGraph(sub_name)
                fo.write("strict digraph {\n")

                # Keep a list of variables that are assigned to. This
                # enables us to update the name by which they are known
                # in the graph.
                # e.g.:
                #  a = b + c
                #  a = a + 1 =>  a' = a + 1
                #  a = a*a   => a'' = a' * a'
                mapping = {}

                # Find all of the assignment statements in the subroutine
                assignments = walk(subroutine.content, Assignment_Stmt)
                for assign in assignments:
                    assigned_to = walk_items([assign.items[0]], Name)
                    var_name = str(assigned_to[0])
                    # If this variable has been assigned to previously
                    # then this is effectively a new variable for the
                    # purposes of the graph.
                    if var_name in mapping:
                        node_name = mapping[var_name] + "'"
                    else:
                        node_name = var_name
                    dag = digraph.get_node(name=node_name,
                                           parent=None,
                                           mapping=mapping)
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

                    # Output the DAG of this assignment
                    #dag.display()
                    dag.to_dot(fo)
                fo.write("}\n")
                print "Wrote DAG to {0}".format(fo.name)
                fo.close()

                num_plus = digraph.count_nodes("+")
                num_minus = digraph.count_nodes("-")
                num_mult = digraph.count_nodes("*")
                num_div = digraph.count_nodes("/")
                num_ref = digraph.count_nodes("array_ref")
                print "Stats for subroutine {0}:".format(sub_name)
                print "Graph has {0} addition operators in it.".\
                    format(num_plus)
                print "Graph has {0} subtraction operators in it.".\
                    format(num_minus)
                print "Graph has {0} multiplication operators in it.".\
                    format(num_mult)
                print "Graph has {0} division operators in it.".\
                    format(num_div)
                print "Graph has {0} array references in it.".\
                    format(num_ref)
                flop_per_byte = (num_plus + num_minus + num_mult + num_div) / \
                                (num_ref*8.0)
                # This is naive for (at least) two reasons: 
                #   1) not all array refs will result in memory traffic
                #      because adjacent elements will almost always be in
                #      the same cache line;
                #   2) all FLOPs are not equal - a division costs ~40x as
                #      much as an addition.
                print "Naive FLOPs/byte = {0}".format(flop_per_byte)

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
