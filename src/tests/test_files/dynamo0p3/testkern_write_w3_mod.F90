!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2014. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
!
!-------------------------------------------------------------------------------

!> @brief The kernel computes the cell integrated potential vorticity
!> int( xi . grad(theta) dV )
module testkern_write_w3_mod
use kernel_mod,              only : kernel_type
use argument_mod,            only : arg_type, func_type,                     &
                                    GH_FIELD, GH_WRITE, GH_READ,             &
                                    W0, W1, W3,                              &
                                    GH_BASIS, GH_DIFF_BASIS, GH_ORIENTATION, &
                                    CELLS
use constants_mod,           only : r_def, earth_radius

implicit none

!-------------------------------------------------------------------------------
! Public types
!-------------------------------------------------------------------------------
!> The type declaration for the kernel. Contains the metadata needed by the Psy layer
type, public, extends(kernel_type) :: compute_total_pv_kernel_type
  private
  type(arg_type) :: meta_args(4) = (/                                  &
       arg_type(GH_FIELD,   GH_WRITE, W3),                             &
       arg_type(GH_FIELD,   GH_READ,  W1),                             &
       arg_type(GH_FIELD,   GH_READ,  W0),                             &
       arg_type(GH_FIELD*3, GH_READ,  W0)                              &
       /)
  type(func_type) :: meta_funcs(2) = (/                                &
       func_type(W0, GH_DIFF_BASIS),                                   &
       func_type(W1, GH_BASIS, GH_ORIENTATION)                         &
       /)
  integer :: iterates_over = CELLS
contains
  procedure, nopass ::compute_total_pv_code
end type

!-------------------------------------------------------------------------------
! Constructors
!-------------------------------------------------------------------------------

! overload the default structure constructor for function space
interface compute_total_pv_kernel_type
   module procedure compute_total_pv_kernel_constructor
end interface

!-------------------------------------------------------------------------------
! Contained functions/subroutines
!-------------------------------------------------------------------------------
public compute_total_pv_code
contains

type(compute_total_pv_kernel_type) function compute_total_pv_kernel_constructor() result(self)
  return
end function compute_total_pv_kernel_constructor

