# -----------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -----------------------------------------------------------------------------
# Author R. Ford and A. R. Porter, STFC Daresbury Lab

''' A module to perform pytest unit and functional tests on the parse
function. '''

from parse import parse, ParseError
import os
import pytest

def test_continuators_kernel():
    '''Tests that an input kernel file with long lines that already has
       continuators to make the code conform to the line length limit
       does not cause an error. '''
    _, _ = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "test_files", "dynamo0p3",
                              "1.1_single_invoke_qr.f90"),
                 api="dynamo0.3", line_length=True)


def test_continuators_algorithm():
    '''Tests that an input algorithm file with long lines that already has
       continuators to make the code conform to the line length limit
       does not cause an error. '''
    _, _ = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "test_files", "dynamo0p3",
                              "13.2_alg_long_line_continuator.f90"),
                 api="dynamo0.3", line_length=True)


def test_get_builtin_defs_wrong_api():
    ''' Check that we raise an appropriate error if we call
    get_builtin_defs() with an invalid API '''
    import parse
    with pytest.raises(ParseError) as excinfo:
        _, _ = parse.get_builtin_defs('invalid_api')
    assert ("get_builtin_defs: Unsupported API" in str(excinfo.value))


def test_kerneltypefactory_wrong_api():
    ''' Check that we raise an appropriate error if we try to create
    a KernelTypeFactory with an invalid API '''
    from parse import KernelTypeFactory
    with pytest.raises(ParseError) as excinfo:
        _ = KernelTypeFactory(api="invalid_api")
    assert ("KernelTypeFactory: Unsupported API" in str(excinfo.value))


def test_kerneltypefactory_default_api():
    ''' Check that the KernelTypeFactory correctly defaults to using
    the default API '''
    from parse import KernelTypeFactory
    from config import DEFAULTAPI
    factory = KernelTypeFactory(api="")
    assert factory._type == DEFAULTAPI


def test_kerneltypefactory_create_broken_type():
    ''' Check that we raise an error if the KernelTypeFactory.create()
    method encounters an unrecognised API. '''
    from parse import KernelTypeFactory
    factory = KernelTypeFactory(api="")
    # Deliberately break the 'type' (API) of this factory
    factory._type = "invalid_api"
    with pytest.raises(ParseError) as excinfo:
        _ = factory.create(None, name="axpy")
    assert ("KernelTypeFactory: Internal Error: Unsupported kernel type"
            in str(excinfo.value))


def test_broken_builtin_metadata():
    ''' Check that we raise an appropriate error if there is a problem
    with the meta-data describing the built-ins for a given API '''
    import dynamo0p3_builtins
    # Keep a copy of the original name of the file containing the meta-data
    # for built-ins
    old_name = dynamo0p3_builtins.BUILTIN_DEFINITIONS_FILE[:]
    # Change it to point to our broken example
    dynamo0p3_builtins.BUILTIN_DEFINITIONS_FILE = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_files", "dynamo0p3", "broken_builtins_mod.f90")
    from parse import KernelTypeFactory
    factory = KernelTypeFactory(api="dynamo0.3")
    with pytest.raises(ParseError) as excinfo:
        _ = factory.create(None, name="axpy")
    assert ("Failed to parse the meta-data for PSyclone built-ins in" in
            str(excinfo.value))
    # Put back the original name of the meta-data file
    dynamo0p3_builtins.BUILTIN_DEFINITIONS_FILE = old_name
