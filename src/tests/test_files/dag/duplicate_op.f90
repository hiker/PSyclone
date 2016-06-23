module duplicate_op_mod
  implicit none

  private

contains

  !=================================================================

  subroutine test_duplicate_product(aprod, bprod, var1, var2, var3)
    ! Simple routine containing two assignments where the same
    ! product is duplicated.
    implicit none
    real(wp), intent(out) :: aprod, bprod
    real(wp), intent(in) :: var1, var2, var3

    aprod = var1 * var2 * var3

    bprod = var1 * var2 / var3
    
  end subroutine test_duplicate_product
  
end module duplicate_op_mod