!> @brief The subroutine which is called directly by the Psy layer
!! @param[in] nlayers Integer the number of layers
!! @param[out] pv The cell integrated pv
!! @param[in] ndf_w1 The number of degrees of freedom per cell for w1
!! @param[in] undf_w1  The number of unique degrees of freedom  for w1
!! @param[in] map_w1 Integer array holding the dofmap for the cell at the base of the column for w1
!! @param[in] w1_basis Real 5-dim array holding basis functions evaluated at gaussian quadrature points 
!! @param[in] orientation The orientation array for w1
!! @param[in] xi The absolute vorticity
!! @param[in] ndf_w0 The number of degrees of freedom per cell for w0
!! @param[in] undf_w0  The number of unique degrees of freedom  for w0
!! @param[in] map_w0 Integer array holding the dofmap for the cell at the base of the column for w0
!! @param[in] w0_diff_basis Real 5-dim array holding differential basis functions evaluated at gaussian quadrature points 
!! @param[in] theta Real array the potential temperature
!! @param[in] chi1 The first component of the coordinate field
!! @param[in] chi2 The second component of the coordinate field
!! @param[in] chi3 The third component of the coordinate field
!! @param[in] nqp_h the number of horizontal quadrature points
!! @param[in] nqp_v the number of vertical quadrature points
!! @param[in] wqp_h the weights of the horizontal quadrature points
!! @param[in] wqp_v the weights of the vertical quadrature points
subroutine compute_total_pv_code(                                                        &
                                 nlayers,                                                &
                                 pv,                                                     &
                                 xi,                                                     &
                                 theta,                                                  &
                                 chi1, chi2, chi3,                                       &
                                 ndf_w3, undf_w3, map_w3,                                &
                                 ndf_w1, undf_w1, map_w1, w1_basis, orientation,         &
                                 ndf_w0, undf_w0, map_w0, w0_diff_basis,                 &
                                 nqp_h, nqp_v, wqp_h, wqp_v )
                               
  use coordinate_jacobian_mod, only: coordinate_jacobian, &
                                     coordinate_jacobian_inverse

  !Arguments
  integer, intent(in) :: nlayers, nqp_h, nqp_v
  integer, intent(in) :: ndf_w0, ndf_w1, undf_w0, undf_w1, ndf_w3, undf_w3

  integer, dimension(ndf_w3), intent(in) :: map_w3
  integer, dimension(ndf_w0), intent(in) :: map_w0
  integer, dimension(ndf_w1), intent(in) :: map_w1, orientation

  real(kind=r_def), dimension(3,ndf_w0,nqp_h,nqp_v), intent(in) :: w0_diff_basis  
  real(kind=r_def), dimension(3,ndf_w1,nqp_h,nqp_v), intent(in) :: w1_basis 

  real(kind=r_def), dimension(undf_w3), intent(out)   :: pv
  real(kind=r_def), dimension(undf_w0), intent(in)    :: theta
  real(kind=r_def), dimension(undf_w0), intent(in)    :: chi1, chi2, chi3
  real(kind=r_def), dimension(undf_w1), intent(in)    :: xi

  real(kind=r_def), dimension(nqp_h), intent(in)      ::  wqp_h
  real(kind=r_def), dimension(nqp_v), intent(in)      ::  wqp_v

  !Internal variables
  integer               :: df, k 
  integer               :: qp1, qp2
  
  real(kind=r_def), dimension(ndf_w0)          :: chi1_e, chi2_e, chi3_e, theta_e
  real(kind=r_def), dimension(ndf_w1)          :: xi_e
  real(kind=r_def), dimension(ndf_w3)          :: pv_e
  real(kind=r_def), dimension(3)               :: xi_at_quad, &
                                                  grad_theta_at_quad
  real(kind=r_def), dimension(nqp_h,nqp_v)     :: dj
  real(kind=r_def), dimension(3,3,nqp_h,nqp_v) :: jac, jac_inv
 
  do k = 0, nlayers-1
  ! Extract element arrays of chi and theta    
    do df = 1, ndf_w0
      chi1_e(df) = chi1( map_w0(df) + k )
      chi2_e(df) = chi2( map_w0(df) + k )
      chi3_e(df) = chi3( map_w0(df) + k )
      theta_e(df)  = theta(  map_w0(df) + k )
    end do
    call coordinate_jacobian(ndf_w0, nqp_h, nqp_v, chi1_e, chi2_e, chi3_e,  &
                             w0_diff_basis, jac, dj)
    call coordinate_jacobian_inverse(nqp_h, nqp_v, jac, dj, jac_inv)  
    do df = 1, ndf_w1
      xi_e(df) = xi( map_w1(df) + k )*real(orientation(df),r_def)
    end do
    pv_e(:) = 0.0_r_def
  ! compute the pv integrated over one cell
    do qp2 = 1, nqp_v
      do qp1 = 1, nqp_h
        xi_at_quad(:) = 0.0_r_def
        do df = 1, ndf_w1
          xi_at_quad(:)  = xi_at_quad(:)  + xi_e(df)*w1_basis(:,df,qp1,qp2)
        end do
        grad_theta_at_quad(:) = 0.0_r_def
        do df = 1, ndf_w0
          grad_theta_at_quad(:) = grad_theta_at_quad(:) &
                                + theta_e(df)*w0_diff_basis(:,df,qp1,qp2)
        end do
        do df = 1,ndf_w3
          pv_e(df) = pv_e(df) + wqp_h(qp1)*wqp_v(qp2)*dj(qp1,qp2) &
                    * dot_product(matmul(transpose(jac_inv(:,:,qp1,qp2)),xi_at_quad), &
                                  matmul(transpose(jac_inv(:,:,qp1,qp2)),grad_theta_at_quad)) &
                    /earth_radius**2 
        end do             
      end do
    end do
    do df = 1, ndf_w3
      pv(map_w3(df)+k) = pv_e(df)
    end do
  end do
  
end subroutine compute_total_pv_code

end module testkern_write_w3_mod
