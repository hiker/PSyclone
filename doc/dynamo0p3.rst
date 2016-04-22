.. _dynamo0.3-api:

dynamo0.3 API
=============

This section describes the dynamo0.3 application programming interface
(API). This API explains what a user needs to write in order to make
use of the dynamo0.3 API in PSyclone.

As with all PSyclone API's the dynamo0.3 API specifies how a user
needs to write the algorithm layer and the kernel layer to allow
PSyclone to generate the PSy layer. These algorithm and kernel API's
are discussed separately in the following sections.

.. _dynamo0.3-api-algorithm:

Algorithm
---------

.. note:: To be written.

.. fields and operators
.. vector of fields
.. quadrature rules

Kernel
-------

The general requirements for the structure of a Kernel are explained
in the :ref:`kernel-layer` section. This section explains the
dynamo0.3-specific metadata and subroutine arguments.

Metadata
++++++++

The code below outlines the elements of the dynamo0.3 API kernel
metadata, 1) 'meta_args', 2) 'meta_funcs', 3)
'iterates_over' and 4) 'procedure'.

::

  type, public, extends(kernel_type) :: my_kernel_type
    type(arg_type) :: meta_args(...) = (/ ... /)
    type(func_type) :: meta_funcs(...) = (/ ... /)
    integer :: iterates_over = cells
  contains
    procedure :: my_kernel_code
  end type

These 4 metadata elements are discussed in order in the following
sections.

.. _dynamo0.3-api-meta-args:

meta_args
#########

The ``meta_args`` array specifies information about data that the
kernel code expects to be passed to it via its argument list. There is
one entry in the ``meta_args`` array for each **scalar**, **field**,
or **operator** passed into the Kernel and the order that these occur
in the ``meta_args`` array must be the same as they are expected in
the kernel code argument list. The entry must be of ``arg_type`` which
itself contains metadata about the associated argument. The size of
the meta_args array must correspond to the number of **scalars**,
**fields** and **operators** passed into the Kernel.

.. note:: it makes no sense for a Kernel to have only **scalar** arguments (because the PSy layer will call a Kernel for each point in the spatial domain) and PSyclone will reject such Kernels.

For example, if there are a total of 2 **scalar** / **field** /
**operator** entities being passed to the Kernel then the meta_args
array will be of size 2 and there will be two ``arg_type`` entries:

::

  type(arg_type) :: meta_args(2) = (/                                  &
       arg_type( ... ),                                                &
       arg_type( ... )                                                 &
       /)

Argument-metadata (metadata contained within the brackets of an
``arg_type`` entry), describes either a **scalar**, a **field** or an
**operator**.

The first argument-metadata entry describes whether the data that is
being passed is for a real scalar (``GH_RSCALAR``), an integer scalar
(``GH_ISCALAR``), a field (``GH_FIELD``) or an operator
(``GH_OPERATOR``). This information is mandatory.

Additionally, argument-metadata can be used to describe a vector of
fields (see the :ref:`dynamo0.3-api-algorithm` section for more
details). If so, the size of the vector is specified using the
notation ``GH_FIELD*N``, where ``N`` is the size of the vector.

As an example, the following ``meta_args`` metadata describes 4
entries, the first is a real scalar, the next two are fields and the
fourth is an operator. The third entry is a field vector of size 3.

::

  type(arg_type) :: meta_args(4) = (/                                  &
       arg_type(GH_RSCALAR, ...),                                      &
       arg_type(GH_FIELD, ... ),                                       &
       arg_type(GH_FIELD*3, ... ),                                     &
       arg_type(GH_OPERATOR, ...)                                      &
       /)

The second entry to argument-metadata (information contained within
the brackets of an ``arg_type``) describes how the Kernel makes use of
the data being passed into it. There are 3 possible values of this
metadata ``GH_WRITE``, ``GH_READ`` and ``GH_INC``. ``GH_WRITE``
indicates the data is modified in the Kernel before (optionally) being
read. ``GH_READ`` indicates that the data is read and left
unmodified. ``GH_INC`` **explanation TBD**.

For example:

::

  type(arg_type) :: meta_args(4) = (/                                  &
       arg_type(GH_RSCALAR, GH_READ),                                  &
       arg_type(GH_FIELD, GH_INC, ... ),                               &
       arg_type(GH_FIELD*3, GH_WRITE, ... ),                           &
       arg_type(GH_OPERATOR, GH_READ, ...)                             &
       /)

For a scalar the argument metadata contains only these two entries.
However, fields and operators require further entries specifying
function-space information.
The meaning of these further entries differs depending on whether a
field or an operator is being described.

