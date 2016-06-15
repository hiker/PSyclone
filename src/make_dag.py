#!/usr/bin/env python

''' A python script to parse a Fortran source file and produce a DAG
    for each subroutine it contains. '''

from dag import DirectedAcyclicGraph, str_to_node_name

try:
    from iocbio.optparse_gui import OptionParser
except ImportError:
    from optparse import OptionParser
from fparser.script_options import set_f2003_options


def walk(children, my_type, indent=0, debug=False):
    '''' Walk down the tree produced by the f2003 parser where children
    are listed under 'content'.  Returns a list of all nodes with the
    specified type. '''
    from fparser.Fortran2003 import Section_Subscript_List, Name
    ignore_types = [Section_Subscript_List]
    local_list = []
    for idx, child in enumerate(children):
        if debug:
            print indent*"  " + "child type = ", type(child)
        if isinstance(child, my_type):
            if isinstance(child, Name):
                suffix = ""
                if idx < len(children)-1 and isinstance(children[idx+1],
                                                        Section_Subscript_List):
                    # This is an array reference
                    suffix = "_" + str_to_node_name(str(children[idx+1]))
                local_list.append(str(child)+suffix)
            else:
                local_list.append(child)
            
        try:
            local_list += walk(child.content, my_type, indent+1, debug)
        except AttributeError:
            pass
        try:
            local_list += walk(child.items, my_type, indent+1, debug)
        except AttributeError:
            pass
    return local_list


def walk_items(children, my_type):
    ''' Walk down tree produced by f2003 parser where child nodes are listed
    under items '''
    from fparser.Fortran2003 import Section_Subscript_List, Name
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


def dag_of_code_block(parent_node, name):
    ''' Creates and returns a DAG for the code that is a child of the
    supplied node '''
    from fparser.Fortran2003 import Assignment_Stmt, Name

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
        print type(parent_node)
        print dir(parent_node)
        assignments = walk(parent_node.items, Assignment_Stmt)
    else:
        assignments = walk(parent_node.content, Assignment_Stmt)

    if not assignments:
        # If this subroutine has no assignment statements
        # then we skip it
        print "Code {0} contains no assignment statements - skipping".format(name)
        return None

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

    apply_fma_transformation = True

    for filename in args:
        reader = FortranFileReader(filename)
        if options.mode != 'auto':
            reader.set_mode_from_str(options.mode)
        try:
            program = Fortran2003.Program(reader)
            # Find all the subroutines contained in the file
            subroutines = walk(program.content, Subroutine_Subprogram, debug=True)
            # Create a DAG for each subroutine
            for subroutine in subroutines:
                substmt = walk(subroutine.content, Subroutine_Stmt)
                sub_name = str(substmt[0].get_name())
                
                loops = walk(subroutine.content, Block_Nonlabel_Do_Construct)
                print "Found {0} loops in subroutine {1}".format(len(loops),
                                                                 sub_name)
                digraphs = []
                
                if not loops:
                    exe_part = walk(subroutine.content, Execution_Part)
                    digraph = dag_of_code_block(exe_part[0], sub_name)
                    if digraph:
                        digraphs.append(digraph)
                else:
                    for idx, loop in enumerate(loops):
                        digraph = dag_of_code_block(loop,
                                                    sub_name+"_loop"+str(idx))
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
