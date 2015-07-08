#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

import argparse
import fparser
from fparser import api as fpapi
from dynamo0p3 import DynKern, DynKernelType03
from psyGen import GenerationError
from parse import ParseError
from config import SUPPORTEDSTUBAPIS
import os

def generate(filename,api=""):

    if api == "":
        from config import DEFAULTSTUBAPI
        api = DEFAULTSTUBAPI
    if api not in SUPPORTEDSTUBAPIS:
        print "Unsupported API '{0}' specified. Supported API's are {1}.".format(api,SUPPORTEDSTUBAPIS)
        raise GenerationError("generate: Unsupported API '{0}' specified. Supported types are {1}.".format(api, SUPPORTEDSTUBAPIS))

    if not os.path.isfile(filename):
        raise IOError, "file '%s' not found" % (filename)

    # drop cache
    fparser.parsefortran.FortranParser.cache.clear()
    fparser.logging.disable('CRITICAL')
    try:
        ast = fpapi.parse(filename, ignore_comments=False)
    except AttributeError:
        raise ParseError("Code appears to be invalid Fortran")

    metadata = DynKernelType03(ast)
    kernel = DynKern()
    kernel.load_meta(metadata)
    return kernel.genstub

if __name__=="__main__":

    from config import SUPPORTEDSTUBAPIS,DEFAULTSTUBAPI
    parser = argparse.ArgumentParser(description='Create Kernel stub code from Kernel metadata')
    parser.add_argument('-o', help='filename of output')
    parser.add_argument('-api', default=DEFAULTSTUBAPI,help='choose a particular api from {0}, default {1}'.format(str(SUPPORTEDSTUBAPIS),DEFAULTSTUBAPI))
    parser.add_argument('filename', help='Kernel metadata')
    args = parser.parse_args()

    stub = gen_kernel_stub(args.filename, api=args.api)

    if args.o is not None:
        file = open(args.o, "w")
        file.write(str(stub))
        file.close()
    else:
        print "Kernel stub code:\n",stub

