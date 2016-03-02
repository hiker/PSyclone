!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown,
! Met Office and NERC 2015.
! However, it has been created with the help of the GungHo Consortium,
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
! Author A. R. Porter STFC Daresbury Lab

program single_invoke

  ! Description: multiple point-wise set operations specified in an invoke call
  ! with the scalar values passed by both value and reference
  use testkern, only: testkern_type
  use inf,      only: field_type
  implicit none
  type(field_type) :: f1, f2
  real(r_def) :: fred, ginger

  fred = 20.1_r_def
  ginger = 40.5_r_def
  
  call invoke(                      &
       set_field_scalar(f1, fred),  &
       set_field_scalar(f2, 3.0),   &
       set_field_scalar(f3, ginger) &
          )

end program single_invoke

subroutine expected_code(f1, f2, value1, value2)
  do df = 1, undf_any_space_1
    f1(df) = value1
  end do
  do df = 1, undf_any_space_1
    f2(df) = 3.0
  end do
  do df = 1, undf_any_space_1
    f3(df) = value2
  end do
end subroutine expected_code
