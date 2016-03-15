.. _infrastructure-calls:

Infrastructure calls
====================

Infrastructure calls are calls which can be specified within an invoke
call in the algorithm layer but do not require an associated kernel to
be implemented as they are supported directly by the infrastructure.

One use of infrastructure calls is for commonly used operations. In
this case infrastructure calls simplify the use of the system as users
do not need to write kernel routines. Infrastructure routines also
offer a potential performance advantage as they provide a
specification of what is required without an implementation. Therefore
the PSy layer is free to implement these routines in whatever way it
chooses.

As infrastructure calls have no kernel implementation, they do not
need to specify a particular type of data (kernels specify the type of
data expected in their metadata description). Therefore infrastructure
calls may be polymorphic with respect to functionspaces (they may
support different functionspaces through the same api).

.. note:: In general, psyclone will need to know the types of fields being passed to the infrastructure calls. The parser obtains this information from an API-specifc file that contains the meta-data for all supported infrastructure calls.


Example
-------

In the following example the invoke call includes an infrastructure
call (``set``) and a kernel call (``testkern_type``). The
infrastructure call sets all values in the field ``one`` to
``1.0``. Notice that, unlike the kernel call, no use association is
required for the infrastructure call.
::

	use testkern, only: testkern_type
	use inf,      only: field_type
	implicit none
	type(field_type) :: one,f2,f3
	
	call invoke(                                          &
     	        set(one,1.0),                                 &
     	        testkern_type(one,f2,f3)                      &
                )

See the full :ref:`examples-infrastructure-label` example in the
:ref:`examples-label` section for more details.

Supported infrastructure calls
------------------------------

The list of supported infrastructure calls is API-specific and
therefore is described under the documentation of each API.

Adding support for additional infrastructure calls to a specific API
--------------------------------------------------------------------

 1. Identify the PSyclone source file for the API to be extended. e.g. for
    Dynamo 0.3 it is ``src/dynamo0p3.py``.
 2. Add the name of the new infrastructure call to the
    ``INTRINSIC_NAMES`` list in that source file.
 2. Add meta-data describing this call to the appropriate file specified in
    the ``INTRINSIC_DEFINITIONS_FILE`` in that source file. For dynamo0.3
    this is ``dynamo0p3_intrinsics_mod.f90``.
 3. Add a hook to create an object for this new call in the ``create()``
    method of the appropriate ``InfCallFactory``. For Dynamo0.3 this is
    ``dynamo0p3.DynInfCallFactory``.
 4. Create the class for this new call. It must inherit from the
    API-specific base class for infrastructure calls (``DynInfKern`` for
    Dynamo0.3).
 5. Implement ``__str__`` and ``gen_code()`` methods for this new class.

If the API being extended does not currently support any intrinsics
then the ``INTRINSIC_NAMES`` and
``INTRINSIC_DEFINITIONS_FILE`` module variables must be added to the
source file for the API.  A Fortran module file must be created in the
PSyclone src directory (with the name specified in
``INTRINSIC_DEFINITIONS_FILE``) containing meta-data describing the
intrinsic operations. Finally, ``parse.get_intrinsic_defs()`` must be
extended to import ``PSYCLONE_INTRINSIC_NAMES`` and
``INTRINSIC_DEFINITIONS_FILE`` for this API.
