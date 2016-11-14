!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown,
! Met Office and NERC 2014.
! However, it has been created with the help of the GungHo Consortium,
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
! Author A. R. Porter, STFC Daresbury Lab

program single_function

  ! Description: type-bound procedure called from an array element
  ! reference
  use testkern_qr, only: testkern_qr_type
  use inf,      only: field_type
  implicit none
  type(field_type) :: f0(2),f1(2,2)
  type(quadrature_rule_type) :: qr
  real(r_def) :: b(2), a(8)
  integer :: iflag(4)

  call f0(1)%log_minmax(LOG_LEVEL_DEBUG(3),'max/min r_u = ')

  call invoke(                                                  &
       testkern_qr_type(f0(1),f1(1,1),f1(2,index),b(1),         &
                        f1(index,index2(index3)),iflag(2), qr) )

end program single_function
