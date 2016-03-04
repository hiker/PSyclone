# Author A. R. Porter, STFC Daresbury Lab

''' This module tests the support for infrastructure/pointwise kernels
in the Dynamo 0.3 API using pytest. '''

# imports
import os
import pytest
from parse import parse, ParseError
from psyGen import PSyFactory, GenerationError


# constants
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_files", "dynamo0p3")

# functions


def test_dyninf_str():
    ''' Check that the str method of DynInfCallFactory works as expected '''
    from dynamo0p3 import DynInfCallFactory
    dyninf = DynInfCallFactory()
    assert str(dyninf) == "Factory for a Dynamo infrastructure call"


def test_dyninf_wrong_name():
    ''' Check that DynInfCallFactory.create() raises an error if it
    doesn't recognise the name of the kernel it is passed '''
    from dynamo0p3 import DynInfCallFactory
    dyninf = DynInfCallFactory()
    fake_kern = ParseError("blah")
    fake_kern.func_name = "pw_blah"
    with pytest.raises(ParseError) as excinfo:
        _ = dyninf.create(fake_kern)
    assert ("Unrecognised infrastructure call. Found 'pw_blah' but "
            "expected one of '[" in str(excinfo.value))


def test_invalid_pointwise_kernel():
    ''' Check that we raise an appropriate error if an unrecognised
    pointwise kernel is specified in the algorithm layer '''
    with pytest.raises(ParseError) as excinfo:
        _, _ = parse(os.path.join(BASE_PATH,
                                  "15.0.0_invalid_pw_kernel.f90"),
                     api="dynamo0.3")
    assert ("kernel call 'set_field_scala' must either be named in a "
            "use statement or be a recognised pointwise kernel" in
            str(excinfo.value))


def test_pointwise_set_str():
    ''' Check that the str method of DynCopyFieldKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15_single_pointwise_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Set infrastructure call"


def test_pointwise_set():
    ''' Tests that we generate correct code for a pointwise
    set operation with a scalar passed by value'''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15_single_pointwise_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
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


def test_pointwise_set_by_ref():
    ''' Tests that we generate correct code for a pointwise
    set operation with a scalar passed by reference '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.0.1_single_pw_set_by_ref.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "    SUBROUTINE invoke_0(fred, f1)\n"
        "      USE mesh_mod, ONLY: mesh_type\n"
        "      REAL(KIND=r_def), intent(inout) :: fred\n"
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
        "        f1_proxy%data(df) = fred\n"
        "      END DO \n")
    assert output in code


@pytest.mark.xfail(reason="Invokes containing multiple kernels with "
                   "any-space arguments are not yet supported")
def test_multiple_pointwise_set():
    ''' Tests that we generate correct code when we have an invoke
    containing multiple set operations '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.0.2_multiple_set_kernels.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "    SUBROUTINE invoke_0(f1, fred, f2, f3, ginger)\n"
        "      USE mesh_mod, ONLY: mesh_type\n"
        "      REAL(KIND=r_def), intent(inout) :: fred, ginger\n"
        "      TYPE(field_type), intent(inout) :: f1, f2, f3\n"
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
        "        f1_proxy%data(df) = fred\n"
        "      END DO \n"
        "      DO df=1,undf_any_space_1\n"
        "        f2_proxy%data(df) = 3.0\n"
        "      END DO \n"
        "      DO df=1,undf_any_space_1\n"
        "        f3_proxy%data(df) = ginger\n"
        "      END DO \n")
    assert output in code


def test_pointwise_set_plus_normal():
    ''' Tests that we generate correct code for a pointwise
    set operation when the invoke also contains a normal kernel '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.1_pw_and_normal_kernel_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "      ! Initialise sizes and allocate any basis arrays for w3\n"
        "      !\n"
        "      ndf_w3 = m2_proxy%vspace%get_ndf()\n"
        "      undf_w3 = m2_proxy%vspace%get_undf()\n"
        "      !\n"
        "      ! Initialise sizes and allocate any basis arrays for "
        "any_space_1\n"
        "      !\n"
        "      ndf_any_space_1 = f1_proxy%vspace%get_ndf()\n"
        "      undf_any_space_1 = f1_proxy%vspace%get_undf()\n"
        "      !\n"
        "      ! Call our kernels\n"
        "      !\n"
        "      DO cell=1,mesh%get_last_halo_cell(1)\n"
        "        !\n"
        "        map_w1 => f1_proxy%vspace%get_cell_dofmap(cell)\n"
        "        map_w2 => f2_proxy%vspace%get_cell_dofmap(cell)\n"
        "        map_w3 => m2_proxy%vspace%get_cell_dofmap(cell)\n"
        "        !\n"
        "        CALL testkern_code(nlayers, ginger, f1_proxy%data, "
        "f2_proxy%data, "
        "m1_proxy%data, m2_proxy%data, ndf_w1, undf_w1, map_w1, ndf_w2, "
        "undf_w2, map_w2, ndf_w3, undf_w3, map_w3)\n"
        "      END DO \n"
        "      !\n"
        "      ! Set halos dirty for fields modified in the above loop\n"
        "      !\n"
        "      CALL f1_proxy%set_dirty()\n"
        "      !\n"
        "      DO df=1,undf_any_space_1\n"
        "        f1_proxy%data(df) = 0.0\n"
        "      END DO ")
    assert output in code


