!-----------------------------------------------------------------------------
! Copyright (c) 2017,  Met Office, on behalf of HMSO and Queen's Printer
! For further details please refer to the file LICENCE.original which you
! should have received as part of this distribution.
!-----------------------------------------------------------------------------
! LICENCE.original is available from the Met Office Science Repository Service:
! https://code.metoffice.gov.uk/trac/lfric/browser/LFRic/trunk/LICENCE.original
!-------------------------------------------------------------------------------
! BSD 3-Clause License
!
! Modifications copyright (c) 2017-2021, Science and Technology Facilities
! Council
! All rights reserved.
!
! Redistribution and use in source and binary forms, with or without
! modification, are permitted provided that the following conditions are met:
!
! * Redistributions of source code must retain the above copyright notice, this
!   list of conditions and the following disclaimer.
!
! * Redistributions in binary form must reproduce the above copyright notice,
!   this list of conditions and the following disclaimer in the documentation
!   and/or other materials provided with the distribution.
!
! * Neither the name of the copyright holder nor the names of its
!   contributors may be used to endorse or promote products derived from
!   this software without specific prior written permission.
!
! THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
! AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
! IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
! DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
! FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
! DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
! SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
! CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
! OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
! OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
! -----------------------------------------------------------------------------
! Modified by: J. Henrichs, Bureau of Meteorology,
!              I. Kavcic, Met Office

!> @brief A module providing field related classes.
!>
!> @details Both a representation of a field which provides no access to the
!> underlying data (to be used in the algorithm layer) and an accessor class
!> (to be used in the Psy layer) are provided.


module field_mod

  use constants_mod,      only: r_def, r_double, i_def, i_halo_index, l_def, &
                                str_def, real_type
  use function_space_mod, only: function_space_type
  use mesh_mod,           only: mesh_type

  use field_parent_mod,   only: field_parent_type, &
                                field_parent_proxy_type, &
                                write_interface, read_interface, &
                                checkpoint_write_interface, &
                                checkpoint_read_interface
  use pure_abstract_field_mod, &
                          only: pure_abstract_field_type

  implicit none

  private

! Public types

!______field_type_____________________________________________________________

  !> Algorithm layer representation of a field.
  !>
  !> Objects of this type hold all the data of the field privately.
  !> Unpacking the data is done via the proxy type accessed by the Psy layer
  !> alone.
  !>
  type, extends(field_parent_type), public :: field_type
    private

    !> The floating point values of the field
    real(kind=r_def), allocatable :: data( : )

    ! IO interface procedure pointers

    procedure(write_interface), nopass, pointer            :: write_method => null()
    procedure(read_interface), nopass, pointer             :: read_method => null()
    procedure(checkpoint_write_interface), nopass, pointer :: checkpoint_write_method => null()
    procedure(checkpoint_read_interface), nopass, pointer  :: checkpoint_read_method => null()

  contains
    !> Initialiser for a field. May only be called once.
    procedure, public :: initialise => field_initialiser

    ! Routine to return a deep copy of a field including all its data
    procedure, public :: copy_field

    ! Routine to return a deep, but empty copy of a field
    procedure, public :: copy_field_properties

    !> Function to get a proxy with public pointers to the data in a
    !! field_type.
    procedure, public :: get_proxy

    ! Logging procedures
    procedure, public :: log_field
    procedure, public :: log_dofs
    procedure, public :: log_minmax
    procedure, public :: log_absmax

    !> Setter for the field write method
    procedure, public :: set_write_behaviour

    !> Getter for the field write method
    procedure, public :: get_write_behaviour

    !> Setter for the read method
    procedure, public :: set_read_behaviour

    !> Getter for the read method
    procedure, public :: get_read_behaviour

    !> Setter for the checkpoint method
    procedure, public :: set_checkpoint_write_behaviour

    !> Setter for the restart method
    procedure, public :: set_checkpoint_read_behaviour

    !> Routine to return whether field can be checkpointed
    procedure, public :: can_checkpoint

    !> Routine to return whether field can be written
    procedure, public :: can_write

    !> Routine to return whether field can be read
    procedure, public :: can_read

    !> Routine to write field
    procedure         :: write_field

    !> Routine to read field
    procedure         :: read_field

    !> Routine to read a checkpoint netCDF file
    procedure         :: read_checkpoint

    !> Routine to write a checkpoint netCDF file
    procedure         :: write_checkpoint

    !> Overloaded assigment operator
    procedure         :: field_type_assign

    !> Routine to destroy field_type
    procedure         :: field_final

    !> Finalizers for scalar and arrays of field_type objects
    final             :: field_destructor_scalar, &
                         field_destructor_array1d, &
                         field_destructor_array2d

    !> Override default assignment for field_type pairs.
    generic           :: assignment(=) => field_type_assign

  end type field_type

