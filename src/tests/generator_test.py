# -----------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2014.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -----------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

'''
    A module to perform pytest unit and functional tests on the generator
    function.
'''

from generator import generate, GenerationError
from parse import ParseError
import pytest
import os


def delete_module(modname):
    '''a function to remove a module from Python's internal modules
       list. This is useful as some tests affect others by importing
       modules.'''
    from sys import modules
    del modules[modname]
    for mod in modules.values():
        try:
            delattr(mod, modname)
        except AttributeError:
            pass

# a set of unit tests for the generate function


def test_non_existant_filename():
    ''' checks that algGen raises appropriate error when a
    non-existant filename is supplied '''
    with pytest.raises(IOError):
        generate("non_existant_file.f90")


def test_invalid_api():
    ''' checks that algGen raises appropriate error when an invalid
        api is supplied '''
    with pytest.raises(GenerationError):
        generate(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "test_files", "dynamo0p1", "algorithm",
                              "1_single_function.f90"), api="invalid")


def test_invalid_kernel_path():
    ''' checks that algGen raises appropriate error when an invalid
        search path for kernel source files is supplied '''
    with pytest.raises(IOError):
        generate(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "test_files", "dynamo0p1", "algorithm",
                              "1_single_function.f90"),
                 api="dynamo0.1",
                 kernel_path="does_not_exist")


def test_wrong_kernel_path():
    ''' checks that algGen raises appropriate error when the kernel
        code cannot be found in the specified search path '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(IOError):
        generate(os.path.join(root_path,
                              "test_files", "dynamo0p3",
                              "1.1_single_invoke_qr.f90"),
                 api="dynamo0.3",
                 kernel_path=os.path.join(root_path,
                                          "test_files", "gocean0p1"))


def test_correct_kernel_path():
    ''' checks that algGen succeeds when the location of the kernel
        source code is *not* the same as that of the algorithm code '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    _, _ = generate(os.path.join(root_path,
                                 "test_files", "dynamo0p1", "algorithm",
                                 "1_single_function.f90"),
                    api="dynamo0.1",
                    kernel_path=os.path.join(root_path, "test_files",
                                             "dynamo0p1", "kernels"))


def test_same_kernel_path():
    ''' checks that the generator succeeds when the search directory
        is the same as the algorithm code directory and a path is
        specified '''
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "test_files", "dynamo0p1", "algorithm")
    _, _ = generate(os.path.join(path, "1_single_function.f90"),
                    api="dynamo0.1", kernel_path=path)


def test_similar_kernel_name():
    ''' checks that the generator does not match incorrect files '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p1",
                                 "algorithm", "1_single_function.f90"),
                    api="dynamo0.1",
                    kernel_path=os.path.join(root_path, "test_files",
                                             "dynamo0p1", "kernels2"))


def test_recurse_correct_kernel_path():
    '''checks that the generator succeeds when the location of the kernel
       source code is *not* the same as that of the algorithm code and
       recursion through subdirectories is required'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p1",
                                 "algorithm", "1_single_function.f90"),
                    api="dynamo0.1",
                    kernel_path=os.path.join(root_path, "test_files",
                                             "dynamo0p1", "kernels3"))


def test_script_file_not_found():
    ''' checks that generator.py raises an appropriate error when a
        script file is supplied that can't be found in the Python path.
        In this case the script path is supplied'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(IOError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3", script_name="./non_existant.py")


def test_script_file_not_found_relative():
    ''' checks that generator.py raises an appropriate error when a script
        file is supplied that can't be found in the Python path. In
        this case the script path is not supplied so must be found via the
        PYTHONPATH variable'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3", script_name="non_existant.py")


def test_script_file_too_short():
    ''' checks that generator.py raises an appropriate error when a
        script file name is too short to contain the '.py' extension'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join(root_path, "test_files",
                                                 "dynamo0p3", "xyz"))


def test_script_file_no_extension():
    ''' checks that generator.py raises an appropriate error when a
        script file does not have an extension'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join(root_path, "test_files",
                                                 "dynamo0p3",
                                                 "invalid_script_name"))


def test_script_file_wrong_extension():
    ''' checks that generator.py raises an appropriate error when a
        script file does not have the '.py' extension'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join(root_path, "test_files",
                                                 "dynamo0p3",
                                                 "1_single_invoke.f90"))


def test_script_invalid_content():
    ''' checks that generator.py raises an appropriate error when a
        script file does not contain valid python '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join(
                            "test_files", "dynamo0p3", "error.py"))


def test_script_invalid_content_runtime():
    ''' checks that generator.py raises an appropriate error when a
        script file contains valid python syntactically but produces a
        runtime exception. '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError):
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join(
                            "test_files", "dynamo0p3", "runtime_error.py"))


def test_script_no_trans():
    ''' checks that generator.py raises an appropriate error when a
        script file does not contain a trans() function '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError) as excinfo:
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join("test_files", "dynamo0p3",
                                                 "no_trans.py"))
    assert 'attempted to import' in str(excinfo.value)


def test_script_attr_error():
    ''' checks that generator.py raises an appropriate error when a
        script file contains a trans() function which raises an
        attribute error. This is what we previously used to check for
        a script file not containing a trans() function.'''
    root_path = os.path.dirname(os.path.abspath(__file__))
    with pytest.raises(GenerationError) as excinfo:
        _, _ = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                     "1_single_invoke.f90"),
                        api="dynamo0.3",
                        script_name=os.path.join(root_path, "test_files",
                                                 "dynamo0p3",
                                                 "error_trans.py"))
    assert 'object has no attribute' in str(excinfo.value)