In the case of an operator, the 3rd and 4th arguments describe the
``to`` and ``from`` function spaces respectively. In the case of a
field the 3rd argument specifies the function space that the field
lives on. Supported function spaces are ``w0``, ``w1``, ``w2``, ``w3``,
``wtheta``, ``w2h`` and ``w2v``.

For example:

::

  type(arg_type) :: meta_args(3) = (/                                  &
       arg_type(GH_FIELD, GH_INC, W1),                                 &
       arg_type(GH_FIELD*3, GH_WRITE, W2H),                            &
       arg_type(GH_OPERATOR, GH_READ, W1, W2H)                         &
       /)

It may be that a Kernel is written such that a field and/or operators
may be on any function space. In this case the metadata should be
specified as being one of ``any_space_1``, ``any_space_2``, ...,
``any_space_9``. The reason for having different names is that a
Kernel might be written to allow 2 or more arguments to be able to support any
function space but for a particular call the function spaces may have
to be the same as each other.

In the example below, the first field entry supports any function space but
it must be the same as the operator's ``to`` function space. Similarly,
the second field entry supports any function space but it must be the same
as the operator's ``from`` function space. Note, the metadata does not
forbid ``ANY_SPACE_1`` and ``ANY_SPACE_2`` from being the same.

::

  type(arg_type) :: meta_args(3) = (/                                  &
       arg_type(GH_FIELD, GH_INC, ANY_SPACE_1 ),                       &
       arg_type(GH_FIELD*3, GH_WRITE, ANY_SPACE_2 ),                   &
       arg_type(GH_OPERATOR, GH_READ, ANY_SPACE_1, ANY_SPACE_2)        &
       /)

Finally, field metadata supports an optional 4th argument which
specifies that the field is accessed as a stencil operation within the
Kernel. Stencil metadata only makes sense if the associated field
is read within a Kernel i.e. it only makes sense to specify stencil
metadata if the first entry is ``GH_FIELD`` and the second entry is
``GH_READ``.

Stencil metadata is written in the following format:

::

  STENCIL(type,extent)

where ``type`` may be one of ``X1D``, ``Y1D``, ``CROSS`` or ``REGION``
and extent is an integer which specifies the maximum distance from the
central point that a stencil extends.

For example, the following stencil:

::

  | 4 | 2 | 1 | 3 | 5 |

would be declared as

::

  STENCIL(X1D,2)

the following stencil

::

  |   |   | 9 |   |   |
  |   |   | 5 |   |   |
  | 6 | 2 | 1 | 3 | 7 |
  |   |   | 4 |   |   |
  |   |   | 8 |   |   |

would be declared as

::

  STENCIL(CROSS,2)

and the following stencil (all adjacent cells)

::

  | 9 | 5 | 8 |
  | 2 | 1 | 3 |
  | 6 | 4 | 7 |

would be declared as

::

  STENCIL(REGION,1)

Below is an example of stencil information within the full kernel metadata.

::

  type(arg_type) :: meta_args(3) = (/                                  &
       arg_type(GH_FIELD, GH_INC, W1),                                 &
       arg_type(GH_FIELD, GH_READ, W2H, STENCIL(REGION,1)),            &
       arg_type(GH_OPERATOR, GH_READ, W1, W2H)                         &
       /)

meta_funcs
##########

.. note:: To be written.

iterates over
#############

The 3rd type of metadata provided is ``ITERATES_OVER``. This specifies
that the Kernel has been written with the assumption that it is
iterating over the specified entity. Currently this only has one valid
value which is ``CELLS``.

Procedure
#########

The 4th and final type of metadata is ``procedure`` metadata. This
specifies the name of the Kernel subroutine that this metadata
describes.

For example:

::

  procedure :: my_kernel_subroutine

Subroutine
++++++++++

.. _stub-generation-rules:

Rules
#####

Kernel arguments follow a set of rules which have been specified for
the dynamo0.3 API. These rules are encoded in the ``_create_arg_list()``
method within the ``DynKern`` class in the ``dynamo0p3.py`` file. The
rules, along with PSyclone's naming conventions, are:

1) If an operator is passed then include the ``cells`` argument. ``cells`` is an integer and has intent ``in``.
2) Include ``nlayers``, the number of layers in a column. ``nlayers`` is an integer and has intent ``in``.
3) For each scalar/field/vector_field/operator in the order specified by the meta_args metadata:

    1) if the current entry is a scalar quantity then include the Fortran variable in the argument list. The intent is determined from the metadata (see :ref:`dynamo0.3-api-meta-args` for an explanation).
    2) if the current entry is a field then include the field array. The field array name is currently specified as being ``"field_"<argument_position>"_"<field_function_space>``. A field array is a real array of type ``r_def`` and dimensioned as the unique degrees of freedom for the space that the field operates on. This value is passed in separately. Again, the intent is determined from the metadata (see :ref:`dynamo0.3-api-meta-args`).
    3) if the current entry is a field vector then for each dimension of the vector, include a field array. The field array name is specified as being using ``"field_"<argument_position>"_"<field_function_space>"_v"<vector_position>``. A field array in a field vector is declared in the same way as a field array (described in the previous step).
    4) if the current entry is an operator then first include a dimension size. This is an integer. The name of this size is ``<operator_name>"_ncell_3d"``. Next include the operator. This is a real array of type ``r_def`` and is 3 dimensional. The first two dimensions are the local degrees of freedom for the ``to`` and ``from`` function spaces respectively. The third dimension is the dimension size mentioned before. The name of the operator is ``"op_"<argument_position>``. Again the intent is determined from the metadata (see :ref:`dynamo0.3-api-meta-args`).

