!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown,
! Met Office and NERC 2015.
! However, it has been created with the help of the GungHo Consortium,
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
! Author R, Ford STFC Daresbury Lab

PROGRAM module_inline_with_use_clash

  use use_kern2_mod, only: use_kern2

  call invoke( use_kern2(a) )

END PROGRAM module_inline_with_use_clash
