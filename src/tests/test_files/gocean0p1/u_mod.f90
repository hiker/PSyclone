module u_mod
  implicit none

  private

  public u_type, compute_u
  type, extends(kernel_type) :: u_type
     type(arg), dimension(1) :: meta_args =    &
          (/ arg(WRITE, CU, POINTWISE)        &
           /)
     integer :: ITERATES_OVER = CU
  contains
    procedure, nopass :: code => compute_u
  end type u_type

contains

  subroutine compute_u(i,j,u)
    real(wp), intent(out),  dimension(:,:) :: u
    u(i,j)=0.0
  end subroutine compute_u

end module u_mod

