!-------------------------------------------------------------
! (c) Copyright Science and Technology Facilities Council 2016
!-------------------------------------------------------------
! Author R. Ford STFC Daresbury Lab

module testkern
  type, extends(kernel_type) :: testkern_type
     type(arg_type), dimension(2) :: meta_args = (/ &
             arg_type(gh_rscalar, gh_sum),         &
             arg_type(gh_field,   gh_write, w3)     &
           /)
     integer, parameter :: iterates_over = cells
   contains
     procedure() :: code => testkern_code
  end type testkern_type
contains

  subroutine testkern_code(rsum, field)
    integer, intent(inout) :: rsum
    real, intent(out) :: field
  end subroutine testkern_code
end module testkern
