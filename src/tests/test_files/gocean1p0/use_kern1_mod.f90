module use_kern1_mod

  use module1

  implicit none

  private

  public use_kern1, use_kern1_code

  type, extends(kernel_type) :: use_kern1
     type(arg), dimension(1) :: meta_args =    &
          (/ arg(WRITE, CU, POINTWISE)         & ! cu
           /)
     integer :: ITERATES_OVER = INTERNAL_PTS
     integer :: index_offset = OFFSET_SW

  contains
    procedure, nopass :: code => use_kern1_code
  end type use_kern1

contains

  subroutine use_kern1_code(a)
    use module2
  end subroutine use_kern1_code


end module use_kern1_mod
