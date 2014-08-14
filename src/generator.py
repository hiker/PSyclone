# Copyright 2013 STFC, all rights reserved
import argparse
import sys
import os
import traceback
from parse import parse,ParseError
from psyGen import PSyFactory,GenerationError

def generate(filename,api=""):
    '''
    Takes a GungHo algorithm specification as input and outputs the associated generated algorithm and psy codes suitable for compiling with the specified kernel(s) and GungHo infrastructure. Uses the :func:`parse.parse` function to parse the algorithm specification, the :class:`psyGen.PSy` class to generate the PSy code and the :class:`algGen.Alg` class to generate the modified algorithm code.

    :param str filename: The file containing the algorithm specification.
    :return: The algorithm code and the psy code.
    :rtype: ast
    :raises IOError: if the filename does not exist

    For example:

    >>> from generator import generate
    >>> psy,alg=generate("algspec.f90")

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
    try:
        from algGen import Alg
        ast,invokeInfo=parse(filename,api=api,invoke_name="invoke")
        psy=PSyFactory(api).create(invokeInfo)
        alg=Alg(ast,psy)
    except Exception as msg:
        raise
    return alg.gen,psy.gen

class TestGenerate:
   ''' unit tests for the generate function '''

   def test_non_existant_filename(self):
       import pytest
       with pytest.raises(IOError):
           generate("non_existant_file.f90")

   def test_invalid_api(self):
       import os
       import pytest
       with pytest.raises(GenerationError):
           generate("test_files"+os.linesep+"1_single_function.f90", api="invalid")

if __name__=="__main__":

    from config import SUPPORTEDAPIS,DEFAULTAPI
    parser = argparse.ArgumentParser(description='Run the PSyclone code generator on a particular file')
    parser.add_argument('-oalg', help='filename of transformed algorithm code')
    parser.add_argument('-opsy', help='filename of generated PSy code')
    parser.add_argument('-api', default=DEFAULTAPI,help='choose a particular api from {0}, default {1}'.format(str(SUPPORTEDAPIS),DEFAULTAPI))
    parser.add_argument('filename', help='algorithm-layer source code')
    args = parser.parse_args()
    if args.api not in SUPPORTEDAPIS:
        print "Unsupported API '{0}' specified. Supported API's are {1}.".format(args.api,SUPPORTEDAPIS)
        exit(1)
    try:
        alg,psy=generate(args.filename,api=args.api)
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

