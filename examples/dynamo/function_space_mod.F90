!-------------------------------------------------------------------------------
! (c) The copyright relating to this work is owned jointly by the Crown, 
! Met Office and NERC 2014. 
! However, it has been created with the help of the GungHo Consortium, 
! whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
!-------------------------------------------------------------------------------
!
!-------------------------------------------------------------------------------
module function_space_mod
implicit none
private

!-------------------------------------------------------------------------------
! Public types
!-------------------------------------------------------------------------------
  
type, public :: function_space_type
  private
  integer              :: ndf, ncell, undf
  integer, allocatable :: dofmap(:,:)
  ! accessor functions go here
contains
  !final :: destructor
  procedure :: get_undf
  procedure :: populate_cell_dofmap
  procedure :: get_ncell
  procedure :: get_cell_dofmap

end type function_space_type

!-------------------------------------------------------------------------------
! Constructors
!-------------------------------------------------------------------------------

! overload the default structure constructor for function space
interface function_space_type
   module procedure constructor
end interface

!-------------------------------------------------------------------------------
! Contained functions/subroutines
!-------------------------------------------------------------------------------
public get_ncell, get_cell_dofmap
contains

type(function_space_type) function constructor(num_cells,num_dofs,num_unique_dofs) &
     result(self)
  !-----------------------------------------------------------------------------
  ! Constructor
  !-----------------------------------------------------------------------------

  !Arguments
  integer, intent(in) :: num_cells, num_dofs, num_unique_dofs

  self%ncell = num_cells
  self%ndf   = num_dofs
  self%undf  = num_unique_dofs
  
  ! allocate some space
  allocate(self%dofmap(num_cells,num_dofs))
  ! this would need populating 

  return
end function constructor

!subroutine destructor()
!  !-----------------------------------------------------------------------------
!  ! Destructor. Allocatables are handled by any F2003-compliant compiler
!  ! anyway.
!  !-----------------------------------------------------------------------------
!  implicit none
!
!  type(function_space_type) :: self
!
!  !deallocate( self%v3dofmap)
!  !deallocate( self%Rv3)
!
!  return
!end subroutine final_lfric

integer function get_undf(self)
  class(function_space_type) :: self
  get_undf=self%undf
  return
end function get_undf

subroutine populate_cell_dofmap(self,cell,map)
  implicit none
  class(function_space_type), intent(inout) :: self
  integer, intent(in) :: cell
  integer, intent(in) :: map(self%ndf)

  integer :: dof

  do dof = 1,self%ndf
     self%dofmap(cell,dof) = map(dof)
!     write(*,'("function_space_type:populate_cell_dofmap:cell=",I2,":df=",I2,":",I2)') cell,dof,map(dof)
  end do
  return 
end subroutine populate_cell_dofmap

integer function get_ncell(self)
  class(function_space_type) :: self
  get_ncell=self%ncell
  return
end function get_ncell

subroutine get_cell_dofmap(self,cell,map)
  implicit none
  class(function_space_type), intent(in) :: self
  integer, intent(in) :: cell
  integer, intent(out) :: map(self%ndf)

  map(:) = self%dofmap(cell,:)
  return
end subroutine get_cell_dofmap

end module function_space_mod
