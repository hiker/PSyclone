!>@brief Broken meta-data for the Dynamo 0.3 built-in operations.
!>@details This meta-data is purely to provide psyclone with a specification
!!         of each operation. This specification is used for
!!         correctness checking as well as to enable optimisations of
!!         invokes containing calls to built-in operations.
!!         The actual implementation of these built-ins is
!!         generated by psyclone (hence the empty ..._code routines in
!!         this file).
module dynamo0p3_builtins_mod

  !> field3 = a*field1 + b*field2
  type, public, extends(kernel_type) :: axpby
     private
     type(arg_type) :: meta_args(5) = (/                              &
          arg_type(GH_REAL,  GH_READ              ),                  &
          arg_type(GH_FIELD, GH_READ,  ANY_SPACE_1),                  &
          arg_type(GH_REAL,  GH_READ              ),                  &
          arg_type(GH_FIELD, GH_READ,  ANY_SPACE_1),                  &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: axpby_code
  end type blah ! BROKEN

  !> field3 = a*field1 + field2
  type, public, extends(kernel_type) :: axpy
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_REAL,  GH_READ             ),                   &
          arg_type(GH_FIELD, GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD, GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: axpy_code
  end type axpy

contains

  subroutine axpy_code()
  end subroutine axpy_code
  
end module dynamo0p3_builtins_mod