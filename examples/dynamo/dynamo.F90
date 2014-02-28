!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2014. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------

program dynamo
  use lfric
  use v3_kernel_mod,           only: v3_kernel_type
  use v3_solver_kernel_mod,    only: v3_solver_kernel_type
  implicit none

  type(function_space_type)      :: v3_function_space
  type(v3_kernel_type)           :: v3_kernel
  type(v3_solver_kernel_type)    :: v3_solver_kernel
  type(field_type)               :: pressure_density,rhs

  integer :: cell

  integer :: num_cells,num_dofs,num_unique_dofs,num_layers

  write(*,'("Dynamo:Hello, World")') 
  call dummy_read_header("dummy_mesh_v3",     &
       num_cells,                             &
       num_dofs,                              &
       num_unique_dofs,                       &
       num_layers)

  ! create the v3 function space type
  v3_function_space = function_space_type( &
       num_cells=num_cells, num_dofs=num_dofs, num_unique_dofs=num_unique_dofs)

  ! read in the connectivity table, or dofmap
  call dummy_read_dofmap("dummy_mesh_v3", &
       num_layers,                        &
       v3_function_space)

  pressure_density = field_type(vector_space = v3_function_space, &
       num_layers = num_layers)

  rhs = field_type(vector_space = v3_function_space, &
       num_layers = num_layers)

  v3_kernel = v3_kernel_type()
  v3_solver_kernel = v3_solver_kernel_type()
  !Construct PSy layer given a list of kernels. This is the line the code
  !generator may parse and do its stuff.
  call invoke (v3_kernel_type(rhs) )
!  call invoke_RHS_V3(rhs)
  call invoke (v3_solver_kernel_type(pressure_density,rhs) )
!  call invoke_v3_solver_kernel(pressure_density,rhs)


  do cell=1,num_cells*num_layers
    write(*,*) cell,pressure_density%data(cell),rhs%data(cell)
  end do
end program dynamo

subroutine dummy_read_header(filename ,num_cells, num_dofs, num_unique_dofs, &
     num_layers)
  ! dummy read the mesh routine, or at least the header
  implicit none
  character(*), intent(in) :: filename ! this is dummy and no used
  integer , intent(out) :: num_cells, num_dofs, num_unique_dofs, num_layers

  ! no file or file format, just coded for now v3, lowest order on quads
  ! Bi-linear plane, 3x3x3 
  ! this is completely discontinuous so the dofs are all independent.
  num_cells = 9
  num_dofs = 1
  num_unique_dofs = 9
  num_layers = 3
  return
end subroutine dummy_read_header

subroutine dummy_read_dofmap(filename,num_layers,v3space)
  use function_space_mod, only: function_space_type
  implicit none
  character(*), intent(in) :: filename ! this is a dummy and no used
  integer , intent(in) :: num_layers
  type(function_space_type) :: v3space
  

  integer :: cell
  integer :: map(1) ! really hacky but in the real code this could be
                    ! allocatable, depending on what the mesh read in 
                    ! and it won't be done in this routine.

  ! this routine explicitly populates the dof map for a v3 space on a 
  ! bi-periodic plane  with quads at lowest order
  
  ! 1st cell
  map(1) = 1
  do cell = 1, v3space%get_ncell()
     call v3space%populate_cell_dofmap(cell,map)
     map(1) = map(1) + num_layers
  end do

end subroutine dummy_read_dofmap
  
