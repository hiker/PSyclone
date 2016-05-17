#!/usr/bin/env python
import os
import sys
from fparser.Fortran2003 import Module, Module_Subprogram_Part, \
    Subroutine_Subprogram, Assignment_Stmt, Add_Operand, \
    Level_2_Expr, Level_2_Unary_Expr, Real_Literal_Constant, \
    Subroutine_Stmt, Name, Section_Subscript_List, Parenthesis, Part_Ref
from dag import DirectedAcyclicGraph, DAGNode

### START UPDATE SYS.PATH ###
### END UPDATE SYS.PATH ###
try:
    from iocbio.optparse_gui import OptionParser
except ImportError:
    from optparse import OptionParser
from fparser.script_options import set_f2003_options

OPERATORS = ["+", "-", "/", "*"]
FORTRAN_INTRINSICS = ["SIGN", "SIN", "COS"]

def str_to_node_name(astring):
    
    new_string = astring.replace(" ","")
    new_string = new_string.replace(",","_")
    new_string = new_string.replace("+","p")
    new_string = new_string.replace("-","m")
    new_string = new_string.replace("(","_")
    new_string = new_string.replace(")","")
    return new_string

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

def walk(children, my_type):
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
    from fparser.Fortran2003 import Name, Section_Subscript_List
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
        except AttributeError as excinfo:
            #print str(excinfo)
            pass
    return local_list

def make_dag(graph, parent, children):
    ''' Makes a DAG from the RHS of an assignment '''

    debug = False

    if debug:
        for child in children:
            if isinstance(child, str):
                print "String: ", child
            elif isinstance(child, Part_Ref):
                print "Part ref", str(child)
            else:
                print type(child)
        print "--------------"

    subex_count = 0
    for child in children:
        if isinstance(child, str):
            if child in OPERATORS:
                # This is the operator which is then the parent
                # of the DAG of this subexpression. All operators
                # are unique nodes in the DAG.
                opnode = graph.get_node(child, parent, unique=True)
                parent.add_child(opnode)
                parent = opnode
        elif is_subexpression(child):
            subex_count += 1

    for idx, child in enumerate(children):
        if isinstance(child, Name):
            suffix = ""
            if idx < len(children)-1 and isinstance(children[idx+1],
                                                    Section_Subscript_List):
                # This is an array reference
                suffix = "_" + str_to_node_name(str(children[idx+1]))
            var_name = str(child) + suffix
            tmpnode = graph.get_node(var_name, parent)
            parent.add_child(tmpnode)
        elif isinstance(child, Real_Literal_Constant):
            # This is a constant
            tmpnode = graph.get_node(str(child), parent, unique=True)
            parent.add_child(tmpnode)
        elif isinstance(child, Part_Ref):
            # This can be either a function call or an array reference
            # TODO sub_class Part_Ref and implement a proper method to
            # generate a string!
            if is_intrinsic_fn(child):
                # Create a node to represent the intrinsic call
                tmpnode = graph.get_node(str(child.items[0]), parent,
                                         unique=True)
                # Add its dependencies
                make_dag(graph, tmpnode, child.items[1:])
            else:
                name = str_to_node_name(str(child))
                tmpnode = graph.get_node(name, parent)
                parent.add_child(tmpnode)
        elif is_subexpression(child):
            if subex_count == 1:
                # There is only 1 subexpression so don't make a node
                # to represent it
                make_dag(graph, parent, child.items)
            else:
                # One or more of the children are themselves sub-expressions
                name = str(type(child))
                tmpnode = graph.get_node(name, parent, unique=True)
                parent.add_child(tmpnode)
                # Make the DAG of this sub-expression
                make_dag(graph, tmpnode, child.items)


def runner (parser, options, args):
    from fparser.api import Fortran2003
    from fparser.readfortran import  FortranFileReader
    for filename in args:
        reader = FortranFileReader(filename)
        if options.mode != 'auto':
            reader.set_mode_from_str(options.mode)
        try:
            program = Fortran2003.Program(reader)
            subroutines = walk(program.content, Subroutine_Subprogram)
            for subroutine in subroutines:
                substmt = walk(subroutine.content, Subroutine_Stmt)
                sub_name = str(substmt[0].get_name())

                # Create a file for the graph of this subroutine
                fo = open(sub_name+".gv", "w")

                digraph = DirectedAcyclicGraph(sub_name)
                fo.write("strict digraph {\n")
                assignments = walk(subroutine.content, Assignment_Stmt)
                for assign in assignments:
                    assigned_to = walk_items([assign.items[0]], Name)
                    var_name = str(assigned_to[0])
                    dag = digraph.get_node(name=var_name, parent=None)
                    # TODO make_dag should be a method of digraph?
                    # First two items of an Assignment_Stmt are the name of
                    # the var being assigned to and '='.
                    make_dag(digraph, dag, assign.items[2:])
                    #dag.display()
                    dag.to_dot(fo)
                fo.write("}\n")
                print "Wrote DAG to {0}".format(fo.name)
                fo.close()

        except Fortran2003.NoMatchError, msg:
            print 'parsing %r failed at %s' % (filename, reader.fifo_item[-1])
            print 'started at %s' % (reader.fifo_item[0])
            print 'Quitting'
            return

def main ():
    parser = OptionParser()
    set_f2003_options(parser)
    if hasattr(parser, 'runner'):
        parser.runner = runner
    options, args = parser.parse_args()
    runner(parser, options, args)
    return

if __name__=="__main__":
    main()
