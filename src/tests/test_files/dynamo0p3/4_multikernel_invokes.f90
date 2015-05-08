!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown,
! Met Office and NERC 2014.
! However, it has been created with the help of the GungHo Consortium,
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
! Author R. Ford STFC Daresbury Lab

program multikernel_invokes_1

  ! Description: multiple kernel calls within an invoke
  use testkern, only : testkern_type
  use testkern_qr, only : testkern_qr_type
  use testkern_chi, only : testkern_chi_type
  use testkern_operator_mod, only : testkern_operator_type
  use inf,      only: field_type, quadrature_rule_type, operator_type
  implicit none
  type(field_type) :: f1, f2, m1, m2, chi(3)
  type(quadrature_rule_type) :: qr
  type(operator_type) :: op1

  call invoke(                            &
       testkern_type(f1,f2,m1,m2),        &
       testkern_type(f1,f2,m1,m2)         &
       )

end program multikernel_invokes_1
