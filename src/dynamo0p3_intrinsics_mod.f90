!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2015. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
!
!>@brief Meta-data for the Dynamo 0.3 point-wise kernels.
!>@details This meta-data is purely to provide psyclone with a specification
!!         of each point-wise kernel. This specification is used for
!!         correctness checking as well as to enable optimisations of
!!         invokes containing pointwise kernel calls.
!!         The actual implementation of these pointwise kernels is
!!         generated by psyclone.
module dynamo0p3_intrinsics_mod

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

  !> field2 = a * field1
  type, public, extends(kernel_type) :: multiply_field
     private
     type(arg_type) :: meta_args(3) = (/                               &
          arg_type(GH_RSCALAR, GH_READ),                               &
          arg_type(GH_FIELD,   GH_READ, ANY_SPACE_1),                  &
          arg_type(GH_FIELD,  GH_WRITE, ANY_SPACE_1)                   &
          /)
     integer :: iterates_over = DOFS
   contains
     procedure, nopass :: multiply_field_code
  end type multiply_field

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

contains

  subroutine set_field_scalar_code()
  end subroutine set_field_scalar_code

  subroutine copy_field_code()
  end subroutine copy_field_code

  subroutine minus_fields_code()
  end subroutine minus_fields_code

  subroutine plus_fields_code()
  end subroutine plus_fields_code

  subroutine divide_fields_code()
  end subroutine divide_fields_code

  subroutine multiply_field_code()
  end subroutine multiply_field_code

  subroutine axpy_code()
  end subroutine axpy_code

  subroutine inner_prod_code()
  end subroutine inner_prod_code
  
end module dynamo0p3_intrinsics_mod
