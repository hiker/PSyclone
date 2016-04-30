!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2015. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
!
!>@brief Meta-data for the Dynamo 0.3 built-in operations.
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
     type(arg_type) :: meta_args(5) = (/                                &
          arg_type(GH_RSCALAR, GH_READ             ),                   &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_RSCALAR, GH_READ             ),                   &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_WRITE, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: axpby_code
  end type axpby

  !> field1 = a*field1 + b*field2
  type, public, extends(kernel_type) :: inc_axpby
     private
     type(arg_type) :: meta_args(4) = (/                                &
          arg_type(GH_RSCALAR, GH_READ             ),                   &
          arg_type(GH_FIELD,   GH_INC, ANY_SPACE_1),                    &
          arg_type(GH_RSCALAR, GH_READ             ),                   &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: inc_axpby_code
  end type inc_axpby

  !> field3 = a*field1 + field2
  type, public, extends(kernel_type) :: axpy
     private
     type(arg_type) :: meta_args(4) = (/                                &
          arg_type(GH_RSCALAR, GH_READ             ),                   &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_WRITE, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: axpy_code
  end type axpy

  !> field1 = a*field1 + field2
  type, public, extends(kernel_type) :: inc_axpy
     private
     type(arg_type) :: meta_args(4) = (/                               &
          arg_type(GH_RSCALAR, GH_READ             ),                  &
          arg_type(GH_FIELD,   GH_INC,  ANY_SPACE_1),                  &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: inc_axpy_code
  end type inc_axpy

  !> field2 = field1
  type, public, extends(kernel_type) :: copy_field
     private
     type(arg_type) :: meta_args(2) = (/                                &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_WRITE, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: copy_field_code
  end type copy_field

  !> field2 = a*field1
  type, public, extends(kernel_type) :: copy_scaled_field
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_RSCALAR, GH_READ             ),                  &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD,  GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: copy_scaled_field_code
  end type copy_scaled_field

  !> field1 = field1 / field2
  type, public, extends(kernel_type) :: divide_field
     private
     type(arg_type) :: meta_args(2) = (/                              &
          arg_type(GH_FIELD,  GH_INC, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: divide_field_code
  end type divide_field

  !> field3 = field1 / field2
  type, public, extends(kernel_type) :: divide_fields
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: divide_fields_code
  end type divide_fields

  !> field1 = field1 + field2
  type, public, extends(kernel_type) :: inc_field
     private
     type(arg_type) :: meta_args(2) = (/                               &
          arg_type(GH_FIELD, GH_INC,  ANY_SPACE_1),                    &
          arg_type(GH_FIELD, GH_READ, ANY_SPACE_1)                     &
          /)
     contains
       procedure, nopass :: inc_field_code
  end type inc_field

  !> sum = sum + field1(i,j,..) * field2(i,j,...)
  type, public, extends(kernel_type) :: inner_prod
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_RSCALAR, GH_SUM              )                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: inner_prod_code
  end type inner_prod

  !> field3 = field1 - field2
  type, public, extends(kernel_type) :: minus_fields
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: minus_fields_code
  end type minus_fields

  !> field3(:) = field1(:) * field2(:)
  type, public, extends(kernel_type) :: multiply_fields
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD,  GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: multiply_fields_code
  end type multiply_fields

  !> field3 = field1 + field2
  type, public, extends(kernel_type) :: plus_fields
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD,  GH_READ, ANY_SPACE_1),                   &
          arg_type(GH_FIELD, GH_WRITE, ANY_SPACE_1)                    &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: plus_fields_code
  end type plus_fields

  !> field1 = ascalar
  type, public, extends(kernel_type) :: set_field_scalar
     private
     type(arg_type) :: meta_args(2) = (/                                &
          arg_type(GH_RSCALAR, GH_READ),                                &
          arg_type(GH_FIELD,   GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: set_field_scalar_code
  end type set_field_scalar

  !> scalar = SUM(field1(:,:,...))
  type, public, extends(kernel_type) :: sum_field
     private
     type(arg_type) :: meta_args(2) = (/                               &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_RSCALAR, GH_SUM              )                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: sum_field_code
  end type sum_field

contains

  subroutine axpby_code()
  end subroutine axpby_code

  subroutine inc_axpby_code()
  end subroutine inc_axpby_code

  subroutine axpy_code()
  end subroutine axpy_code

  subroutine inc_axpy_code()
  end subroutine inc_axpy_code

  subroutine copy_field_code()
  end subroutine copy_field_code

  subroutine copy_scaled_field_code()
  end subroutine copy_scaled_field_code

  subroutine divide_field_code()
  end subroutine divide_field_code

  subroutine divide_fields_code()
  end subroutine divide_fields_code

  subroutine inc_field_code()
  end subroutine inc_field_code

  subroutine inner_prod_code()
  end subroutine inner_prod_code

  subroutine minus_fields_code()
  end subroutine minus_fields_code

  subroutine multiply_fields_code()
  end subroutine multiply_fields_code

  subroutine plus_fields_code()
  end subroutine plus_fields_code

  subroutine set_field_scalar_code()
  end subroutine set_field_scalar_code

  subroutine sum_field_code()
  end subroutine sum_field_code
  
end module dynamo0p3_builtins_mod