!______field_pointer_type_______________________________________________________

!> a class to hold a pointer to a field in an object that is a child of
!> the pure abstract field class

  type, extends(pure_abstract_field_type), public :: field_pointer_type
    !> A pointer to a field
    type(field_type), pointer, public :: field_ptr
  contains
    !> Initialiser for a field pointer. May only be called once.
    procedure, public :: field_pointer_initialiser
    !> Finaliser for a field pointer object
    final :: field_pointer_destructor
  end type field_pointer_type

!______field_proxy_type_______________________________________________________

  !> Psy layer representation of a field.
  !>
  !> This is an accessor class that allows access to the actual field
  !> information with each element accessed via a public pointer.
  !>
  type, extends(field_parent_proxy_type), public :: field_proxy_type

    private

    !> Allocatable array of type real which holds the values of the field
    real(kind=r_def), public, pointer :: data( : ) => null()
    !> Unique identifier used to identify a halo exchange, so the start of an
    !> asynchronous halo exchange can be matched with the end
    integer(kind=i_def) :: halo_request

  contains

    !> Performs a blocking halo exchange operation on the field.
    !> @todo This is temporarily required by PSyclone for initial development
    !! Eventually, the PSy layer will call the asynchronous versions of
    !! halo_exchange and this function should be removed.
    !! @param[in] depth The depth to which the halos should be exchanged
    procedure, public :: halo_exchange
    !> Starts a halo exchange operation on the field. The halo exchange
    !> is non-blocking, so this call only starts the process. On Return
    !> from this call, outbound data will have been transferred, but no
    !> guarantees are made for in-bound data elements at this stage.
    !! @param[in] depth The depth to which the halos should be exchanged
    procedure, public :: halo_exchange_start

    !> Wait (i.e. block) until the transfer of data in a halo exchange
    !> (started by a call to halo_exchange_start) has completed.
    !! @param[in] depth The depth to which the halos have been exchanged
    procedure, public :: halo_exchange_finish

    !> Perform a global sum operation on the field
    !> @return The global sum of the field values over all ranks
    procedure, public :: get_sum

    !> Calculate the global minimum of the field
    !> @return The minimum of the field values over all ranks
    procedure, public :: get_min

    !> Calculate the global maximum of the field
    !> @return The maximum of the field values over all ranks
    procedure, public :: get_max

    !> Wait (i.e. block) until all current non-blocking reductions
    !> (sum, max, min) are complete.
    !>
    !> We presently have only blocking reductions, so this
    !> subroutine currently returns without waiting.
    procedure, public :: reduction_finish

  end type field_proxy_type

!______end of type declarations_______________________________________________

contains