def test_script_null_trans():
    ''' checks that generator.py works correctly when the trans()
        function in a valid script file does no transformations (it
        simply passes input to output). In this case the valid
        script file has an explicit path and must therefore exist at
        this location. '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    alg1, psy1 = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                       "1_single_invoke.f90"),
                          api="dynamo0.3")
    alg2, psy2 = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                       "1_single_invoke.f90"),
                          api="dynamo0.3",
                          script_name=os.path.join(root_path, "test_files",
                                                   "dynamo0p3",
                                                   "null_trans.py"))
    # remove module so we do not affect any following tests
    delete_module("null_trans")
    # we need to remove the first line before comparing output as
    # this line is an instance specific header
    assert '\n'.join(str(alg1).split('\n')[1:]) == \
        '\n'.join(str(alg2).split('\n')[1:])
    assert '\n'.join(str(psy1).split('\n')[1:]) == \
        '\n'.join(str(psy2).split('\n')[1:])


def test_script_null_trans_relative():
    ''' checks that generator.py works correctly when the trans()
        function in a valid script file does no transformations (it
        simply passes input to output). In this case the valid
        script file contains no path and must therefore be found via
        the PYTHOPATH path list. '''
    root_path = os.path.dirname(os.path.abspath(__file__))
    alg1, psy1 = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                       "1_single_invoke.f90"),
                          api="dynamo0.3")
    # set up the python path so that null_trans.py can be found
    os.sys.path.append(os.path.join(root_path, "test_files", "dynamo0p3"))
    alg2, psy2 = generate(os.path.join(root_path, "test_files", "dynamo0p3",
                                       "1_single_invoke.f90"),
                          api="dynamo0.3", script_name="null_trans.py")
    # remove imported module so we do not affect any following tests
    delete_module("null_trans")
    os.sys.path.pop()
    # we need to remove the first line before comparing output as
    # this line is an instance specific header
    assert '\n'.join(str(alg1).split('\n')[1:]) == \
        '\n'.join(str(alg2).split('\n')[1:])
    assert str(psy1) == str(psy2)


def test_script_trans():
    ''' checks that generator.py works correctly when a
        transformation is provided as a script, i.e. it applies the
        transformations correctly. We use loop fusion as an
        example.'''
    from parse import parse
    from psyGen import PSyFactory
    from transformations import LoopFuseTrans
    root_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.join(root_path, "test_files", "dynamo0p3")
    # first loop fuse explicitly (without using generator.py)
    parse_file = os.path.join(base_path, "4_multikernel_invokes.f90")
    _, invoke_info = parse(parse_file, api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    invoke = psy.invokes.get("invoke_0")
    schedule = invoke.schedule
    loop1 = schedule.children[0]
    loop2 = schedule.children[1]
    trans = LoopFuseTrans()
    schedule, _ = trans.apply(loop1, loop2)
    invoke.schedule = schedule
    generated_code_1 = psy.gen
    # second loop fuse using generator.py and a script
    _, generated_code_2 = generate(parse_file, api="dynamo0.3",
                                   script_name=os.path.join(
                                       base_path, "loop_fuse_trans.py"))
    # remove module so we do not affect any following tests
    delete_module("loop_fuse_trans")
    # third - check that the results are the same ...
    assert str(generated_code_1) == str(generated_code_2)

DYN03_BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "test_files", "dynamo0p3")


def test_alg_lines_too_long_tested():
    ''' Test that the generate function causes an exception if the
    line_length argument is set to True and the algorithm file has
    lines longer than 132 characters. We use the dynamo0.3 API in this
    case but could have chosen any. '''
    alg_filename = os.path.join(DYN03_BASE_PATH, "13_alg_long_line.f90")
    with pytest.raises(ParseError) as excinfo:
        _,  _ = generate(alg_filename, api="dynamo0.3", line_length=True)
    assert 'algorithm file does not conform' in str(excinfo.value)


def test_alg_lines_too_long_not_tested():
    ''' Test that the generate function returns successfully if the
    line_length argument is not set (as it should default to False)
    when the algorithm file has lines longer than 132 characters. We
    use the dynamo0.3 API in this case but could have chosen any.'''
    alg_filename = os.path.join(DYN03_BASE_PATH, "13_alg_long_line.f90")
    _, _ = generate(alg_filename, api="dynamo0.3")


def test_kern_lines_too_long_tested():
    ''' Test that the generate function raises an exception if the
    line_length argument is set to True and a Kernel file has
    lines longer than 132 characters. We use the dynamo0.3 API in this
    case but could have chosen any. '''
    alg_filename = os.path.join(DYN03_BASE_PATH, "13.1_kern_long_line.f90")
    with pytest.raises(ParseError) as excinfo:
        _, _ = generate(alg_filename, api="dynamo0.3", line_length=True)
    assert 'kernel file' in str(excinfo.value)
    assert 'does not conform' in str(excinfo.value)


def test_kern_lines_too_long_not_tested():
    ''' Test that the generate function returns successfully if the
    line_length argument is not set (as it should default to False)
    when a kernel file has lines longer than 132 characters. We
    use the dynamo0.3 API in this case but could have chosen any.'''
    alg_filename = os.path.join(DYN03_BASE_PATH, "13.1_kern_long_line.f90")
    _, _ = generate(alg_filename, api="dynamo0.3")


def test_continuators():
    '''Tests that input files with long lines that already have
       continuators to make the code conform to the line length limit
       do not cause an error '''
    _, _ = generate(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 "test_files", "dynamo0p3",
                                 "1.1_single_invoke_qr.f90"),
                    api="dynamo0.3", line_length=True)
