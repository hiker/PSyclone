    program kernel_specific_example1

    ! the matrix vector_mm kernel currently requires additional
    ! boundary layer information to be set up which is not described
    ! in the API. Therefore, for the moment, we add this in when we
    ! see the matrix_vector_mm kernel.

    use matrix_vector_mm_mod, only : matrix_vector_kernel_mm_type

    call invoke(matrix_vector_kernel_mm_type(a, b, c))

    end program kernel_specific_example1
