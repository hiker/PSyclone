module v_mod
  implicit none

  private

  public v_type, compute_v
  type, extends(kernel_type) :: v_type
     type(arg), dimension(1) :: meta_args =    &
          (/ arg(WRITE, CV, POINTWISE)        &
           /)
     integer :: ITERATES_OVER = CV
  contains
    procedure, nopass :: code => compute_v
  end type v_type

contains

  subroutine compute_v(i,j,v)
    real(wp), intent(out),  dimension(:,:) :: v
    v(i,j)=0.0
  end subroutine compute_v

end module v_mod
