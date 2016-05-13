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
                Specification_Part
            subroutines = walk(program.content, Subroutine_Subprogram)
            for subroutine in subroutines:
                print type(subroutine)
                print dir(subroutine)
                for item in subroutine.content:
                    print type(item)
                    if isinstance(item, Specification_Part):
                        print dir(item)
                pluscount = 0
                assignments = walk(subroutine.content, Assignment_Stmt)
                for assign in assignments:
                    print "--------------------------"
                    print assign.item
                    print assign.items[0], "<- {"  
                    if isinstance(assign.items[2], Add_Operand):
                        print dir(assign.items[2])
                        print assign.items[2].use_names
                        pluscount += 1
                        print "plus{0}".format(pluscount)
                        pass
                    elif isinstance(assign.items[2], Level_2_Expr):
                        print dir(assign.items[2])
                        print assign.items[2]
                        pass
                    elif isinstance(assign.items[2], Level_2_Unary_Expr):
                        pass
                    elif isinstance(assign.items[2], Real_Literal_Constant):
                        print assign.items[2]
                        pass
                    else:
                        print "Unrecognised expression type: ", assign.item
                        print "Type is ", type(assign.item)

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
