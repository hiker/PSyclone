!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2014. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
!
!-------------------------------------------------------------------------------
module v3_solver_kernel_mod
use lfric
use gaussian_quadrature_mod 
use constants_mod, only: dp
implicit none

type(gaussian_quadrature_type) :: gaussian_quadrature

private

!-------------------------------------------------------------------------------
! Public types
!-------------------------------------------------------------------------------
public v3_solver_kernel_type
type, extends(kernel_type) :: v3_solver_kernel_type
  private
  type(arg) :: meta_args(2) = (/ &
       arg(readwrite,v3,FE), &
       arg(read,v3,FE) /)
  integer :: iterates_over = cells
contains
  procedure, nopass :: code => solver_v3_code
end type

!-------------------------------------------------------------------------------
! Constructors
!-------------------------------------------------------------------------------

! overload the default structure constructor for function space
interface v3_solver_kernel_type
   module procedure v3_solver_kernel_constructor
end interface

!-------------------------------------------------------------------------------
! Contained functions/subroutines
!-------------------------------------------------------------------------------
public solver_v3_code
contains

type(v3_solver_kernel_type) function v3_solver_kernel_constructor() result(self)
  ! no arguments, simply call the constructor for gaussian quadrature
  gaussian_quadrature  = gaussian_quadrature_type()
  return
end function v3_solver_kernel_constructor
  
subroutine solver_v3_code(nlayers,map,X,RHS)
  ! needs to compute the integral of rho_df * P 
  ! P_analytic over a single column
  
  !Arguments
  integer, intent(in) :: nlayers
  integer, intent(in) :: map(1) ! hard coded
  real(kind=dp), intent(inout) :: X(*)
  real(kind=dp), intent(in) :: RHS(*)


  !Internal variables
  integer               :: df1, df2, k
  integer               :: ndf
  integer               :: qp1, qp2, qp3
  real(kind=dp), dimension(ngp,ngp,ngp) :: f
  real(kind=dp), dimension(1,ngp,ngp,ngp) :: v3_basis 
  real(kind=dp), dimension(1,1) :: M_v3, inv_M_v3

  v3_basis = 1.0 ! hard-coded values, but the size is correct.

  ndf=1
  
  ! compute the LHS integrated over one cell and solve
  do k = 0, nlayers-1
    do df1 = 1, ndf
       do df2 = 1,ndf
          do qp1 = 1, ngp
             do qp2 = 1, ngp
                do qp3 = 1, ngp
                   f(qp1,qp2,qp3) = v3_basis(df1,qp1,qp2,qp3) * &
                                    v3_basis(df2,qp1,qp2,qp3)
                end do
             end do
          end do
          M_v3(df1,df2) = gaussian_quadrature%integrate(f)
       end do
    end do
    inv_M_v3(1,1) = 1.0/M_v3(1,1)
    X(map(1)+k) = inv_M_v3(1,1)*RHS(map(1)+k)
  end do
  
end subroutine solver_v3_code

end module v3_solver_kernel_mod
