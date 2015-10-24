# ------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# ------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

''' This module tests the line_limit module using pytest. '''

# imports
import pytest
from line_length import FortLineLength

# functions

def test_openmp_directive():
    ''' Tests that we raise an error if we find an long line that is
    an openmp directive '''
    input_file = "  !$OMP PARALLEL LOOP\n"
    expected_output = "  !$OMP PARALLEL &\n!$omp&  LOOP\n"
    fll = FortLineLength(line_length=len(input_file)-3)
    output_file = fll.process(input_file)
    assert output_file == expected_output

def test_acc_directive():
    ''' Tests that we deal with an OpenACC directive appropriately
    when its needs to be line wrapped '''
    input_file = "  !$ACC kernels loop gang(32), vector(16)\n"
    expected_output = "  !$ACC kernels loop gang(32), &\n!$acc&  vector(16)\n"
    fll = FortLineLength(line_length=len(input_file)-5)
    output_file = fll.process(input_file)
    assert output_file == expected_output

def test_unknown():
    ''' Tests that we raise an error if we find a long line that we
    can't determine the type of '''
    input_file = "  A = 10 + B + C\n"
    with pytest.raises(Exception):
        fll = FortLineLength(line_length=len(input_file)-5)
        _ = fll.process(input_file)

def test_comment():
    ''' Tests that a long comment line wrapped as expected '''
    input_file = " ! this is a comment"
    expected_output = " ! this is a\n!&  comment"
    fll = FortLineLength(line_length=len(input_file)-5)
    output_file = fll.process(input_file)
    assert output_file == expected_output

def test_unchanged():
    ''' Tests that a file whose lines are shorter than the specified
    line length is unchanged by the FortLineLength class '''
    input_file = (
        "    INTEGER stuff\n"
        "    REAL stuff\n"
        "    TYPE stuff\n"
        "    CALL stuff\n"
        "    SUBROUTINE stuff\n"
        "    USE stuff\n"
        "    !$OMP stuff\n"
        "    !$ACC stuff\n"
        "    ! stuff\n"
        "    stuff\n")
    fll = FortLineLength(line_length=25)
    output_file = fll.process(input_file)
    print "("+input_file+")"
    print "("+output_file+")"
    assert input_file == output_file, "input should remain unchanged"
    
# upper case and lower case use, call, subroutine, integer, real, type

