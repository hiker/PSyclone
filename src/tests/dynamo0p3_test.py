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
        output = """   SUBROUTINE invoke_0_testkern_type(f1, f2, m1, m2)
      USE testkern, ONLY: testkern_code
      TYPE(field_type), intent(inout) :: f1, f2, m1, m2
      INTEGER cell
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
      ! Call our kernels
      !
      DO cell=1,f1%get_ncell()
        CALL testkern_code(f1%data, f2%data, m1%data, m2%data)
      END DO 
      !
    END SUBROUTINE invoke_0_testkern_type
"""
        assert str(generated_code).find(output)!=-1
    def test_field_qr(self):
        ''' tests that a call, with a set of fields requiring quadrature, produces correct code '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","1.1_single_invoke_qr.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        output = """
    SUBROUTINE invoke_0_testkern_qr_type(f1, f2, m1, m2, qr)
      USE testkern_qr, ONLY: testkern_qr_code
      TYPE(field_type), intent(inout) :: f1, f2, m1, m2
      TYPE(quadrature_type), intent(in) :: qr
      INTEGER cell
      INTEGER dim_w3, diff_dim_w3, diff_dim_w2, dim_w1
      INTEGER ndf_w3, undf_w3, ndf_w2, undf_w2, ndf_w1, undf_w1
      REAL(KIND=r_def), allocatable :: gh_basis_w3(:,:,:,:), gh_diff_basis_w3(:,:,:,:), gh_diff_basis_w2(:,:,:,:), gh_basis_w1(:,:,:,:)
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
      nqp_h = qr%get_nqp_h()
      nqp_v = qr%get_nqp_v()
      zp = qr%get_zp()
      xp = qr%get_xp()
      wh = qr%get_wh()
      wv = qr%get_wv()
      !
      ! Initialise sizes and allocate basis arrays for w3
      !
      ndf_w3 = m2_proxy%vspace%get_ndf()
      undf_w3 = m2_proxy%vspace%get_undf()
      dim_w3 = m2_proxy%vspace%get_dim_space()
      ALLOCATE (gh_basis_w3(dim_w3, ndf_w3, nqp_h, nqp_v))
      diff_dim_w3 = m2_proxy%vspace%get_dim_space_diff()
      ALLOCATE (gh_diff_basis_w3(diff_dim_w3, ndf_w3, nqp_h, nqp_v))
      !
      ! Initialise sizes and allocate basis arrays for w2
      !
      ndf_w2 = f2_proxy%vspace%get_ndf()
      undf_w2 = f2_proxy%vspace%get_undf()
      diff_dim_w2 = f2_proxy%vspace%get_dim_space_diff()
      ALLOCATE (gh_diff_basis_w2(diff_dim_w2, ndf_w2, nqp_h, nqp_v))
      !
      ! Initialise sizes and allocate basis arrays for w1
      !
      ndf_w1 = f1_proxy%vspace%get_ndf()
      undf_w1 = f1_proxy%vspace%get_undf()
      dim_w1 = f1_proxy%vspace%get_dim_space()
      ALLOCATE (gh_basis_w1(dim_w1, ndf_w1, nqp_h, nqp_v))
      !
      ! Compute basis arrays
      !
      CALL m2_proxy%vspace%compute_gh_basis_function(gh_basis_w3, ndf_w3, nqp_h, nqp_v, xp, zp)
      CALL m2_proxy%vspace%compute_gh_diff_basis_function(gh_diff_basis_w3, ndf_w3, nqp_h, nqp_v, xp, zp)
      CALL f2_proxy%vspace%compute_gh_diff_basis_function(gh_diff_basis_w2, ndf_w2, nqp_h, nqp_v, xp, zp)
      CALL f1_proxy%vspace%compute_gh_basis_function(gh_basis_w1, ndf_w1, nqp_h, nqp_v, xp, zp)
      !
      ! Call our kernels
      !
      DO cell=1,f1%get_ncell()
        CALL testkern_qr_code(f1%data, f2%data, m1%data, m2%data)
      END DO 
      !
      ! Deallocate basis arrays
      !
      DEALLOCATE (gh_basis_w3, gh_diff_basis_w3, gh_diff_basis_w2, gh_basis_w1)
      !
    END SUBROUTINE invoke_0_testkern_qr_type
"""
        assert str(generated_code).find(output)!=-1
    def test_vector_field(self):
        ''' tests that a vector field is declared correctly in the PSy layer '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","8_vector_field.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        assert(str(generated_code).find("SUBROUTINE invoke_0_testkern_chi_type(f1, chi)")!=-1 and \
                  str(generated_code).find("TYPE(field_type), intent(inout) :: f1, chi(3)")!=-1)
