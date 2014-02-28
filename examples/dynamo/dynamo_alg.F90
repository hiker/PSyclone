!BEGINSOURCE <open file 'dynamo.F90', mode 'r' at 0x27c1c90> mode=free
  !-------------------------------------------------------------------------------
  ! (c) The copyright relating to this work is owned jointly by the Crown,
  ! Met Office and NERC 2014.
  ! However, it has been created with the help of the GungHo Consortium,
  ! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
  !-------------------------------------------------------------------------------

  PROGRAM dynamo
    USE psy_dynamo, ONLY: invoke_1
    USE psy_dynamo, ONLY: invoke_0
    USE lfric
    USE v3_kernel_mod, ONLY: v3_kernel_type
    USE v3_solver_kernel_mod, ONLY: v3_solver_kernel_type
    IMPLICIT NONE

    TYPE(function_space_type) v3_function_space
    TYPE(v3_kernel_type) v3_kernel
    TYPE(v3_solver_kernel_type) v3_solver_kernel
    TYPE(field_type) pressure_density, rhs

    INTEGER cell

    INTEGER num_cells, num_dofs, num_unique_dofs, num_layers

    WRITE (*, '("Dynamo:Hello, World")')
    CALL dummy_read_header("dummy_mesh_v3", num_cells, num_dofs, num_unique_dofs, num_layers)

    ! create the v3 function space type
    v3_function_space = function_space_type(num_cells=num_cells, num_dofs=num_dofs, num_unique_dofs=num_unique_dofs)

    ! read in the connectivity table, or dofmap
    CALL dummy_read_dofmap("dummy_mesh_v3", num_layers, v3_function_space)

    pressure_density = field_type(vector_space = v3_function_space,        num_layers = num_layers)

    rhs = field_type(vector_space = v3_function_space,        num_layers = num_layers)

    v3_kernel = v3_kernel_type()
    v3_solver_kernel = v3_solver_kernel_type()
    !Construct PSy layer given a list of kernels. This is the line the code
    !generator may parse and do its stuff.
    CALL invoke_0(rhs)
    !  call invoke_RHS_V3(rhs)
    CALL invoke_1(pressure_density, rhs)
    !  call invoke_v3_solver_kernel(pressure_density,rhs)


    DO cell=1,num_cells*num_layers
      WRITE (*, *) cell, pressure_density%data(cell), rhs%data(cell)
    END DO 
  END PROGRAM dynamo

  SUBROUTINE dummy_read_header(filename, num_cells, num_dofs, num_unique_dofs, num_layers)
    ! dummy read the mesh routine, or at least the header
    IMPLICIT NONE
    CHARACTER(LEN=*), intent(in) :: filename
    ! this is dummy and no used
    INTEGER, intent(out) :: num_cells, num_dofs, num_unique_dofs, num_layers

    ! no file or file format, just coded for now v3, lowest order on quads
    ! Bi-linear plane, 3x3x3
    ! this is completely discontinuous so the dofs are all independent.
    num_cells = 9
    num_dofs = 1
    num_unique_dofs = 9
    num_layers = 3
    RETURN
  END SUBROUTINE dummy_read_header

  SUBROUTINE dummy_read_dofmap(filename, num_layers, v3space)
    USE function_space_mod, ONLY: function_space_type
    IMPLICIT NONE
    CHARACTER(LEN=*), intent(in) :: filename
    ! this is a dummy and no used
    INTEGER, intent(in) :: num_layers
    TYPE(function_space_type) v3space


    INTEGER cell
    INTEGER map(1)
    ! really hacky but in the real code this could be
    ! allocatable, depending on what the mesh read in
    ! and it won't be done in this routine.

    ! this routine explicitly populates the dof map for a v3 space on a
    ! bi-periodic plane  with quads at lowest order

    ! 1st cell
    map(1) = 1
    DO cell = 1, v3space%get_ncell()
      CALL v3space%populate_cell_dofmap(cell, map)
      map(1) = map(1) + num_layers
    END DO 

  END SUBROUTINE dummy_read_dofmap