def test_pointwise_copy_str():
    ''' Check that the str method of DynCopyFieldKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.2_single_pw_fld_copy_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Field copy infrastructure call"


def test_pointwise_copy():
    ''' Tests that we generate correct code for a pointwise
    copy field operation '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.2_single_pw_fld_copy_invoke.f90"),
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


def test_pw_subtract_fields_str():
    ''' Test that the str method of DynSubtractFieldsKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.4.0_subtract_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Subtract fields infrastructure call"


def test_pw_subtract_fields():
    ''' Test that the str method of DynSubtractFieldsKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.4.0_subtract_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "      f1_proxy = f1%get_proxy()\n"
        "      f2_proxy = f2%get_proxy()\n"
        "      f3_proxy = f3%get_proxy()\n"
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
        "        f3_proxy%data(df) = f1_proxy%data(df) - f2_proxy%data(df)\n"
        "      END DO")
    assert output in code


def test_pw_add_fields_str():
    ''' Test that the str method of DynSubtractFieldsKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.5.0_add_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Add fields infrastructure call"


def test_pw_add_fields():
    ''' Test that the str method of DynAddFieldsKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.5.0_add_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "      f1_proxy = f1%get_proxy()\n"
        "      f2_proxy = f2%get_proxy()\n"
        "      f3_proxy = f3%get_proxy()\n"
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
        "        f3_proxy%data(df) = f1_proxy%data(df) + f2_proxy%data(df)\n"
        "      END DO")
    assert output in code


def test_pw_divide_fields_str():
    ''' Test that the str method of DynDivideFieldsKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.6.0_divide_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Divide fields infrastructure call"


def test_pw_divide_fields():
    ''' Test that we generate correct code for the divide fields
    infrastructure kernel '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.6.0_divide_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "      f1_proxy = f1%get_proxy()\n"
        "      f2_proxy = f2%get_proxy()\n"
        "      f3_proxy = f3%get_proxy()\n"
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
        "        f3_proxy%data(df) = f1_proxy%data(df) / f2_proxy%data(df)\n"
        "      END DO")
    assert output in code


def test_pw_multiply_field_str():
    ''' Test that the str method of DynMultiplyFieldKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.7.0_multiply_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "Multiply field (by a scalar) infrastructure call"


def test_pw_multiply_field():
    ''' Test that we generate correct code for the multiply field
    (y = a*x) infrastructure kernel '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.7.0_multiply_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
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
        "        f2_proxy%data(df) = a * f1_proxy%data(df)\n"
        "      END DO")
    assert output in code


def test_pw_axpy_field_str():
    ''' Test that the str method of DynAXPYKern returns the
    expected string '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.3_axpy_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    first_invoke = psy.invokes.invoke_list[0]
    kern = first_invoke.schedule.children[0].children[0]
    assert str(kern) == "AXPY infrastructure call"
 

def test_pw_axpy():
    ''' Test that we generate correct code for the pointwise
    operation f = a*x + y where 'a' is a scalar '''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.3_axpy_invoke.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "      f1_proxy = f1%get_proxy()\n"
        "      f2_proxy = f2%get_proxy()\n"
        "      f3_proxy = f3%get_proxy()\n"
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
        "        f3_proxy%data(df) = a*f1_proxy%data(df) + f2_proxy%data(df)\n"
        "      END DO \n"
        )
    assert output in code
 

def test_pw_axpy_by_value():
    ''' Test that we generate correct code for the pointwise
    operation y = a*x when a is passed by value'''
    _, invoke_info = parse(os.path.join(BASE_PATH,
                                        "15.3.2_axpy_invoke_by_value.f90"),
                           api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "      f1_proxy = f1%get_proxy()\n"
        "      f2_proxy = f2%get_proxy()\n"
        "      f3_proxy = f3%get_proxy()\n"
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
        "        f3_proxy%data(df) = 0.5*f1_proxy%data(df) + "
        "f2_proxy%data(df)\n"
        "      END DO \n"
        )
    assert output in code


@pytest.mark.xfail(
    reason="Requires kernel-argument dependency analysis to deduce the "
    "spaces of the fields passed to the pointwise kernel")
def test_pw_multiply_fields_on_different_spaces():
    ''' Test that we raise an error if multiply_fields() is called for
    two fields that are on different spaces '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH,
                     "15.3.0_multiply_fields_different_spaces.f90"),
        api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    with pytest.raises(GenerationError) as excinfo:
        _ = str(psy.gen)
    assert "some string" in str(excinfo.value)


@pytest.mark.xfail(
    reason="Dependency analysis of kernel arguments within an invoke is "
    "not yet implemented")
def test_pw_multiply_fields_deduce_space():
    ''' Test that we generate correct code if multiply_fields() is called
    in an invoke containing another kernel that allows the space of the
    fields to be deduced '''
    _, invoke_info = parse(
        os.path.join(BASE_PATH,
                     "15.3.1_multiply_fields_deduce_space.f90"),
        api="dynamo0.3")
    psy = PSyFactory("dynamo0.3").create(invoke_info)
    code = str(psy.gen)
    print code
    output = (
        "some fortran\n"
    )
    assert output in code
