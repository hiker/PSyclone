#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

from parse import parse
from psyGen import PSyFactory
import os

class TestPSyDynamo0p3API:
    ''' Tests for PSy layer code generation that are specific to the dynamo0.3 api. '''

    def test_field(self):
        ''' tests that a call with a set of fields and no basis functions produces correct code '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","1_single_invoke.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        output = """  MODULE psy_single_invoke
    USE constants_mod, ONLY: r_def
    USE quadrature_mod, ONLY: quadrature_type
    USE operator_mod, ONLY: operator_type, operator_proxy_type
    USE field_mod, ONLY: field_type, field_proxy_type
    IMPLICIT NONE
    CONTAINS
    SUBROUTINE invoke_0_testkern_type(f1, f2, m1, m2)
      USE testkern, ONLY: testkern_code
      TYPE(field_type), intent(inout) :: f1, f2, m1, m2
      INTEGER, pointer :: map_w1(:) => null(), map_w2(:) => null(), map_w3(:) => null()
      INTEGER cell
      INTEGER ndf_w1, undf_w1, ndf_w2, undf_w2, ndf_w3, undf_w3
      INTEGER nlayers
      TYPE(field_proxy_type) f1_proxy, f2_proxy, m1_proxy, m2_proxy
      !
      ! Initialise field proxies
      !
      f1_proxy = f1%get_proxy()
      f2_proxy = f2%get_proxy()
      m1_proxy = m1%get_proxy()
      m2_proxy = m2%get_proxy()
      !
      ! Initialise number of layers
      !
      nlayers = f1_proxy%vspace%get_nlayers()
      !
      ! Initialise sizes and allocate any basis arrays for w1
      !
      ndf_w1 = f1_proxy%vspace%get_ndf()
      undf_w1 = f1_proxy%vspace%get_undf()
      !
      ! Initialise sizes and allocate any basis arrays for w2
      !
      ndf_w2 = f2_proxy%vspace%get_ndf()
      undf_w2 = f2_proxy%vspace%get_undf()
      !
      ! Initialise sizes and allocate any basis arrays for w3
      !
      ndf_w3 = m2_proxy%vspace%get_ndf()
      undf_w3 = m2_proxy%vspace%get_undf()
      !
      ! Call our kernels
      !
      DO cell=1,f1_proxy%vspace%get_ncell()
        !
        map_w1 => f1_proxy%vspace%get_cell_dofmap(cell)
        map_w2 => f2_proxy%vspace%get_cell_dofmap(cell)
        map_w3 => m2_proxy%vspace%get_cell_dofmap(cell)
        !
        CALL testkern_code(nlayers, f1_proxy%data, f2_proxy%data, m1_proxy%data, m2_proxy%data, ndf_w1, undf_w1, map_w1, ndf_w2, undf_w2, map_w2, ndf_w3, undf_w3, map_w3)
      END DO 
      !
    END SUBROUTINE invoke_0_testkern_type
  END MODULE psy_single_invoke"""
        assert str(generated_code).find(output)!=-1
    def test_field_qr(self):
        ''' tests that a call, with a set of fields requiring quadrature, produces correct code '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","1.1_single_invoke_qr.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        output = """    SUBROUTINE invoke_0_testkern_qr_type(f1, f2, m1, m2, qr)
      USE testkern_qr, ONLY: testkern_qr_code
      TYPE(field_type), intent(inout) :: f1, f2, m1, m2
      TYPE(quadrature_type), intent(in) :: qr
      INTEGER, pointer :: map_w1(:) => null(), map_w2(:) => null(), map_w3(:) => null()
      INTEGER cell
      REAL(KIND=r_def), allocatable :: basis_w1(:,:,:,:), diff_basis_w2(:,:,:,:), basis_w3(:,:,:,:), diff_basis_w3(:,:,:,:)
      INTEGER dim_w1, diff_dim_w2, dim_w3, diff_dim_w3
      INTEGER ndf_w1, undf_w1, ndf_w2, undf_w2, ndf_w3, undf_w3
      REAL(KIND=r_def), pointer :: zp(:) => null(), wh(:) => null(), wv(:) => null()
      REAL(KIND=r_def), pointer :: xp(:,:) => null()
      INTEGER nqp_h, nqp_v
      INTEGER nlayers
      TYPE(field_proxy_type) f1_proxy, f2_proxy, m1_proxy, m2_proxy
      !
      ! Initialise field proxies
      !
      f1_proxy = f1%get_proxy()
      f2_proxy = f2%get_proxy()
      m1_proxy = m1%get_proxy()
      m2_proxy = m2%get_proxy()
      !
      ! Initialise number of layers
      !
      nlayers = f1_proxy%vspace%get_nlayers()
      !
      ! Initialise qr values
      !
      wv => qr%get_wqp_v()
      xp => qr%get_xqp_h()
      zp => qr%get_xqp_v()
      wh => qr%get_wqp_h()
      nqp_h = qr%get_nqp_h()
      nqp_v = qr%get_nqp_v()
      !
      ! Initialise sizes and allocate any basis arrays for w1
      !
      ndf_w1 = f1_proxy%vspace%get_ndf()
      undf_w1 = f1_proxy%vspace%get_undf()
      dim_w1 = f1_proxy%vspace%get_dim_space()
      ALLOCATE (basis_w1(dim_w1, ndf_w1, nqp_h, nqp_v))
      !
      ! Initialise sizes and allocate any basis arrays for w2
      !
      ndf_w2 = f2_proxy%vspace%get_ndf()
      undf_w2 = f2_proxy%vspace%get_undf()
      diff_dim_w2 = f2_proxy%vspace%get_dim_space_diff()
      ALLOCATE (diff_basis_w2(diff_dim_w2, ndf_w2, nqp_h, nqp_v))
      !
      ! Initialise sizes and allocate any basis arrays for w3
      !
      ndf_w3 = m2_proxy%vspace%get_ndf()
      undf_w3 = m2_proxy%vspace%get_undf()
      dim_w3 = m2_proxy%vspace%get_dim_space()
      ALLOCATE (basis_w3(dim_w3, ndf_w3, nqp_h, nqp_v))
      diff_dim_w3 = m2_proxy%vspace%get_dim_space_diff()
      ALLOCATE (diff_basis_w3(diff_dim_w3, ndf_w3, nqp_h, nqp_v))
      !
      ! Compute basis arrays
      !
      CALL f1_proxy%vspace%compute_basis_function(basis_w1, ndf_w1, nqp_h, nqp_v, xp, zp)
      CALL f2_proxy%vspace%compute_diff_basis_function(diff_basis_w2, ndf_w2, nqp_h, nqp_v, xp, zp)
      CALL m2_proxy%vspace%compute_basis_function(basis_w3, ndf_w3, nqp_h, nqp_v, xp, zp)
      CALL m2_proxy%vspace%compute_diff_basis_function(diff_basis_w3, ndf_w3, nqp_h, nqp_v, xp, zp)
      !
      ! Call our kernels
      !
      DO cell=1,f1_proxy%vspace%get_ncell()
        !
        map_w1 => f1_proxy%vspace%get_cell_dofmap(cell)
        map_w2 => f2_proxy%vspace%get_cell_dofmap(cell)
        map_w3 => m2_proxy%vspace%get_cell_dofmap(cell)
        !
        CALL testkern_qr_code(nlayers, f1_proxy%data, f2_proxy%data, m1_proxy%data, m2_proxy%data, ndf_w1, undf_w1, map_w1, basis_w1, ndf_w2, undf_w2, map_w2, diff_basis_w2, ndf_w3, undf_w3, map_w3, basis_w3, diff_basis_w3, nqp_h, nqp_v, wh, wv)
      END DO 
      !
      ! Deallocate basis arrays
      !
      DEALLOCATE (basis_w1, diff_basis_w2, basis_w3, diff_basis_w3)
      !
    END SUBROUTINE invoke_0_testkern_qr_type"""
        assert str(generated_code).find(output)!=-1
    def test_vector_field(self):
        ''' tests that a vector field is declared correctly in the PSy layer '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","8_vector_field.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        assert(str(generated_code).find("SUBROUTINE invoke_0_testkern_chi_type(f1, chi)")!=-1 and \
                  str(generated_code).find("TYPE(field_type), intent(inout) :: f1, chi(3)")!=-1)

    def test_orientation(self):
	ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","9_orientation.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
	assert str(generated_code).find("INTEGER, pointer :: orientation_w2(:) => null()")!=-1 and \
               str(generated_code).find("orientation_w2 => f2_proxy%vspace%get_cell_orientation(cell)")!=-1

    def test_operator(self):
        ''' tests that an operator is implemented correctly in the PSy layer '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","10_operator.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        assert(str(generated_code).find("SUBROUTINE invoke_0_testkern_operator_type(mm_w0, chi, qr)")!=-1 and \
               str(generated_code).find("TYPE(operator_type), intent(inout) :: mm_w0")!=-1 and \
               str(generated_code).find("TYPE(operator_proxy_type) mm_w0_proxy")!=-1 and \
               str(generated_code).find("mm_w0_proxy = mm_w0%get_proxy()")!=-1 and \
               str(generated_code).find("CALL testkern_operator_code(cell, nlayers, mm_w0_proxy%ncell_3d, mm_w0_proxy%local_stencil, chi_proxy(1)%data, chi_proxy(2)%data, chi_proxy(3)%data, ndf_w0, undf_w0, map_w0, basis_w0, diff_basis_w0, nqp_h, nqp_v, wh, wv)")!=-1)

    def test_operator_nofield(self):
        ''' tests that an operator with no field on the same space is implemented correctly in the PSy layer '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","10.1_operator_nofield.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        gen_code_str = str(psy.gen)
        assert(gen_code_str.find("SUBROUTINE invoke_0_testkern_operator_nofield_type(mm_w2, chi, qr)")!=-1)
        assert(gen_code_str.find("TYPE(operator_type), intent(inout) :: mm_w2")!=-1)
        assert(gen_code_str.find("TYPE(operator_proxy_type) mm_w2_proxy")!=-1)
        assert(gen_code_str.find("mm_w2_proxy = mm_w2%get_proxy()")!=-1)
        assert(gen_code_str.find("undf_w2")==-1)
        assert(gen_code_str.find("map_w2")==-1)
        assert(gen_code_str.find("CALL testkern_operator_code(cell, nlayers, mm_w2_proxy%ncell_3d, mm_w2_proxy%local_stencil, chi_proxy(1)%data, chi_proxy(2)%data, chi_proxy(3)%data, ndf_w2, basis_w2, ndf_w0, undf_w0, map_w0, diff_basis_w0, nqp_h, nqp_v, wh, wv)")!=-1)

    def test_any_space_1(self):
        ''' tests that any_space is implemented correctly in the PSy layer. Includes more than one type of any_space delcaration and func_type basis functions on any_space. '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","11_any_space.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        assert(str(generated_code).find("INTEGER, pointer :: map_any_space_1(:) => null(), map_any_space_2(:) => null()")!=-1)
        assert(str(generated_code).find("REAL(KIND=r_def), allocatable :: basis_any_space_1(:,:,:,:), basis_any_space_2(:,:,:,:)")!=-1)
        assert(str(generated_code).find("ALLOCATE (basis_any_space_1(dim_any_space_1, ndf_any_space_1, nqp_h, nqp_v))")!=-1)
        assert(str(generated_code).find("ALLOCATE (basis_any_space_2(dim_any_space_2, ndf_any_space_2, nqp_h, nqp_v))")!=-1)
        assert(str(generated_code).find("map_any_space_1 => a_proxy%vspace%get_cell_dofmap(cell)")!=-1)
        assert(str(generated_code).find("map_any_space_2 => b_proxy%vspace%get_cell_dofmap(cell)")!=-1)
        assert(str(generated_code).find("CALL testkern_any_space_1_code(nlayers, a_proxy%data, b_proxy%data, c_proxy(1)%data, c_proxy(2)%data, c_proxy(3)%data, ndf_any_space_1, undf_any_space_1, map_any_space_1, basis_any_space_1, ndf_any_space_2, undf_any_space_2, map_any_space_2, basis_any_space_2, ndf_w0, undf_w0, map_w0, diff_basis_w0, nqp_h, nqp_v, wh, wv)")!=-1)
        assert(str(generated_code).find("DEALLOCATE (basis_any_space_1, basis_any_space_2, diff_basis_w0)")!=-1)

    def test_any_space_2(self):
        ''' tests that any_space is implemented correctly in the PSy layer. Includes multiple declarations of the same space, no func_type declarations and any_space used with an operator. '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","11.1_any_space.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        assert(str(generated_code).find("INTEGER, pointer :: map_any_space_1(:) => null()")!=-1)
        assert(str(generated_code).find("INTEGER ndf_any_space_1, undf_any_space_1")!=-1)
        assert(str(generated_code).find("ndf_any_space_1 = a_proxy%vspace%get_ndf()")!=-1)
        assert(str(generated_code).find("undf_any_space_1 = a_proxy%vspace%get_undf()")!=-1)
        assert(str(generated_code).find("map_any_space_1 => a_proxy%vspace%get_cell_dofmap(cell)")!=-1)
        assert(str(generated_code).find("CALL testkern_any_space_2_code(cell, nlayers, a_proxy%data, b_proxy%data, c_proxy%ncell_3d, c_proxy%local_stencil, ndf_any_space_1, undf_any_space_1, map_any_space_1)")!=-1)

    def test_kernel_specific1(self):
        '''tests that kernel-specific code is added to the
           matrix_vector_kernel_mm kernel. This code is required as
           the dynamo0.3 api does not know about boundary conditions
           but this kernel requires them. This "hack" is only
           supported to get PSyclone to generate correct code for the
           current implementation of dynamo. Future API's will not
           support any hacks.
        '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","12_kernel_specific.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        output1='''    fs = x%which_function_space()  
    if(fs .eq. W2) then 
       boundary_dofs => x_p%vspace%get_boundary_dofs()
    end if'''
        assert(str(generated_code).find(output1)!=-1)
        output2='''       if(fs.eq.W2) then ! this is yuk but haven't done others yet              
          call enforce_bc_w2(nlayers,ndf,undf,map,boundary_dofs,Ax_p%data)           
       end if'''
        assert(str(generated_code).find(output2)!=-1)

    def test_kernel_specific2(self):

        '''tests that kernel-specific code is added to the
           ru_kernel kernel. This code is required as
           the dynamo0.3 api does not know about boundary conditions
           but this kernel requires them. This "hack" is only
           supported to get PSyclone to generate correct code for the
           current implementation of dynamo. Future API's will not
           support any hacks.
        '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","12.1_kernel_specific.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        output1="INTEGER, pointer :: boundary_dofs_w2(:,:) => null()"
        assert(str(generated_code).find(output1)!=-1)
        output2="boundary_dofs_w2 => a_proxy%vspace%get_boundary_dofs()"
        assert(str(generated_code).find(output2)!=-1)
        output3="CALL ru_code(nlayers, a_proxy%data, b_proxy%data, c_proxy%data, d_proxy(1)%data, d_proxy(2)%data, d_proxy(3)%data, ndf_w2, undf_w2, map_w2, basis_w2, diff_basis_w2, boundary_dofs_w2, ndf_w3, undf_w3, map_w3, basis_w3, ndf_w0, undf_w0, map_w0, basis_w0, diff_basis_w0, nqp_h, nqp_v, wh, wv)"
        assert(str(generated_code).find(output3)!=-1)
