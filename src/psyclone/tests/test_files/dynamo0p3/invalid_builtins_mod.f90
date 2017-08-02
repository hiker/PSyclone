! Modified I. Kavcic Met Office

!>@brief Broken meta-data for the Dynamo 0.3 built-in operations.
!>@details This meta-data is purely to provide psyclone with a
!specification
!!         of each operation. This specification is used for
!!         correctness checking as well as to enable optimisations of
!!         invokes containing calls to built-in operations.
!!         The actual implementation of these built-ins is
!!         generated by psyclone (hence the empty ..._code routines in
!!         this file).
module dynamo0p3_builtins_mod

  !> An invalid built-in that writes to more than one field
  type, public, extends(kernel_type) :: axpy
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_REAL,  GH_READ              ),                  &
          arg_type(GH_FIELD, GH_READ,  ANY_SPACE_1),                  &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1),                  &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: axpy_code
  end type axpy

  !> An invalid built-in that updates two fields where one is gh_sum
  !! and the other is gh_inc
  type, public, extends(kernel_type) :: inc_axpy
     private
     type(arg_type) :: meta_args(3) = (/                            &
          arg_type(GH_REAL,  GH_SUM            ),                   &
          arg_type(GH_FIELD, GH_INC, ANY_SPACE_1),                  &
          arg_type(GH_FIELD, GH_READ, ANY_SPACE_1)                  &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: inc_axpy_code
  end type inc_axpy

  !> An invalid built-in that doesn't write to any argument
  type, public, extends(kernel_type) :: axpby
     private
     type(arg_type) :: meta_args(5) = (/                             &
          arg_type(GH_REAL,  GH_READ              ),                 &
          arg_type(GH_FIELD, GH_READ,  ANY_SPACE_1),                 &
          arg_type(GH_REAL,  GH_READ              ),                 &
          arg_type(GH_FIELD, GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD, GH_READ, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: axpby_code
  end type axpby

  !> An invalid built-in that writes to two different
  !! args but with different access types - one is gh_write, one is gh_inc.
  type, public, extends(kernel_type) :: inc_aX_plus_bY
     private
     type(arg_type) :: meta_args(4) = (/                              &
          arg_type(GH_REAL,  GH_READ             ),                   &
          arg_type(GH_FIELD, GH_INC, ANY_SPACE_1),                    &
          arg_type(GH_REAL,  GH_READ             ),                   &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: inc_aX_plus_bY_code
  end type inc_aX_plus_bY

  !> An invalid built-in that has no field arguments
  type, public, extends(kernel_type) :: copy_field
     private
     type(arg_type) :: meta_args(2) = (/               &
          arg_type(GH_REAL, GH_READ),                  &
          arg_type(GH_REAL, GH_SUM)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: copy_field_code
  end type copy_field

  !> Invalid built-in that claims to take an operator as an argument
  type, public, extends(kernel_type) :: copy_scaled_field
     private
     type(arg_type) :: meta_args(3) = (/                              &
          arg_type(GH_REAL,  GH_READ              ),                  &
          arg_type(GH_OPERATOR, GH_READ, ANY_SPACE_1, ANY_SPACE_1),   &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: copy_scaled_field_code
  end type copy_scaled_field

  !> Invalid built-in that has arguments on different spaces
  type, public, extends(kernel_type) :: inc_X_divideby_Y
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD,  GH_INC, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_2)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: inc_X_divideby_Y_code
  end type inc_X_divideby_Y

contains

  subroutine axpy_code()
  end subroutine axpy_code

  subroutine inc_axpy_code()
  end subroutine inc_axpy_code

  subroutine axpby_code()
  end subroutine axpby_code

  subroutine inc_aX_plus_bY_code()
  end subroutine inc_aX_plus_bY_code

  subroutine copy_field_code()
  end subroutine copy_field_code

  subroutine copy_scaled_field_code()
  end subroutine copy_scaled_field_code

  subroutine inc_X_divideby_Y_code()
  end subroutine inc_X_divideby_Y_code

end module dynamo0p3_builtins_mod

