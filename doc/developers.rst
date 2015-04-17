.. highlight:: python
   :linenothreshold: 5
Developers guide
****************

Creating a new API
==================

PSyclone has been designed to support multiple API's and to allow new
API's to be added. This section explains how to create a new API in
PSyclone.


Modifying `config.py <https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/config.py>`_
---------

The names of the supported API's and the default API are specified in
`config.py <https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/config.py>`_. When adding a new API you must add the name you would like
to use to the *SUPPORTEDAPIS* list (and change the *DEFAULTAPI* if
required).

For example, if we would like to add a new API called *dynamo0.3* and make it the default, the appopriate lines of `config.py <https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/config.py>`_ would look like this:
::
	SUPPORTEDAPIS=["gunghoproto","dynamo0.1","gocean","dynamo0.3"]
	DEFAULTAPI="dynamo0.3"


Modifying `parse.py <https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/parse.py>`_
--------

The parser code, `parse.py
<https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/parse.py>`_,
takes an algorithm code as input. It parses the algorithm code and
finds and parses any kernels that are referenced by the algorithm
code. It returns the parsed algorithm code as an *ast* and an object
containing all the required algorithm invocation information and its
associated kernel information.

>>> from parse import parse
>>> ast, info = parse("example.F90")

The parser currently assumes that all API's will use the standard
*invoke()* approach within the algorithm layer but that the content
and structure of the metadata in the kernel code may differ.

If the algorithm API differs from this expectation, then the parser
will need to be refactored. Any such refactoring is beyond the scope
of this document and is currently not part of the PSyclone software
design.

To add support for a new API, three classes need to be modified and/or
created in `parse.py
<https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/parse.py>`_. The
KernelTypeFactory class needs to be modified, a new subclass of the
KernelType class needs to be created and a new subclass of the
Descriptor class needs to be created. These modifications and
additions are detailed in the following 3 sections.

Modifying the KernelTypeFactory Class
+++++++++++++++++++++++

Kernel metadata, is likely to be different from one API to another. To
parse this kernel-API-specific metadata a *KernelTypeFactory* is
provided which is responsible for returning the appropriate
*KernelType* object. The *KernelTypeFactory* class is found in
`parse.py
<https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/parse.py>`_
at line 232.

