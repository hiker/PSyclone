!-----------------------------------------------------------------------------
! Copyright (c) 2017-2020,  Met Office, on behalf of HMSO and Queen's Printer
! For further details please refer to the file LICENCE.original which you
! should have received as part of this distribution.
!-----------------------------------------------------------------------------
! LICENCE.original is available from the Met Office Science Repository Service:
! https://code.metoffice.gov.uk/trac/lfric/browser/LFRic/trunk/LICENCE.original
!-----------------------------------------------------------------------------
!
!> @brief Define various constants for the application.
!>
!> @details Various computational, physical and geometrical constants are
!>          defined in this module. Their values are also set here.

module constants_mod

  use, intrinsic :: iso_fortran_env, only : int8, int16, int32, int64, &
                                            real32, real64, real128

  implicit none

  private

  public :: c_def, c_native,                                             &
            dp_native, dp_xios,                                          &
            i_byte, i_def, i_halo_index, i_long, i_medium, i_native,     &
            i_timestep, i_um,                                            &
            l_def, l_native,                                             &
            r_def, r_double, r_ncdf, r_native, r_second, r_single, r_um, &
            CMDI, EIMDI, EMDI, IMDI, RMDI,                               &
            real_type, integer_type, logical_type,                       &
            EPS, tiny_eps,                                               &
            str_def, str_long, str_max_filename, str_short,              &
            LARGE_REAL_NEGATIVE, LARGE_REAL_POSITIVE, xios_max_int,      &
            PI, degrees_to_radians, radians_to_degrees,                  &
            cache_block, PRECISION_REAL

  ! Define default application-defined kinds for all intrinsic data types

  !> @name Set up default kinds for real and double-precision variables.
  !> @{
  real               :: r_val              !< A native real used to compute kind of native real.
  double precision   :: dp_val             !< A native double-precision used to compute kind of native dp.

  ! Default real kind for application.
#if (RDEF_PRECISION == 32)
  integer,      parameter :: r_def = real32
  character(3), parameter :: PRECISION_REAL = '32'
#elif (RDEF_PRECISION == 128)
  integer,      parameter :: r_def = real128
  character(3), parameter :: PRECISION_REAL = '128'
#else
  integer,      parameter :: r_def = real64
  character(3), parameter :: PRECISION_REAL = '64'
#endif

  integer, parameter :: real_type    = 1 !< A parameter used to indicate a real data typa
  integer, parameter :: integer_type = 2 !< A parameter used to indicate an integer data type
  integer, parameter :: logical_type = 3 !< A parameter used to indicate a logical data type

  integer, parameter :: r_double = real64 !< Default double precision real kind for application.
  integer, parameter :: r_native = kind(r_val)  !< Native kind for real.
  integer, parameter :: r_ncdf   = real64 !< Default real kind used in netcdf get and put.
  integer, parameter :: r_quad   =  real128 !< Default quad precision real kind for application.
  integer, parameter :: r_second = real64 !< Kind for second counts.
  integer, parameter :: r_single = real32 !< Default single precision real kind for application.
  integer, parameter :: r_um     = real64 !< Default real kind used by the UM.

  integer, parameter :: dp_native = kind(dp_val) !< Native kind for double precision.
  ! Define kinds specifically for IO
  integer, parameter :: dp_xios = kind(dp_val) !< XIOS kind for double precision fields

  !> @}

  !> @name Complex
  !> @{
  !> @}

  !> @name Set up default kinds for integers.
  !> @{
  integer            :: i_val                      !< A native integer used to compute kind of native integer.

  integer, parameter :: i_byte       = int8        !< Explicit byte integer.
  integer, parameter :: i_def        = int32       !< Default integer kind for application.
  integer, parameter :: i_halo_index = int64       !< Integer kind for the index used in halo swapping
  integer, parameter :: i_long       = int64       !< Explicit long integer.
  integer, parameter :: i_medium     = int32       !< Explicit midsize integer.
  integer, parameter :: i_native     = kind(i_val) !< Native kind for integer.
  integer, parameter :: i_short      = int16       !< Explicit short integer.
  integer, parameter :: i_timestep   = int32       !< Kind for timestep counts.
  integer, parameter :: i_um         = int32       !< Default integer kind used by the UM.
  !> @}

  !> @name Set up default kinds for logicals.
  !> @{
  logical            :: l_val                   !< A native logical used to compute kind of native logical.

  integer, parameter :: l_def     = kind(l_val) !< Default logical kind for application.
  integer, parameter :: l_native  = kind(l_val) !< Native kind for logical.
  !> @}

  !> @name Set up default kinds for character variables.
  !> @{
  character          :: c_val                   !< A native character used to compute kind of native character.

  integer, parameter :: c_def     = kind(c_val) !< Default character kind for application.
  integer, parameter :: c_native  = kind(c_val) !< Native kind for character.
  !> @}

  !> @name Set up default lengths for string variables.
  !> @{
  integer, parameter :: str_short        = 16  !< Length of "short" strings.
  integer, parameter :: str_def          = 128 !< Default string length for normal strings.
  integer, parameter :: str_long         = 255 !< Default length of long string.
  integer, parameter :: str_max_filename = 512 !< Default maximum length of a file-name.
  !> @}

  !> @name Platform constants
  !> @{
  real(kind=r_def), parameter :: LARGE_REAL_POSITIVE = huge(0.0_r_def) !< The largest
  !<                            positive number of kind r_def that is not an infinity.
  real(kind=r_def), parameter :: LARGE_REAL_NEGATIVE = -LARGE_REAL_POSITIVE !< The largest
  !<                            negative number of kind r_def that is not an infinity.
  integer(kind=i_def), parameter :: xios_max_int = huge(0_i_short) !< The largest
  !<                            integer that can be output by XIOS
  integer, parameter :: cache_block = 256 !< Size of a cache block, for padding
  !<                           arrays to ensure access to different cache lines

  !> @}

  !> @name Numerical constants
  !> @{
  real(kind=r_def), parameter :: EPS = 3.0e-15_r_def      !< Relative precision: if (abs(x-y) > EPS) then assume x==y.
  real(kind=r_def), parameter :: tiny_eps = 1.0e-30_r_def !< Similar to EPS but lot smaller, which can be used where
  !<                             x/y < EPS but (x-y) is not considered to be zero like many chemistry tracers.
  !> @}

  !> @name Mathematical constants
  !> @{
  real(kind=r_def), parameter :: PI  = 4.0_r_def*atan(1.0_r_def) !< Value of pi.
  !> @}

  !> @name Conversion factors
  !> @{
  real(r_def), parameter :: degrees_to_radians = PI / 180.0_r_def
  real(r_def), parameter :: radians_to_degrees = 180.0_r_def / PI

  !> @}
  ! Missing data indicators
  real     (r_def),     parameter :: RMDI  = -huge(0.0_r_def)     !< Value for real numbers
  integer  (i_def),     parameter :: IMDI  = -huge(0_i_def)       !< Value for integer numbers
  character(str_short), parameter :: CMDI  = 'unset'              !< Value for characters
  character(str_short), parameter :: EMDI  = 'missing data'       !< Chararater value for namelist enumerations
  integer  (i_native),  parameter :: EIMDI = int(IMDI, i_native)  !< Integer value for namelist enumerations
  !> @}

end module constants_mod

