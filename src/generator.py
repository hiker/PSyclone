#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2014.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

import argparse
import sys
import os
import traceback
from parse import parse,ParseError
from psyGen import PSyFactory,GenerationError
from algGen import AlgorithmError

def generate(filename, api="", kernel_path="", script_name=None):
    '''
    Takes a GungHo algorithm specification as input and outputs the associated generated algorithm and psy codes suitable for compiling with the specified kernel(s) and GungHo infrastructure. Uses the :func:`parse.parse` function to parse the algorithm specification, the :class:`psyGen.PSy` class to generate the PSy code and the :class:`algGen.Alg` class to generate the modified algorithm code.

    :param str filename: The file containing the algorithm specification.
    :param str kernel_path: The directory from which to recursively search for the files containing the kernel source (if different from the location of the algorithm specification)
    :param str script_name: A script file that can apply optimisations to the PSy layer (can be a path to a file or a filename that relies on the PYTHONPATH to find the module).
    :return: The algorithm code and the psy code.
    :rtype: ast
    :raises IOError: if the filename or search path do not exist

    For example:

    >>> from generator import generate
    >>> psy, alg = generate("algspec.f90")
    >>> psy, alg = generate("algspec.f90", kernel_path="src/kernels")
    >>> psy, alg = generate("algspec.f90", script_name="optimise.py")

    '''

    if api=="":
        from config import DEFAULTAPI
        api=DEFAULTAPI
    else:
        from config import SUPPORTEDAPIS
        if api not in SUPPORTEDAPIS:
            raise GenerationError("generate: Unsupported API '{0}' specified. Supported types are {1}.".format(api, SUPPORTEDAPIS))

    if not os.path.isfile(filename):
        raise IOError, "file '%s' not found" % (filename)
    if (len(kernel_path) > 0) and (not os.access(kernel_path, os.R_OK)):
        raise IOError, "kernel search path '%s' not found" % (kernel_path)
    try:
        from algGen import Alg
        ast,invokeInfo=parse(filename,api=api,invoke_name="invoke",
                             kernel_path=kernel_path)
        psy=PSyFactory(api).create(invokeInfo)
        if script_name is not None:
            # a script has been provided
            sys_path_appended = False
            filepath, filename = os.path.split(script_name)
            if filepath != '':
                # a path to a file has been provided
                # we need to check the file exists
                if not os.path.isfile(script_name):
                    raise IOError, "script file '{0}' not found in path '{1}'".\
                        format(filename, filepath)
                # it exists so we need to add the path to the python
                # search path
                sys_path_appended = True
                sys.path.append(filepath)
            filename, fileext = os.path.splitext(filename)
            if fileext != '.py':
                if sys_path_appended:
                    os.sys.path.pop()
                raise GenerationError("generator: expected the script file '{0}'to have the '.py' extension".format(fileext))
            try:
                transmod = __import__(filename)
            except ImportError:
                if sys_path_appended:
                    os.sys.path.pop()
                raise GenerationError("generator: attempted to import '{0}' but script file '{1}' has not been found".format(filename, script_name))
            except SyntaxError:
                if sys_path_appended:
                    os.sys.path.pop()
                raise GenerationError("generator: attempted to import '{0}' but script file '{1}' is not valid python".format(filename, script_name))
            try:
                psy = transmod.trans(psy)
            except AttributeError:
                if sys_path_appended:
                    os.sys.path.pop()
                raise GenerationError("generator: attempted to import '{0}' but script file '{1}' does not contain a 'trans()' function".format(filename, script_name))
            if sys_path_appended:
                os.sys.path.pop()
        alg=Alg(ast,psy)
    except Exception as msg:
        raise
    return alg.gen,psy.gen

if __name__=="__main__":

    from config import SUPPORTEDAPIS,DEFAULTAPI
    parser = argparse.ArgumentParser(description='Run the PSyclone code generator on a particular file')
    parser.add_argument('-oalg', help='filename of transformed algorithm code')
    parser.add_argument('-opsy', help='filename of generated PSy code')
    parser.add_argument('-api', default=DEFAULTAPI,help='choose a particular api from {0}, default {1}'.format(str(SUPPORTEDAPIS),DEFAULTAPI))
    parser.add_argument('filename', help='algorithm-layer source code')
    parser.add_argument('-s', '--script', help='filename of a PSyclone optimisation script')
    parser.add_argument('-d','--directory', default="", help='path to root of directory structure containing kernel source code')
    args = parser.parse_args()
    if args.api not in SUPPORTEDAPIS:
        print "Unsupported API '{0}' specified. Supported API's are {1}.".format(args.api,SUPPORTEDAPIS)
        exit(1)
    try:
        alg,psy=generate(args.filename, api=args.api,
                         kernel_path=args.directory,
                         script_name=args.script)
    except AlgorithmError as e:
        print "Warning:",e
        exit(0)
    except (OSError, IOError, ParseError,GenerationError,RuntimeError) as e:
        print "Error:",e
        exit(1)
    except Exception as e:
        print "Error, unexpected exception:\n"
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print exc_type
        print exc_value
        traceback.print_tb(exc_traceback)
        exit(1)
    if args.oalg is not None:
        file = open(args.oalg, "w")
        file.write(str(alg))
        file.close()
    else:
        print "Transformed algorithm code:\n",alg
    if args.opsy is not None:
        file = open(args.opsy, "w")
        file.write(str(psy))
        file.close()
    else:
        print "Generated psy layer code:\n",psy