!______field_type_procedures____________________________________________________

  !> Function to create a proxy with access to the data in the field_type.
  !>
  !> @return The proxy type with public pointers to the elements of
  !> field_type
  type(field_proxy_type ) function get_proxy(self)
    implicit none
    class(field_type), target, intent(in)  :: self

    ! Call the routine that initialises the proxy for data held in the parent
    call self%field_parent_proxy_initialiser(get_proxy)

    get_proxy%data   => self%data

  end function get_proxy

  !> Initialise a <code>field_type</code> object.
  !>
  !> @param [in] vector_space the function space that the field lives on
  !> @param [in] name The name of the field. 'none' is a reserved name
  !> @param [in] ndata_first Whether mutlidata fields have data ordered by
  !>                         the multidata dimension first
  !> @param [in] advection_flag Whether the field is to be advected
  !>
  subroutine field_initialiser(self, &
                               vector_space, &
                               name, &
                               ndata_first, &
                               advection_flag)

    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR
    implicit none

    class(field_type), intent(inout)               :: self
    type(function_space_type), pointer, intent(in) :: vector_space
    character(*), optional, intent(in)             :: name
    logical,      optional, intent(in)             :: ndata_first
    logical,      optional, intent(in)             :: advection_flag

    ! If there's already data in the field, destruct it
    ! ready for re-initialisation
    if(allocated(self%data))call field_destructor_scalar(self)

    call self%field_parent_initialiser(vector_space, &
                                       name=name, &
                                       fortran_type=real_type, &
                                       fortran_kind=r_def, &
                                       ndata_first=ndata_first, &
                                       advection_flag=advection_flag)

    ! Create space for holding field data
    allocate( self%data(self%vspace%get_last_dof_halo()) )

  end subroutine field_initialiser

  !> Initialise a field pointer
  !>
  !> @param [in] field_ptr A pointer to the field that is to be
  !>                       stored as a reference
  subroutine field_pointer_initialiser(self, field_ptr)
    implicit none
    class(field_pointer_type) :: self
    type(field_type), pointer :: field_ptr
    self%field_ptr => field_ptr
  end subroutine field_pointer_initialiser

  ! Finaliser for a field pointer
  !
  ! The following finaliser doesn't do anything. Without it, the Gnu compiler
  ! tries to create its own, but only ends up producing an Internal Compiler
  ! Error, so it is included here to prevent that.
  subroutine field_pointer_destructor(self)
    implicit none
    type(field_pointer_type), intent(inout) :: self
  end subroutine field_pointer_destructor

  !> Create a new field that inherits the properties of the source field and
  !> has a copy of all the field data from the source field.
  !>
  !> @param[out] dest   field object into which the copy will be made
  !> @param[in]  name   An optional argument that provides an identifying name
  subroutine copy_field(self, dest, name)

    implicit none
    class(field_type), target, intent(in)  :: self
    class(field_type), target, intent(out) :: dest
    character(*), optional, intent(in)     :: name

    if (present(name)) then
      call self%copy_field_properties(dest, name)
    else
      call self%copy_field_properties(dest)
    end if

    dest%data(:) = self%data(:)
    call self%copy_field_parent(dest)

  end subroutine copy_field

  !> Create a new empty field that inherits the properties of the source field.
  !>
  !> @param[out] dest   field object into which the copy will be made
  !> @param[in]  name   An optional argument that provides an identifying name
  subroutine copy_field_properties(self, dest, name)
    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR
    implicit none
    class(field_type), target, intent(in)  :: self
    class(field_type), target, intent(out) :: dest
    character(*), optional, intent(in)     :: name

    if (present(name)) then
      call dest%initialise(self%vspace, name, self%is_advected())
    else
      call dest%initialise( self%vspace, self%get_name(), self%is_advected() )
    end if

    dest%write_method => self%write_method
    dest%read_method => self%read_method
    dest%checkpoint_write_method => self%checkpoint_write_method
    dest%checkpoint_read_method => self%checkpoint_read_method

  end subroutine copy_field_properties

  !> DEPRECATED: Assignment operator between field_type pairs. Currently, this
  !> routine generates a (hopefully) useful message, then performs a double
  !> allocate to force an error stack trace (which should be useful to the
  !> developer - tells them where they have called the deprecated routine from).
  !>
  !> @param[out] dest   field_type lhs
  !> @param[in]  source field_type rhs
  subroutine field_type_assign(dest, source)

    use log_mod,         only : log_event, &
                                log_scratch_space, &
                                LOG_LEVEL_INFO
    implicit none
    class(field_type), intent(in)  :: source
    class(field_type), intent(out) :: dest

    write(log_scratch_space,'(A,A)')&
              '"field2=field1" syntax no longer supported. '// &
              'Use "call field1%copy_field(field2)". Field: ', &
              source%name
    call log_event(log_scratch_space,LOG_LEVEL_INFO )
    allocate(dest%data(1))   ! allocate the same memory twice, to force
    allocate(dest%data(2))   ! an error and generate a stack trace

  end subroutine field_type_assign

  !> Destroy a scalar field_type instance.
  subroutine field_final(self)

    use log_mod, only : log_event, LOG_LEVEL_ERROR

    implicit none

    class(field_type), intent(inout)    :: self

    call self%field_parent_final()

    if(allocated(self%data)) then
      deallocate(self%data)
    end if

    nullify( self%vspace,                   &
             self%write_method,             &
             self%read_method,              &
             self%checkpoint_write_method,  &
             self%checkpoint_read_method )

  end subroutine field_final

  !> Finalizer for a scalar <code>field_type</code> instance.
  subroutine field_destructor_scalar(self)

    implicit none

    type(field_type), intent(inout)    :: self

    call self%field_final()

  end subroutine field_destructor_scalar

  !> Finalizer for a 1d array of <code>field_type</code> instances.
  subroutine field_destructor_array1d(self)

    implicit none

    type(field_type), intent(inout)    :: self(:)
    integer(i_def) :: i

    do i=lbound(self,1), ubound(self,1)
      call self(i)%field_final()
    end do

  end subroutine field_destructor_array1d

  !> Finalizer for a 2d array of <code>field_type</code> instances.
  subroutine field_destructor_array2d(self)

    implicit none

    type(field_type), intent(inout)    :: self(:,:)
    integer(i_def) :: i,j

    do i=lbound(self,1), ubound(self,1)
      do j=lbound(self,2), ubound(self,2)
        call self(i,j)%field_final()
      end do
    end do

  end subroutine field_destructor_array2d

  !> Setter for field write behaviour
  !> @param[in,out]  self  field_type
  !> @param [in] write_behaviour - pointer to procedure implementing write method
  subroutine set_write_behaviour(self, write_behaviour)
    implicit none
    class(field_type), intent(inout)                  :: self
    procedure(write_interface), pointer, intent(in) :: write_behaviour
    self%write_method => write_behaviour
  end subroutine set_write_behaviour

  !> Getter to get pointer to field write behaviour
  !> @param[in]  self  field_type
  !> @param [in] write_behaviour -
  !>             pointer to procedure implementing write method
  !> @return pointer to procedure for field write behaviour
  subroutine get_write_behaviour(self, write_behaviour)

    implicit none

    class(field_type), intent(in) :: self
    procedure(write_interface), pointer, intent(inout) :: write_behaviour

    write_behaviour => self%write_method

    return
  end subroutine get_write_behaviour

  !> Setter for read behaviour
  !> @param [in] read_behaviour - pointer to procedure implementing read method
  subroutine set_read_behaviour(self, read_behaviour)
    implicit none
    class(field_type), intent(inout)               :: self
    procedure(read_interface), pointer, intent(in) :: read_behaviour
    self%read_method => read_behaviour
  end subroutine set_read_behaviour

  !> Getter to get pointer to read behaviour
  !> @param[in,out] read_behaviour -
  !>                pointer to procedure implementing read method
  !> @return pointer to procedure for read behaviour
  subroutine get_read_behaviour(self, read_behaviour)

    implicit none

    class(field_type), intent(in) :: self
    procedure(read_interface), pointer, intent(inout) :: read_behaviour

    read_behaviour => self%read_method

    return
  end subroutine get_read_behaviour


  !> Setter for checkpoint write behaviour
  !>
  !> @param [in] checkpoint_write_behaviour -
  !>             pointer to procedure implementing checkpoint write method
  subroutine set_checkpoint_write_behaviour(self, checkpoint_write_behaviour)
    implicit none
    class(field_type), intent(inout)                  :: self
    procedure(checkpoint_write_interface), pointer, intent(in)   :: checkpoint_write_behaviour
    self%checkpoint_write_method => checkpoint_write_behaviour
  end subroutine set_checkpoint_write_behaviour

  !> Setter for checkpoint read behaviour
  !>
  !> @param [in] checkpoint_read_behaviour -
  !>             pointer to procedure implementing checkpoint read method
  subroutine set_checkpoint_read_behaviour(self, checkpoint_read_behaviour)
    implicit none
    class(field_type), intent(inout)                  :: self
    procedure(checkpoint_read_interface), pointer, intent(in)   :: checkpoint_read_behaviour
    self%checkpoint_read_method => checkpoint_read_behaviour
  end subroutine set_checkpoint_read_behaviour

  !> Returns whether field can be checkpointed
  !>
  !> @return .true. or .false.
  function can_checkpoint(self) result(checkpointable)

    implicit none

    class(field_type), intent(in) :: self
    logical(l_def) :: checkpointable

    if (associated(self%checkpoint_write_method) .and. &
       associated(self%checkpoint_read_method)) then
      checkpointable = .true.
    else
      checkpointable = .false.
    end if

  end function can_checkpoint

  !> Returns whether field can be written
  !>
  !> @return .true. or .false.
  function can_write(self) result(writeable)

    implicit none

    class(field_type), intent(in) :: self
    logical(l_def) :: writeable

    writeable = associated(self%write_method)

  end function can_write

  !> Returns whether field can be read
  !>
  !> @return .true. or .false.
  function can_read(self) result(readable)

    implicit none

    class(field_type), intent(in) :: self
    logical(l_def) :: readable

    readable = associated(self%read_method)

  end function can_read

  !---------------------------------------------------------------------------
  ! Contained functions/subroutines
  !---------------------------------------------------------------------------


  !> Sends field contents to the log.
  !!
  !! @param[in] dump_level The level to use when sending the dump to the log.
  !! @param[in] label A title added to the log before the data is written out
  !>
  subroutine log_field( self, dump_level, label )

    use constants_mod, only : r_double, i_def
    use log_mod, only : log_event,         &
                        log_scratch_space, &
                        log_level,         &
                        LOG_LEVEL_INFO,    &
                        LOG_LEVEL_TRACE

    implicit none

    class( field_type ), target, intent(in) :: self
    integer(i_def),              intent(in) :: dump_level
    character( * ),              intent(in) :: label

    integer(i_def)          :: cell
    integer(i_def)          :: layer
    integer(i_def)          :: df
    integer(i_def), pointer :: map(:) => null()

    ! If we are not going to write the field to the log then do
    ! not write the field to the scratch space.
    if ( dump_level < log_level() ) return

    write( log_scratch_space, '( A, A)' ) trim( label ), " =["
    call log_event( log_scratch_space, dump_level )

    do cell=1,self%vspace%get_ncell()
      map => self%vspace%get_cell_dofmap( cell )
      do df=1,self%vspace%get_ndf()
        do layer=0,self%vspace%get_nlayers()-1
          write( log_scratch_space, '( I6, I6, I6, E16.8 )' ) &
              cell, df, layer+1, self%data( map( df ) + layer )
          call log_event( log_scratch_space, dump_level )
        end do
      end do
    end do

    call log_event( '];', dump_level )
    return

  end subroutine log_field

  !> Sends the field contents to the log
  !!
  !! @param[in] log_level The level to use for logging.
  !! @param[in] label A title added to the log before the data is written out
  !!
  subroutine log_dofs( self, log_level, label )

    use log_mod, only : log_event, log_scratch_space, LOG_LEVEL_INFO

    implicit none

    class( field_type ), target, intent(in) :: self
    integer(i_def),              intent(in) :: log_level
    character( * ),              intent(in) :: label

    integer(i_def) :: df

    call log_event( label, log_level )

    do df=1,self%vspace%get_undf()
      write( log_scratch_space, '( I6, E16.8 )' ) df,self%data( df )
      call log_event( log_scratch_space, log_level )
    end do

  end subroutine log_dofs

  !> Sends the min/max of a field to the log
  !!
  !! @param[in] log_level The level to use for logging.
  !! @param[in] label A title added to the log before the data is written out
  !!
  subroutine log_minmax( self, log_level, label )

    use log_mod,    only : log_event, log_scratch_space,     &
                           application_log_level => log_level
    use scalar_mod, only : scalar_type
    implicit none

    class( field_type ), target, intent(in) :: self
    integer(i_def),              intent(in) :: log_level
    character( * ),              intent(in) :: label
    integer(i_def)                          :: undf
    type(scalar_type)                       :: fmin, fmax

    ! If we aren't going to log the min and max then we don't need to
    ! do any further work here.
    if ( log_level < application_log_level() ) return

    undf = self%vspace%get_last_dof_owned()
    fmin = scalar_type( minval( self%data(1:undf) ) )
    fmax = scalar_type( maxval( self%data(1:undf) ) )

    write( log_scratch_space, '( A, A, A, 2E16.8 )' ) &
         "Min/max ", trim( label ),                   &
    ! Functions get_min() and get_max() rely on MPI comms so
    ! these calls are disabled here. Min and max are simply
    ! values of fmin and fmax scalars.
    !     " = ", fmin%get_min(), fmax%get_max()
         " = ", fmin%value, fmax%value
    call log_event( log_scratch_space, log_level )

  end subroutine log_minmax

  !> Sends the max of the absolute value of field to the log
  !!
  !! @param[in] log_level The level to use for logging.
  !! @param[in] label A title added to the log before the data is written out.
  !!
  subroutine log_absmax( self, log_level, label )

    use log_mod,    only : log_event, log_scratch_space,     &
                           application_log_level => log_level
    use scalar_mod, only : scalar_type
    implicit none

    class( field_type ), target, intent(in) :: self
    integer(i_def),              intent(in) :: log_level
    character( * ),              intent(in) :: label
    integer(i_def)                          :: undf
    type(scalar_type)                       :: fmax

    ! If we aren't going to log the abs max then we don't need to
    ! do any further work here.
    if ( log_level < application_log_level() ) return

    undf = self%vspace%get_last_dof_owned()
    fmax = scalar_type( maxval( abs(self%data(1:undf)) ) )

    write( log_scratch_space, '( A, A, E16.8 )' ) &
    ! Function get_max() relies on MPI comms so this call is
    ! disabled here. Max is simply the values of fmax scalar.
    !     trim( label ), " = ", fmax%get_max()
         trim( label ), " = ", fmax%value
    call log_event( log_scratch_space, log_level )

  end subroutine log_absmax

  !> Calls the underlying IO implementation for writing a field
  !> throws an error if this has not been set
  !> @param [in] field_name - field name / id to write
  subroutine write_field(this, field_name)

    use log_mod,           only : log_event, &
                                  LOG_LEVEL_ERROR

    implicit none

    class(field_type),   intent(in)     :: this
    character(len=*),    intent(in)     :: field_name

    if (associated(this%write_method)) then

      call this%write_method(trim(field_name), this%get_proxy())

    else

      call log_event( 'Error trying to write field '// trim(field_name) // &
                      ', write_method not set up', LOG_LEVEL_ERROR )
    end if

  end subroutine write_field

  !> Calls the underlying IO implementation for reading into the field
  !> throws an error if this has not been set
  !> @param [in] field_name - field name / id to read
  subroutine read_field( self, field_name)
    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR, &
                                LOG_LEVEL_INFO

    implicit none

    class( field_type ),  target, intent( inout ) :: self
    character(len=*),     intent(in)              :: field_name


    type( field_proxy_type )                      :: tmp_proxy

    if (associated(self%read_method)) then

      tmp_proxy = self%get_proxy()

      call self%read_method(trim(field_name), tmp_proxy)

      ! Set halos dirty here as for parallel read we only read in data for owned
      ! dofs and the halos will not be set

      call tmp_proxy%set_dirty()

    else

      call log_event( 'Error trying to read into field '// trim(field_name) // &
                      ', read_method not set up', LOG_LEVEL_ERROR )
    end if

  end subroutine read_field

  !> Reads a checkpoint file into the field
  !> @param [in] field_name - field name / id to read
  !> @param [in] file_name - file name to read from
  subroutine read_checkpoint( self, field_name, file_name)
    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR

    implicit none

    class( field_type ),  target, intent( inout ) :: self
    character(len=*),     intent(in)              :: field_name
    character(len=*),     intent(in)              :: file_name


    type( field_proxy_type )                      :: tmp_proxy


    if (associated(self%checkpoint_read_method)) then

      tmp_proxy = self%get_proxy()

      call self%checkpoint_read_method(trim(field_name), trim(file_name), tmp_proxy)

      ! Set halos dirty here as for parallel read we only read in data for owned
      ! dofs and the halos will not be set

      call tmp_proxy%set_dirty()

    else

      call log_event( 'Error trying to read checkpoint for field '// trim(field_name) // &
                      ', checkpoint_read_method not set up', LOG_LEVEL_ERROR )
    end if

  end subroutine read_checkpoint

  !> Writes a checkpoint file
  !> @param [in] field_name - field name / id to write
  !> @param [in] file_name - file name to write to
  subroutine write_checkpoint( self, field_name, file_name )
    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR


    implicit none

    class( field_type ),  target, intent( inout ) :: self
    character(len=*),     intent(in)              :: field_name
    character(len=*),     intent(in)              :: file_name

    if (associated(self%checkpoint_write_method)) then

      call self%checkpoint_write_method(trim(field_name), trim(file_name), self%get_proxy())

    else

      call log_event( 'Error trying to write checkpoint for field '// trim(field_name) // &
                      ', checkpoint_write_method not set up', LOG_LEVEL_ERROR )
    end if

  end subroutine write_checkpoint


  !! Perform a blocking halo exchange operation on the field
  !!
  subroutine halo_exchange( self, depth )

    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR
    use count_mod,       only : halo_calls
    implicit none

    class( field_proxy_type ), target, intent(inout) :: self
    integer(i_def), intent(in) :: depth

    if ( self%vspace%is_writable() ) then
      if ( depth > self%max_halo_depth() ) &
        call log_event( 'Error in field: '// &
                        'attempt to exchange halos with depth out of range.', &
                        LOG_LEVEL_ERROR )

      ! Halo exchange is complete so set the halo dirty flag to say it
      ! is clean (or more accurately - not dirty)
      self%halo_dirty(1:depth) = 0
      ! If a halo counter has been set up, increment it
      if (allocated(halo_calls)) call halo_calls%counter_inc()
    else
      call log_event( 'Error in field: '// &
        'attempt to exchange halos (a write operation) on a read-only field.', &
         LOG_LEVEL_ERROR )
    end if

  end subroutine halo_exchange

  !! Start a halo exchange operation on the field
  !!
  subroutine halo_exchange_start( self, depth )

    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR
    implicit none

    class( field_proxy_type ), target, intent(inout) :: self
    integer(i_def), intent(in) :: depth

    if ( self%vspace%is_writable() ) then
      if ( depth > self%max_halo_depth() ) &
        call log_event( 'Error in field: '// &
                        'attempt to exchange halos with depth out of range.', &
                        LOG_LEVEL_ERROR )
    else
      call log_event( 'Error in field: '// &
        'attempt to exchange halos (a write operation) on a read-only field.', &
         LOG_LEVEL_ERROR )
    end if

  end subroutine halo_exchange_start

  !! Wait for a halo exchange to complete
  !!
  subroutine halo_exchange_finish( self, depth )

    use log_mod,         only : log_event, &
                                LOG_LEVEL_ERROR
    use count_mod,       only : halo_calls
    implicit none

    class( field_proxy_type ), target, intent(inout) :: self
    integer(i_def), intent(in) :: depth

    if ( self%vspace%is_writable() ) then
      if ( depth > self%max_halo_depth() ) &
        call log_event( 'Error in field: '// &
                        'attempt to exchange halos with depth out of range.', &
                        LOG_LEVEL_ERROR )

      ! Halo exchange is complete so set the halo dirty flag to say it
      ! is clean (or more accurately - not dirty)
      self%halo_dirty(1:depth) = 0
      ! If a halo counter has been set up, increment it
      if (allocated(halo_calls)) call halo_calls%counter_inc()
    else
      call log_event( 'Error in field: '// &
        'attempt to exchange halos (a write operation) on a read-only field.', &
         LOG_LEVEL_ERROR )
    end if

  end subroutine halo_exchange_finish

  !! Start performing a global sum operation on the field
  !!
  function get_sum(self) result (answer)

    use mpi_mod, only: global_sum
    implicit none

    class(field_proxy_type), intent(in) :: self

    real(r_def) :: l_sum
    real(r_def) :: answer

    integer(i_def) :: i

    ! Generate local sum
    l_sum = 0.0_r_def
    do i = 1, self%vspace%get_last_dof_owned()
      l_sum = l_sum + self%data(i)
    end do

    call global_sum( l_sum, answer )
  end function get_sum

  !! Start the calculation of the global minimum of the field
  !!
  function get_min(self) result (answer)

    use mpi_mod, only: global_min
    implicit none

    class(field_proxy_type), intent(in) :: self

    real(r_def) :: l_min
    real(r_def) :: answer

    integer(i_def) :: i

    ! Generate local min
    l_min = self%data(1)
    do i = 2, self%vspace%get_last_dof_owned()
      if( self%data(i) < l_min ) l_min = self%data(i)
    end do

    call global_min( l_min, answer )

  end function get_min

  !! Start the calculation of the global maximum of the field
  !!
  function get_max(self) result (answer)

    use mpi_mod, only: global_max
    implicit none

    class(field_proxy_type), intent(in) :: self

    real(r_def) :: l_max
    real(r_def) :: answer

    integer(i_def) :: i

    ! Generate local max
    l_max = self%data(1)
    do i = 2, self%vspace%get_last_dof_owned()
      if( self%data(i) > l_max ) l_max = self%data(i)
    end do

    call global_max( l_max, answer )

  end function get_max

  !! Wait for any current (non-blocking) reductions (sum, max, min) to complete
  !!
  !! We presently have only blocking reductions, so there is
  !! no need to ever call this subroutine. It is left in here to complete the
  !! API so when non-blocking reductions are implemented, we can support them
  subroutine reduction_finish(self)

    implicit none

    class(field_proxy_type), intent(in) :: self

    logical(l_def) :: is_dirty_tmp

    is_dirty_tmp=self%is_dirty(1)    ! reduction_finish currently does nothing.
                                    ! The "self" that is passed in automatically
                                    ! to a type-bound subroutine is not used -
                                    ! so the compilers complain -  have to use
                                    ! it for something harmless.

  end subroutine reduction_finish

end module field_mod
