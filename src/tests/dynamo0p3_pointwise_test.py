# Author A. R. Porter, STFC Daresbury Lab

''' This module tests the support for infrastructure/pointwise kernels
in the Dynamo 0.3 API using pytest. '''

# imports
import os
import pytest
from parse import parse, ParseError
from psyGen import PSyFactory


# constants
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_files", "dynamo0p3")

# functions


def test_dyninf_str():
    ''' Check that the str method of DynInfCallFactory works as expected '''
    from dynamo0p3 import DynInfCallFactory
    dyninf = DynInfCallFactory()
    assert str(dyninf) == "Factory for a Dynamo infrastructure call"


def test_pointwise_set():
    ''' Tests that we generate correct code for a pointwise
    set operation '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14_single_pointwise_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    code = str(psy.gen)
    print code
    output = (
        "    SUBROUTINE invoke_0(f1)\n"
        "      USE mesh_mod, ONLY: mesh_type\n"
        "      TYPE(field_type), intent(inout) :: f1\n"
        "      INTEGER df\n"
        "      INTEGER ndf_any_space_1, undf_any_space_1\n"
        "      TYPE(mesh_type) mesh\n"
        "      INTEGER nlayers\n"
        "      TYPE(field_proxy_type) f1_proxy\n"
        "      !\n"
        "      ! Initialise field proxies\n"
        "      !\n"
        "      f1_proxy = f1%get_proxy()\n"
        "      !\n"
        "      ! Initialise number of layers\n"
        "      !\n"
        "      nlayers = f1_proxy%vspace%get_nlayers()\n"
        "      !\n"
        "      ! Create a mesh object\n"
        "      !\n"
        "      mesh = f1%get_mesh()\n"
        "      !\n"
        "      ! Initialise sizes and allocate any basis arrays for "
        "any_space_1\n"
        "      !\n"
        "      ndf_any_space_1 = f1_proxy%vspace%get_ndf()\n"
        "      undf_any_space_1 = f1_proxy%vspace%get_undf()\n"
        "      !\n"
        "      ! Call our kernels\n"
        "      !\n"
        "      DO df=1,undf_any_space_1\n"
        "        f1_proxy%data(df) = 0.0\n"
        "      END DO \n")
    assert output in code


@pytest.mark.xfail(
    reason="Requires kernel-argument dependency analysis to deduce the "
    "space of the field passed to the pointwise kernel")
def test_pointwise_set_plus_normal():
    ''' Tests that we generate correct code for a pointwise
    set operation when the invoke also contains a normal kernel '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14.1_pw_and_normal_kernel_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    code = str(psy.gen)
    print code
    output = (
        "      ! Initialise sizes and allocate any basis arrays for w3\n"
        "      !\n"
        "      ndf_w3 = m2_proxy%vspace%get_ndf()\n"
        "      undf_w3 = m2_proxy%vspace%get_undf()\n"
        "      !\n"
        "      ! Call our kernels\n"
        "      !\n"
        "      DO cell=1,f1_proxy%vspace%get_ncell()\n"
        "        !\n"
        "        map_w1 => f1_proxy%vspace%get_cell_dofmap(cell)\n"
        "        map_w2 => f2_proxy%vspace%get_cell_dofmap(cell)\n"
        "        map_w3 => m2_proxy%vspace%get_cell_dofmap(cell)\n"
        "        !\n"
        "        CALL testkern_code(nlayers, f1_proxy%data, f2_proxy%data, "
        "m1_proxy%data, m2_proxy%data, ndf_w1, undf_w1, map_w1, ndf_w2, "
        "undf_w2, map_w2, ndf_w3, undf_w3, map_w3)\n"
        "      END DO \n"
        "      DO df=1,undf_w1\n"
        "        f1_proxy%data(df) = 0.0\n"
        "      END DO ")
    assert output in code


def test_pointwise_copy():
    ''' Tests that we generate correct code for a pointwise
    copy field operation '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14.2_single_pw_fld_copy_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "    SUBROUTINE invoke_0(f1, f2)\n"
        "      USE mesh_mod, ONLY: mesh_type\n"
        "      TYPE(field_type), intent(inout) :: f1, f2\n"
        "      INTEGER df\n"
        "      INTEGER ndf_any_space_1, undf_any_space_1\n"
        "      TYPE(mesh_type) mesh\n"
        "      INTEGER nlayers\n"
        "      TYPE(field_proxy_type) f1_proxy, f2_proxy\n"
        "      !\n"
        "      ! Initialise field proxies\n"
        "      !\n"
        "      f1_proxy = f1%get_proxy()\n"
        "      f2_proxy = f2%get_proxy()\n"
        "      !\n"
        "      ! Initialise number of layers\n"
        "      !\n"
        "      nlayers = f1_proxy%vspace%get_nlayers()\n"
        "      !\n"
        "      ! Create a mesh object\n"
        "      !\n"
        "      mesh = f1%get_mesh()\n"
        "      !\n"
        "      ! Initialise sizes and allocate any basis arrays for "
        "any_space_1\n"
        "      !\n"
        "      ndf_any_space_1 = f1_proxy%vspace%get_ndf()\n"
        "      undf_any_space_1 = f1_proxy%vspace%get_undf()\n"
        "      !\n"
        "      ! Call our kernels\n"
        "      !\n"
        "      DO df=1,undf_any_space_1\n"
        "        f2_proxy%data(df) = f1_proxy%data(df)\n"
        "      END DO")
    assert output in code


def test_pointwise_copy_str():
    ''' Check that the str method of DynCopyFieldKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14.2_single_pw_fld_copy_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Field copy infrastructure call"


def test_pointwise_set_str():
    ''' Check that the str method of DynCopyFieldKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14_single_pointwise_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Set infrastructure call"


def test_pw_multiply_field_str():
    ''' Test that the str method of DynMultiplyFieldKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14.3_multiply_field_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Field multiply infrastructure call"
 

def test_pw_multiply_field():
    ''' Test that we generate correct code for the pointwise
    operation y = a*x '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "14.3_multiply_field_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    output = (
        "    x_proxy = x%get_proxy()\n"
        "    y_proxy = y%get_proxy()\n"
        "\n"
        "    undf = x_proxy%vspace%get_undf()\n"
        "\n"
        "    do i = 1,undf\n"
        "      y_proxy%data(i) = a*x_proxy%data(i)\n"
        "    end do \n"
        )
    assert output in code


def test_pw_multiply_fields_on_different_spaces():
    ''' Test that we raise an error if multiply_fields() is called for
    two fields that are on different spaces '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH,
                     "14.3.0_multiply_fields_different_spaces.f90"),
        api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)


def test_pw_multiply_fields_on_different_spaces():
    ''' Test that we generate correct code if multiply_fields() is called
    in an invoke containing another kernel that allows the space of the
    fields to be deduced '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH,
                     "14.3.1_multiply_fields_deduce_space.f90"),
        api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    output = (
        "some fortran\n"
    )
    assert output in code
