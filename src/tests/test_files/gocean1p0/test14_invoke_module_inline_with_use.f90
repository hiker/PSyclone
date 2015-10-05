!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown,
! Met Office and NERC 2015.
! However, it has been created with the help of the GungHo Consortium,
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
! Author R, Ford STFC Daresbury Lab

PROGRAM module_inline_with_use

  use use_kern1_mod, only: use_kern1

  call invoke( use_kern1(a) )

END PROGRAM module_inline_with_use
