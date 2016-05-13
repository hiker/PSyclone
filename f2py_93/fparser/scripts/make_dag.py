#!/usr/bin/env python
import os
import sys
### START UPDATE SYS.PATH ###
### END UPDATE SYS.PATH ###
try:
    from iocbio.optparse_gui import OptionParser
except ImportError:
    from optparse import OptionParser
from fparser.script_options import set_f2003_options

def str_to_node_name(astring):
    
    new_string = astring.replace(" ","")
    new_string = new_string.replace(",","_")
    new_string = new_string.replace("+","p")
    new_string = new_string.replace("-","m")
    return new_string

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

def runner (parser, options, args):
    from fparser.api import Fortran2003
    from fparser.readfortran import  FortranFileReader
    for filename in args:
        reader = FortranFileReader(filename)
        if options.mode != 'auto':
            reader.set_mode_from_str(options.mode)
        try:
            program = Fortran2003.Program(reader)
            print program
            print type(program)
            print dir(program.content)
            from fparser.Fortran2003 import Module, Module_Subprogram_Part, \
                Subroutine_Subprogram, Assignment_Stmt, Add_Operand, \
                Level_2_Expr, Level_2_Unary_Expr, Real_Literal_Constant, \
                Specification_Part, Name
            subroutines = walk(program.content, Subroutine_Subprogram)
            for subroutine in subroutines:
                print type(subroutine)
                print dir(subroutine)
                #for item in subroutine.content:
                #    print type(item)
                #    if isinstance(item, Specification_Part):
                #        print dir(item)
                pluscount = 0
                assignments = walk(subroutine.content, Assignment_Stmt)
                for assign in assignments:
                    #print "--------------------------"
                    #print assign.item

                    var_list = walk_items(assign.items[1:], Name)

                    assigned_to = walk_items([assign.items[0]], Name)
                    subgraphstr = str(assigned_to[0]) + " -> {"
                    for var in var_list:
                        subgraphstr += " " + var
                    subgraphstr += "}"
                    print subgraphstr

        except Fortran2003.NoMatchError, msg:
            print 'parsing %r failed at %s' % (filename, reader.fifo_item[-1])
            print 'started at %s' % (reader.fifo_item[0])
            print 'quiting'
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
