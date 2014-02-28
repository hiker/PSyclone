!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2014. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
!
!-------------------------------------------------------------------------------
module v3_kernel_mod
use lfric
use gaussian_quadrature_mod 
use constants_mod, only: dp
implicit none

type(gaussian_quadrature_type) :: gaussian_quadrature

private
public v3_kernel_type

!-------------------------------------------------------------------------------
! Public types
!-------------------------------------------------------------------------------

type, public, extends(kernel_type) :: v3_kernel_type
  private
  type(arg) :: meta_args(1) = (/ &
       arg(readwrite,v3,FE) /)
  integer :: iterates_over = cells
contains
  procedure, nopass :: code => RHS_v3_code
!  procedure :: operate
end type  

!------------------------------------- ------------------------------------------
! Constructors
!-------------------------------------------------------------------------------

! overload the default structure constructor for function space
interface v3_kernel_type
   module procedure v3_kernel_constructor
end interface

!-------------------------------------------------------------------------------
! Contained functions/subroutines
!-------------------------------------------------------------------------------
public RHS_v3_code
contains

type(v3_kernel_type) function v3_kernel_constructor() result(self)
  ! no arguments, simply call the constructor for gaussian quadrature
  gaussian_quadrature  = gaussian_quadrature_type()
  return
end function v3_kernel_constructor
  
subroutine RHS_v3_code(nlayers,map,X)
  ! needs to compute the integral of rho_df * P 
  ! P_analytic over a single column
  
  !Arguments
  integer, intent(in) :: nlayers
  integer, intent(in) :: map(1) ! hard coded
  real(kind=dp), intent(inout) :: X(*)


  !Internal variables
  integer               :: df, k
  integer               :: ndf
  integer               :: qp1, qp2, qp3
  real(kind=dp), dimension(ngp,ngp,ngp) :: f
  real(kind=dp), dimension(1,ngp,ngp,ngp) :: v3_basis 

  v3_basis = 1.0 ! hard-coded values, but the size is correct.

  ndf=1
  
  ! compute the analytic R integrated over one cell
  do k = 0, nlayers-1
    do df = 1, ndf
       do qp1 = 1, ngp
          do qp2 = 1, ngp
             do qp3 = 1, ngp
                f(qp1,qp2,qp3) = v3_basis(df,qp1,qp2,qp3) * real(k+1)
             end do
          end do
       end do
      X(map(df) + k) = gaussian_quadrature%integrate(f)
    end do
  end do
  
end subroutine RHS_v3_code

!subroutine operate(self,cell)
!    class(kernel_type)  :: self
!    integer, intent(in) :: cell
!end subroutine operate

function dummy_integration()
  real :: dummy_integration
  dummy_integration = 0.5
end function dummy_integration

end module v3_kernel_mod
