module use_kern2_mod

  ! full name clash with other modules
  use module1, only : a,b,c
  ! partial name clash with another module
  use module2, only : d,e

  ! full overlap with the same module
  use module3, only : f,g
  ! partial overlap with same module
  use module4, only : h,i

  ! overlap with same module, no only in subroutine
  use module5, only : j
  ! overlap with same module, no only in module
  use module6

  ! no overlap with same module
  use module7, only : k

  ! unique module, only
  use module8, only : l
  ! unique module, no only
  use module9

  implicit none

  private

  public use_kern2, use_kern2_code

  type, extends(kernel_type) :: use_kern2
     type(arg), dimension(1) :: meta_args =    &
          (/ arg(WRITE, CU, POINTWISE)         & ! cu
           /)
     integer :: ITERATES_OVER = INTERNAL_PTS
     integer :: index_offset = OFFSET_SW

  contains
    procedure, nopass :: code => use_kern2_code
  end type use_kern2

contains

  subroutine use_kern2_code()
    use module10, only : a,b
    use module11, only : c
    use module12, only : d,m
    use module3, only : f,g
    use module4, only : h,n
    use module5
    use module6, only : o
    use module7, only : p
    use module13, only, q
    use module14

    !expected ...
    !use module2, only : e
    !use module3, only : f,g
    !use module4, only : h,i,n
    !use module5 ! j is in module5
    !use module6 ! o is in module6
    !use module7, only : k,p
    !use module8, only : l
    !use module9
    !use module10, only : a,b
    !use module11, only : c
    !use module12, only : d,m
    !use module13, only : q
    !use module14

  end subroutine use_kern2_code


end module use_kern2_mod