4) For each function space in the order they appear in the metadata arguments (the ``to`` function space of an operator is considered to be before the ``from`` function space of the same operator as it appears first in lexicographic order)

    1) Include the number of local degrees of freedom for the function space. This is an integer and has intent ``in``. The name of this argument is ``"ndf_"<field_function_space>``.
    2) If there is a field on this space

        1) Include the unique number of degrees of freedom for the function space. This is an integer and has intent ``in``. The name of this argument is ``"undf_"<field_function_space>``.
        2) Include the dofmap for this function space. This is an integer array with intent ``in``. It has one dimension sized by the local degrees of freedom for the function space.

    3) For each operation on the function space (``basis``, ``diff_basis``, ``orientation``) in the order specified in the metadata

        1) If it is a basis function, include the associated argument. This is a real array of kind r_def with intent ``in``. It has four dimensions. The first dimension is 1 or 3 depending on the function space (w0=1,w1=3,w2=3,w3=1,wtheta=1,w2h=3,w2v=3). The second dimension is the local degrees of freedom for the function space. The third argument is the quadrature rule size which is currently named ``nqp_h`` and the fourth argument is the quadrature rule size which is currently named ``nqp_v``.  The name of the argument is ``"basis_"<field_function_space>``
        2) If it is a differential basis function, include the associated argument. The sizes and dimensions are the same as the basis function except for the size of the first dimension which is sized as 1 or 3 depending on different function space rules (w0=3,w1=3,w2=1,w3=1,wtheta=3,w2h=1,w2v=1). The name of the argument is ``"diff_basis_"<field_function_space>``.
        3) If is an orientation array, include the associated argument. The argument is an integer array with intent ``in``. There is one dimension of size the local degrees of freedom for the function space. The name of the array is ``"orientation_"<field_function_space>``.

5) if Quadrature is required (this is the case if any of the function spaces require a basis or differential basis function)

    1) include ``nqp_h``. This is an integer scalar with intent ``in``.
    2) include ``nqp_v``. This is an integer scalar with intent ``in``.
    3) include ``wh``. This is a real array of kind r_def with intent ``in``. It has one dimension of size ``nqp_h``.
    4) include ``wv``. This is a real array of kind r_def with intent ``in``. It has one dimension of size ``nqp_v``.


Supported Built-ins
-------------------

The basic concept of a PSyclone Built-in is described in the
:ref:`built-ins` section.  In the Dynamo 0.3 API, calls to
built-ins generally follow a convention that the field/scalar written
to comes last in the argument list. Although field arguments to
built-ins may be on any space, the arguments to any given
call must all be on the same space.

The built-ins supported for the Dynamo 0.3 API are
described (in alphabetical order) below. For clarity, the calculation
performed by each built-in is described using Fortran array syntax; this
does not necessarily reflect the actual implementation of the
built-in (*e.g.* it could be implemented by PSyclone
generating a call to an optimised math library).

axpby
+++++

**axpby** (*a*, *field1*, *b*, *field2*, *field3*)

Performs: ::
   
   field3(:) = a*field1(:) + b*field2(:)

where:

* real(r_def), intent(in) :: *a*, *b*
* type(field_type), intent(in) :: *field1*, *field2*
* type(field_type), intent(out) :: *field3*

inc_axpby
+++++++++

**inc_axpby** (*a*, *field1*, *b*, *field2*)

Performs: ::
   
   field1(:) = a*field1(:) + b*field2(:)

where:

* real(r_def), intent(in) :: *a*, *b*
* type(field_type), intent(inout) :: *field1*
* type(field_type),    intent(in) :: *field2*

axpy
++++

**axpy** (*a*, *field1*, *field2*, *field3*)

Performs: ::
   
   field3(:) = a*field1(:) + field2(:)

where:

* real(r_def), intent(in) :: *a*
* type(field_type), intent(in) :: *field1*, *field2*
* type(field_type), intent(out) :: *field3*

inc_axpy
++++++++