For example, assuming we want a new *KernelType* for the 0.3 dynamo
API which we decided to call *DynKernelType03* we would modify the
*create* method of *KernelTypeFactory* as shown below:
::
	def create(self,name,ast):
	    if self._type=="gunghoproto":
     	        return GHProtoKernelType(name,ast)
	    elif self._type=="dynamo0.1":
	        return DynKernelType(name,ast)
	    elif self._type=="gocean":
	        return GOKernelType(name,ast)
	    elif self._type=="dynamo0.3":
	        return DynKernelType03(name,ast)
	    else:
	        raise ParseError("KernelTypeFactory: Internal Error: Unsupported kernel type '{0}' found.
                                  Should not be possible.".format(self._type))

If the kernel metadata happens to be the same as another existing API
then the existing KernelType subclass can be used for the new API.

For example, assuming the 0.3 dynamo API uses the same metadata as the
0.1 dynamo API we could modify the *create* method of
*KernelTypeFactory* in the following way leading to the
*DynKernelType* object being returned for both the *dynamo0.1* and
*dynamo0.3* API's.
::
	def create(self,name,ast):
	        if self._type=="gunghoproto":
	            return GHProtoKernelType(name,ast)
	        elif self._type in ["dynamo0.1","dynamo0.3"]:
	            return DynKernelType(name,ast)
	        elif self._type=="gocean":
	            return GOKernelType(name,ast)
	        else:
	            raise ParseError("KernelTypeFactory: Internal Error: Unsupported kernel type '{0}' found.
                                      Should not be possible.".format(self._type))

Sub-classing the KernelType Class
++++++++++++++++

The role of the API-specific *KernelType* **subclass** is to capture all
the required kernel metadata for the particular API. This information
will be used by psyGen.py to generate the PSy layer code.

The *KernelType* **class** (see `parse.py
<https://puma.nerc.ac.uk/trac/GungHo/browser/PSyclone/trunk/src/parse.py>`_
line 253) makes the assumption that Kernel metadata will be stored
within the Kernel fortran module as a Fortran type with a particular
structure.  Below gives an example of the expected structure with
information that can vary from one API to another being shown in
xml-style brackets (<.../>)
::
  type, public, extends(kernel_type) :: <typename/>
    private
    type(<sometype/>) :: meta_args(<n/>) = (/                            &
         <sometype/>(<arg1/>,<arg2/>,...,<argn/>),                       &
         <sometype/>(<arg1/>,<arg2/>,...,<argn/>),                       &
         ...                                                             &
         /)
    integer :: iterates_over = <somespace/>
  contains
    procedure, nopass :: <kernelname/>
  end type

Therefore a type is expected which extends *kernel_type* and contains
a *meta_args* array of types (one for each field passed to the
Kernel). The meta_args types are each initialised via a structure
constructor. The type also contains an integer iterates_over which is
set to a value and a procedure which provide the name of the actual
kernel code.

If the new API provides metadata in the above format then the
*KernelType* **sub-class** can use the *KernelType* **class** to
extract the metadata. To do this the the *KernelType* subclass needs
to specialise the *KernelType __init__* method and initialise the
*KernelType* class with the supplied arguments.
::
	class DynKernelType03(KernelType):
	    def __init__(self,name,ast):
	        KernelType.__init__(self,name,ast)
	
**UP TO HERE , UP TO HERE**

Base class provides _inits list with each info
Need to populate _arg_descriptors list with this info. For 0.3 API
DynArgDescriptor03, captures metadata about each argument (field)
::
	class DynKernelType03(KernelType):
	    def __init__(self,name,ast):
	        KernelType.__init__(self,name,ast)

	        # parse arg_type metadata
	        self._arg_descriptors=[]
	        for arg_type in self._inits:
	            self._arg_descriptors.append(DynArgDescriptor03(arg_type))



%Checks whether the metadata is public (it should be ?)
%Assumes iterates_over variable.
%Binding to a procedure - assumes one of two styles.
%Assumes a meta_args type

The KernelType subclass must then create and store an api-specific
subclass of the Descriptor class (see below) for each of the meta_args
arguments and populate this with the relevant API-specific metadata.

For simplicitity API's should try to conform to the supported
structure. However, in some cases additional information may be
required. In the dynamo0.3 API, for example, two different types of
metadata are required (metadata associated with arguments and metadata
associated with function space). In this case there is a meta_args
variable and a separate meta_funcs variable. This additional metadata
can be supported by using the getkerneldescriptors() method in the
base class (see the code for more details) with the optional var_name
being set to the appropriate name to parse the metadata.

Descriptor Class
++++++++++++++++

The role of a descriptor class is to store the information in each
of the entries in the meta_args (or equivalent) array. It can also be
used to check whether the content, structure and order of the arrays
are valid.

An api specific version of this class should be created and can make
use of the base class if it is beneficial. The base class provides
space for 3 types of metadata, "access type", "function space" and
"stencil type".

At this point you should be able to successfully parse the kernel metadata
provided by the new API.

psyGen.py
---------

psyGen.py contains the code to generate the PSy layer from the
metadata provided by the parser.

In order to support the generation of PSy code for a new api in
PSyclone a new file needs to be created and the following classes
found in psyGen.py need to be subclassed within it:

PSy, Invokes, Invoke, Schedule, Loop, Kern, Arguments, Argument

You may also need to subclass the Inf class depending on the api.

If there is already a similar API available a simple way to start
would be to make a copy of the associated file, renaming it
appropriately.

PSyFactory Class
++++++++++++++++

Once the subclass of the PSy class has been created, it should be
added as an option to the create() method in the PSyFactory class
within psyGen.py.

Class Initialisation
++++++++++++++++++++

The parser information passed to the PSy layer is used to create an
invokes object which in turn creates a list of invoke objects. Each
invoke object contains a schedule and a schedule consists of loops and
calls. Finally, a call contains an arguments object which itself
contains a list of argument objects.

To make sure the subclass versions of the above objects are created
the __init__ methods of the subclasses must make sure they create
the appropriate objects.

Some of the baseclass constructors (__init__ methods) support the
classname being provided. This allow them to instantiate the
appropriate objects without knowing what they are.

gen_code()
++++++++++

All of the above classes (with the exception of PSy which supports a
gen() method) have the gen_code() method. This method passes the
parent of the generation tree and expect the object to add the code
associated with the object as a child of the parent. The object is
then expected to call any children. This approach is powerful as it
lets each object concentrate on the code that it is responsible for.

Adding code in gen_code() : f2pygen
+++++++++++++++++++++++++++++++++++

The f2pygen classes have been developed to help create appropriate
fortran code in the gen_code() method.

When writing a gen_code() method for a particular object and API it is
natural to add code as a child of the parent provided by the callee of
the method. However, in some cases we do not want code to appear at
the current position in the hierarchy.

The add() method
++++++++++++++++

PSyclone supports the addition of code to an ast via the add() method

explicitely place at the appropriate place in the hierarchy. For example,
parent.parent.add(...)

optional argument. default is auto. This attempts to place code in the
expected place. For example, specify a declaration. auto finds a
correct place to put this code.

Specify position explicitly
"before", "after", "first", "last"

Sometimes don't know exactly where to place. On example that is
supported is when you want to add something before or after a loop
nest. start_parent_loop(). This method recurses up until the parent is
not a loop, it then skips any comments (as they may be directives) and
return this position. Therefore supports an arbitrary number of loops
and directives.

.. OpenMP Support
==============
Loop directives are treated as first class entities in the psyGen
package. Therefore they can be added to psyGen's high level
representation of the fortran code structure in the same way as calls
and loops. Obviously it is only valid to add a loop directive outside
of a loop.

.. When adding a call inside a loop the placement of any additional calls
or declarations must be specified correctly to ensure that they are
placed at the correct location in the hierarchy. To avoid accidentally
splitting the loop directive from its loop the start_parent_loop()
method can be used. This is available as a method in all fortran
generation calls. ** We could have placed it in psyGen instead of
f2pygen **.  This method returns the location at the top of any loop
hierarchy and before any comments immediately before the top level
loop.

.. The OpenMPLoopDirective object needs to know which variables are
shared and which are private. In the current implementation default
shared is used and private variables are listed. To determine the
objects private variables the OpenMP implementation uses its internal
_get_private_list() method. This method first finds all loops
contained within the directive and adds each loops variable name as a
private variable. this method then finds all calls contained within
the directive and adds each calls list of private variables, returned
with the local_vars() method. Therefore the OpenMPLoopDirective object
relies on calls specifying which variables they require being local.
