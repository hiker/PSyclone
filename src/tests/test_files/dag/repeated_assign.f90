module repeated_assign_mod
  implicit none

contains

  subroutine test_repeated_assign(aprod, var1, var2, var3)
    ! Simple routine that contains multiple updates to the
    ! same variable
    implicit none
    real(wp), intent(out) :: aprod
    real(wp), intent(in) :: var1, var2, var3

    aprod = var1 * var2 * var3
    aprod = aprod * var1
    aprod = aprod * aprod

  end subroutine test_repeated_assign
  
end module repeated_assign_mod