**inc_axpy** (*a*, *field1*, *field2*)

Performs an AXPY and returns the result as an increment to the first
field: ::
   
   field1(:) = a*field1(:) + field2(:)

where:

* real(r_def), intent(in) :: *a*
* type(field_type), intent(inout) :: *field1*
* type(field_type),    intent(in) :: *field2*

copy_field
++++++++++

**copy_field** (*field1*, *field2*)

Copy the values from *field1* into *field2*: ::

   field2(:) = field1(:)

where:

* type(field_type), intent(in) :: *field1*
* type(field_type), intent(out) :: *field2*

copy_scaled_field
+++++++++++++++++

**copy_scaled_field** (*value*, *field1*, *field2*)

Multiplies a field by a scalar and stores the result in a second field: ::
  
  field2(:) = value * field1(:)

where:

* real(r_def), intent(in) :: *value*
* type(field_type), intent(in) :: *field1*
* type(field_type), intent(out) :: *field2*

divide_field
++++++++++++

**divide_field** (*field1*, *field2*)

Divides the first field by the second and returns it: ::

   field1(:) = field1(:) / field2(:)

where:

* type(field_type), intent(inout) :: *field1*
* type(field_type),    intent(in) :: *field2*

divide_fields
+++++++++++++

**divide_fields** (*field1*, *field2*, *field3*)

Divides the first field by the second and returns the result in the third: ::

   field3(:) = field1(:) / field2(:)

where:

* type(field_type), intent(in) :: *field1*, *field2*
* type(field_type), intent(out) :: *field3*

inner_product
+++++++++++++

**inner_product** (*field1*, *field2*, *sumval*)

Computes the inner product of the fields *field1* and *field2*, *i.e.*: ::

  sumval = SUM(field1(:)*field2(:))

where:

* type(field_type), intent(in) :: *field1*, *field2*
* real(r_def), intent(out) :: *sumval*

inc_field
+++++++++

**inc_field** (*field1*, *field2*)

Adds the second field to the first and returns it: ::

  field1(:) = field1(:) + field2(:)

where:

* type(field_type), intent(inout) :: *field1*
* type(field_type),    intent(in) :: *field2*

minus_fields
++++++++++++

**minus_fields** (*field1*, *field2*, *field3*)

Subtracts the second field from the first and stores the result in
the third. *i.e.* performs the operation: ::
  
  field3(:) = field1(:) - field2(:)

where:

* type(field_type), intent(in) :: *field1*
* type(field_type), intent(in) :: *field2*
* type(field_type), intent(out) :: *field3*

multiply_fields
+++++++++++++++

**multiply_fields** (*field1*, *field2*, *field3*)

Multiplies two fields together and returns the result in a third field: ::

  field3(:) = field1(:)*field2(:)

where:

* type(field_type), intent(in) :: *field1*, *field2*
* type(field_type), intent(out) :: *field3*

plus_fields
+++++++++++

**plus_fields** (*field1*, *field2*, *field3*)

Sums two fields: ::
  
  field3(:) = field1(:) + field2(:)

where:

* type(field_type), intent(in) :: *field1*
* type(field_type), intent(in) :: *field2*
* type(field_type), intent(out) :: *field3*

set_field_scalar
++++++++++++++++

**set_field_scalar** (*value*, *field*)

Set all elements of the field *field* to the value *value*.
The field may be on any function space.

* type(field_type), intent(out) :: *field*
* real(r_def), intent(in) :: *value*

.. note:: The Fortran parser used by PSyclone cannot currently cope with numerical constants containing an explicit kind paramer (e.g. ``1.0_r_def``). This limitation may be worked around by passing the scalar quantity by argument instead of by value.

sum_field
+++++++++

**sum_field** (*field*, *sumval*)

Sums all of the elements of the field *field* and returns the result
in the scalar variable *sumval*: ::
  
  sumval = SUM(field(:))

where:

* type(field_type), intent(in) :: field
* real(r_def), intent(out) :: sumval

Conventions
-----------

There is a convention in the dynamo0.3 API kernel code that if the
name of the operation being performed is ``<name>`` then a kernel file
is ``<name>_mod.[fF90]``, the name of the module inside the kernel
file is ``<name>_mod``, the name of the kernel metadata in the module
is ``<name>_type`` and the name of the kernel subroutine in the module
is ``<name>_code``. PSyclone does not need this convention to be followed apart from the stub generator (see the :ref:`stub-generation` Section ) where the name of the metadata to be parsed is determined from the module name.

The contents of the metadata is also usually declared private but this
does not affect PSyclone.

Finally, the ``procedure`` metadata (located within the kernel
metadata) usually has ``nopass`` specified but again this is ignored
by PSyclone.

Transformations
---------------

.. note:: To be written.
