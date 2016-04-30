! Author A. R. Porter STFC Daresbury Lab

program single_invoke

  ! Description: single point-wise operation (y = a* x)
  ! specified in an invoke call
  use testkern, only: testkern_type
  use inf,      only: field_type
  implicit none
  type(field_type) :: f1, f2
  real(r_def) :: a

  call invoke(                            &
              copy_scaled_field(a, f1, f2)   &
             )

end program single_invoke
