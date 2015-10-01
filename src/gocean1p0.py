#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Authors R. Ford and A. R. Porter, STFC Daresbury Lab
# Funded by the GOcean project

'''This module implements the PSyclone GOcean 1.0 API by specialising
    the required base classes for both code generation (PSy, Invokes,
    Invoke, Schedule, Loop, Kern, Inf, Arguments and KernelArgument)
    and parsing (Descriptor and KernelType). It adds a
    GOKernelGridArgument class to capture information on kernel arguments
    that supply properties of the grid (and are generated in the PSy
    layer).

'''

from parse import Descriptor, KernelType, ParseError
from psyGen import PSy, Invokes, Invoke, Schedule, Loop, Kern, Arguments, \
                   KernelArgument, GenerationError, Inf, Node

# The different grid-point types that a field can live on
VALID_FIELD_GRID_TYPES = ["cu", "cv", "ct", "cf", "every"]

# The two scalar types we support
VALID_SCALAR_TYPES = ["i_scalar", "r_scalar"]

# Index-offset schemes (for the Arakawa C-grid)
VALID_OFFSET_NAMES = ["offset_se", "offset_sw",
                      "offset_ne", "offset_nw", "offset_any"]

# The sets of grid points that a kernel may operate on
VALID_ITERATES_OVER = ["all_pts", "internal_pts", "external_pts"]

# Valid values for the type of access a kernel argument may have
VALID_ARG_ACCESSES = ["read", "write", "readwrite"]

# The list of valid stencil properties. We currently only support
# pointwise. This property could probably be removed from the
# GOcean API altogether.
VALID_STENCILS = ["pointwise"]

# A dictionary giving the mapping from meta-data names for
# properties of the grid to their names in the Fortran grid_type.
GRID_PROPERTY_DICT = {"grid_area_t":"area_t",
                      "grid_area_u":"area_u",
                      "grid_area_v":"area_v",
                      "grid_mask_t":"tmask",
                      "grid_dx_t":"dx_t",
                      "grid_dx_u":"dx_u",
                      "grid_dx_v":"dx_v",
                      "grid_dy_t":"dy_t",
                      "grid_dy_u":"dy_u",
                      "grid_dy_v":"dy_v",
                      "grid_lat_u":"gphiu",
                      "grid_lat_v":"gphiv",
                      "grid_dx_const":"dx",
                      "grid_dy_const":"dy"}

# The valid types of loop. In this API we expect only doubly-nested
# loops.
VALID_LOOP_TYPES = ["inner", "outer"]

class GOPSy(PSy):
    ''' The GOcean 1.0 specific PSy class. This creates a GOcean specific
        invokes object (which controls all the required invocation calls).
        Also overrides the PSy gen method so that we generate GOcean-
        specific PSy module code. '''
    def __init__(self, invoke_info):
        PSy.__init__(self, invoke_info)
        self._invokes = GOInvokes(invoke_info.calls)
    @property
    def gen(self):
        '''
        Generate PSy code for the GOcean api v.1.0.

        :rtype: ast

        '''
        from f2pygen import ModuleGen, UseGen

        # create an empty PSy layer module
        psy_module = ModuleGen(self.name)
        # include the kind_params module
        psy_module.add(UseGen(psy_module, name="kind_params_mod"))
        # include the field_mod module
        psy_module.add(UseGen(psy_module, name="field_mod"))
        # add in the subroutines for each invocation
        self.invokes.gen_code(psy_module)
        return psy_module.root

class GOInvokes(Invokes):
    ''' The GOcean specific invokes class. This passes the GOcean specific
        invoke class to the base class so it creates the one we require. '''
    def __init__(self, alg_calls):
        if False:
            self._0_to_n = GOInvoke(None, None) # for pyreverse
        Invokes.__init__(self, alg_calls, GOInvoke)

        index_offsets = []
        # Loop over all of the kernels in all of the invoke() calls
        # and check that they work on compatible grid-index offsets.
        # Strictly speaking this check should be done in the parsing
        # code since it is a check on the correctness of the meta-data.
        # However, that would require a fundamental change to the parsing
        # code since it requires information  on all of the invokes and
        # kernels in an application. Therefore it is much simpler to
        # do it here where we have easy access to that information.
        for invoke in self.invoke_list:
            for kern_call in invoke.schedule.kern_calls():
                # We only care if the index offset is not offset_any (since
                # that is compatible with any other offset)
                if kern_call.index_offset != "offset_any":
                    # Loop over the offsets we've seen so far
                    for offset in index_offsets:
                        if offset != kern_call.index_offset:
                            raise GenerationError("Meta-data error in kernel "
                                                  "{0}: INDEX_OFFSET of '{1}' "
                                                  "does not match that ({2}) "
                                                  "of other kernels. This is "
                                                  "not supported.".\
                                                  format(kern_call.name,
                                                         kern_call.index_offset,
                                                         offset))
                    # Append the index-offset of this kernel to the list of
                    # those seen so far
                    index_offsets.append(kern_call.index_offset)

class GOInvoke(Invoke):
    ''' The GOcean specific invoke class. This passes the GOcean specific
        schedule class to the base class so it creates the one we require.
        A set of GOcean infrastructure reserved names are also passed to
        ensure that there are no name clashes. Also overrides the gen_code
        method so that we generate GOcean specific invocation code and
        provides three methods which separate arguments that are arrays from
        arguments that are {integer, real} scalars. '''
    def __init__(self, alg_invocation, idx):
        if False:
            self._schedule = GOSchedule(None) # for pyreverse
        Invoke.__init__(self, alg_invocation, idx, GOSchedule)

    @property
    def unique_args_arrays(self):
        ''' find unique arguments that are arrays (defined as those that are
            field objects as opposed to scalars or properties of the grid). '''
        result = []
        for call in self._schedule.calls():
            for arg in call.arguments.args:
                if arg.type == 'field' and not arg.name in result:
                    result.append(arg.name)
        return result

    @property
    def unique_args_rscalars(self):
        ''' find unique arguments that are scalars of type real (defined
            as those that are r_scalar 'space'. '''
        result = []
        for call in self._schedule.calls():
            for arg in call.arguments.args:
                if arg.type == 'scalar' and arg.space.lower() == "r_scalar" and\
                   not arg.name in result:
                    result.append(arg.name)
        return result


    @property
    def unique_args_iscalars(self):
        ''' find unique arguments that are scalars of type integer (defined
            as those that are i_scalar 'space'). '''
        result = []
        for call in self._schedule.calls():
            for arg in call.arguments.args:
                if arg.type == 'scalar' and arg.space.lower() == "i_scalar" and\
                   not arg.name in result:
                    result.append(arg.name)
        return result

    def gen_code(self, parent):
        ''' Generates GOcean specific invocation code (the subroutine called
            by the associated invoke call in the algorithm layer). This
            consists of the PSy invocation subroutine and the declaration of
            its arguments.'''
        from f2pygen import SubroutineGen, DeclGen, TypeDeclGen
        # create the subroutine
        invoke_sub = SubroutineGen(parent, name=self.name,
                                   args=self.psy_unique_var_names)
        parent.add(invoke_sub)
        self.schedule.gen_code(invoke_sub)
        # add the subroutine argument declarations for arrays
        if len(self.unique_args_arrays) > 0:
            my_decl_arrays = TypeDeclGen(invoke_sub, datatype="r2d_field",
                                         intent="inout",
                                         entity_decls=self.unique_args_arrays)
            invoke_sub.add(my_decl_arrays)
        # add the subroutine argument declarations for real scalars
        if len(self.unique_args_rscalars) > 0:
            my_decl_rscalars = DeclGen(invoke_sub, datatype="REAL",
                                       intent="inout", kind="wp",
                                       entity_decls=self.unique_args_rscalars)
            invoke_sub.add(my_decl_rscalars)
        # add the subroutine argument declarations for integer scalars
        if len(self.unique_args_iscalars) > 0:
            my_decl_iscalars = DeclGen(invoke_sub, datatype="INTEGER",
                                       intent="inout",
                                       entity_decls=self.unique_args_iscalars)
            invoke_sub.add(my_decl_iscalars)

class GOSchedule(Schedule):

    ''' The GOcean specific schedule class. The PSyclone schedule class assumes
        that a call has one parent loop. Therefore we override the _init_ method
        and add in our two loops. '''

    def __init__(self, alg_calls):
        sequence = []
        from parse import InfCall
        for call in alg_calls:
            if isinstance(call, InfCall):
                sequence.append(GOInf.create(call, parent=self))
            else:
                outer_loop = GOLoop(call=None, parent=self, 
                                    loop_type="outer")
                sequence.append(outer_loop)
                inner_loop = GOLoop(call=None, parent=outer_loop, 
                                    loop_type="inner")
                outer_loop.addchild(inner_loop)
                call = GOKern(call, parent=inner_loop)
                inner_loop.addchild(call)
                # determine inner and outer loops space information from the
                # child kernel call. This is only picked up automatically (by
                # the inner loop) if the kernel call is passed into the inner
                # loop.
                inner_loop.iteration_space = call.iterates_over
                outer_loop.iteration_space = inner_loop.iteration_space
                inner_loop.field_space = call.arguments.iteration_space_arg().\
                                         function_space
                outer_loop.field_space = inner_loop.field_space
                inner_loop.field_name = call.arguments.iteration_space_arg().\
                                        name
                outer_loop.field_name = inner_loop.field_name
        Node.__init__(self, children=sequence)

class GOLoop(Loop):
    ''' The GOcean specific Loop class. This passes the GOcean specific
        single loop information to the base class so it creates the one we
        require. Adds a GOcean specific setBounds method which tells the loop
        what to iterate over. Need to harmonise with the topology_name method
        in the Dynamo api. '''
    def __init__(self, call=None, parent=None,
                 topology_name="", loop_type=""):
        Loop.__init__(self, GOInf, GOKern, call=call, parent=parent,
                      valid_loop_types=VALID_LOOP_TYPES)
        self.loop_type = loop_type

        if self._loop_type == "inner":
            self._variable_name = "i"
        elif self._loop_type == "outer":
            self._variable_name = "j"
        else:
            raise GenerationError("Invalid loop type of '{0}'. Expected "
                                  "one of {1}".\
                                  format(self._loop_type, VALID_LOOP_TYPES))

    def gen_code(self, parent):

        if self.field_space == "every":
            from f2pygen import DeclGen, AssignGen
            dim_var = DeclGen(parent, datatype="INTEGER",
                              entity_decls=[self._variable_name])
            parent.add(dim_var)

            # loop bounds
            self._start = "1"
            if self._loop_type == "inner":
                self._stop = "SIZE("+self.field_name+"%data, 1)"
            elif self._loop_type == "outer":
                self._stop = "SIZE("+self.field_name+"%data, 2)"

        else: # one of our spaces so use values provided by the infrastructure

            # loop bounds are pulled from the field object
            self._start = self.field_name
            self._stop = self.field_name

            if self._iteration_space.lower() == "internal_pts":
                self._start += "%internal"
                self._stop += "%internal"
            elif self._iteration_space.lower() == "all_pts":
                self._start += "%whole"
                self._stop += "%whole"
            else:
                raise GenerationError("Unrecognised iteration space, {0}. "
                                      "Cannot generate loop bounds.".\
                                      format(self._iteration_space))

            if self._loop_type == "inner":
                self._start += "%xstart"
                self._stop += "%xstop"
            elif self._loop_type == "outer":
                self._start += "%ystart"
                self._stop += "%ystop"

        Loop.gen_code(self, parent)

class GOInf(Inf):
    ''' A GOcean specific infrastructure call factory. No infrastructure
        calls are supported in GOcean at the moment so we just call the base
        class (which currently recognises the set() infrastructure call). '''
    @staticmethod
    def create(call, parent=None):
        ''' Creates a specific infrastructure call. Currently just calls
            the base class method. '''
        return Inf.create(call, parent)

class GOKern(Kern):
    ''' Stores information about GOcean Kernels as specified by the Kernel
        metadata. Uses this information to generate appropriate PSy layer
        code for the Kernel instance. Specialises the gen_code method to
        create the appropriate GOcean specific kernel call. '''
    def __init__(self, call, parent=None):
        if False:
            self._arguments = GOKernelArguments(None, None) # for pyreverse
        Kern.__init__(self, GOKernelArguments, call, parent, check=False)

        # Pull out the grid index-offset that this kernel expects and
        # store it here. This is used to check that all of the kernels
        # invoked by an application are using compatible index offsets.
        self._index_offset = call.ktype.index_offset

    def local_vars(self):
        return []

    def _find_grid_access(self):
        '''Determine the best kernel argument from which to get properties of
            the grid. For this, an argument must be a field (i.e. not
            a scalar) and must be supplied by the algorithm layer
            (i.e. not a grid property). If possible it should also be
            a field that is read-only as otherwise compilers can get
            confused about data dependencies and refuse to SIMD
            vectorise.

        '''
        for access in ["read", "readwrite", "write"]:
            for arg in self._arguments.args:
                if arg.type == "field" and arg.access.lower() == access:
                    return arg
        # We failed to find any kernel argument which could be used
        # to access the grid properties. This will only be a problem
        # if the kernel requires a grid-property argument.
        return None

    def gen_code(self, parent):
        ''' Generates GOcean v1.0 specific psy code for a call to the dynamo
            kernel instance. '''
        from f2pygen import CallGen, UseGen

        # Before we do anything else, go through the arguments and
        # determine the best one from which to obtain the grid properties.
        grid_arg = self._find_grid_access()

        # A GOcean 1.0 kernel always requires the [i,j] indices of the
        # grid-point that is to be updated
        arguments = ["i", "j"]
        for arg in self._arguments.args:

            if arg.type == "scalar":
                # Scalar arguments require no de-referencing
                arguments.append(arg.name)
            elif arg.type == "field":
                # Field objects are Fortran derived-types
                arguments.append(arg.name + "%data")
            elif arg.type == "grid_property":
                # Argument is a property of the grid which we can access via
                # the grid member of any field object.
                # We use the most suitable field as chosen above.
                if grid_arg is None:
                    raise GenerationError("Error: kernel {0} requires "
                                          "grid property {1} but does not "
                                          "have any arguments that are "
                                          "fields".format(self._name, arg.name))
                else:
                    arguments.append(grid_arg.name+"%grid%"+arg.name)
            else:
                raise GenerationError("Kernel {0}, argument {1} has "
                                      "unrecognised type: {2}".\
                                      format(self._name, arg.name, arg.type))

        parent.add(CallGen(parent, self._name, arguments))
        parent.add(UseGen(parent, name=self._module_name, only=True,
                          funcnames=[self._name]))

    @property
    def index_offset(self):
        ''' The grid index-offset convention that this kernel expects '''
        return self._index_offset

class GOKernelArguments(Arguments):
    '''Provides information about GOcean kernel-call arguments
        collectively, as specified by the kernel argument
        metadata. This class ensures that initialisation is performed
        correctly. It also overrides the iteration_space_arg method to
        supply a GOcean-specific dictionary for the mapping of
        argument-access types.

    '''
    def __init__(self, call, parent_call):
        if False:
            self._0_to_n = GOKernelArgument(None, None, None) # for pyreverse
        Arguments.__init__(self, parent_call)

        self._args = []
        # Loop over the kernel arguments obtained from the meta data
        for (idx, arg) in enumerate(call.ktype.arg_descriptors):
            # arg is a GO1p0Descriptor object
            if arg.type == "grid_property":
                # This is an argument supplied by the psy layer
                self._args.append(GOKernelGridArgument(arg))
            elif arg.type == "scalar" or arg.type == "field":
                # This is a kernel argument supplied by the Algorithm layer
                self._args.append(GOKernelArgument(arg, call.args[idx],
                                                   parent_call))
            else:
                raise ParseError("Invalid kernel argument type. Found '{0}' "
                                 "but must be one of {1}".\
                                 format(arg.type, ["grid_property", "scalar",
                                                   "field"]))
        self._dofs = []
    @property
    def dofs(self):
        ''' Currently required for invoke base class although this makes no
            sense for GOcean. Need to refactor the invoke class and pull out
            dofs into the gunghoproto api '''
        return self._dofs

    def iteration_space_arg(self, mapping={}):
        if mapping != {}:
            my_mapping = mapping
        else:
            # We provide an empty mapping for inc as it is not supported
            # in the GOcean 1.0 API. However, the entry has to be there
            # in the dictionary as a field that has read access causes
            # the code (that checks that a kernel has at least one argument
            # that is written to) to attempt to lookup "inc".
            my_mapping = {"write":"write", "read":"read",
                          "readwrite":"readwrite", "inc":""}
        arg = Arguments.iteration_space_arg(self, my_mapping)
        return arg

class GOKernelArgument(KernelArgument):
    ''' Provides information about individual GOcean kernel call arguments
        as specified by the kernel argument metadata. '''
    def __init__(self, arg, arg_info, call):

        self._arg = arg
        KernelArgument.__init__(self, arg, arg_info, call)

    @property
    def type(self):
        ''' Return the type of this kernel argument - whether it is a field,
            a scalar or a grid_property (to be supplied by the PSy layer) '''
        return self._arg.type

    @property
    def function_space(self):
        ''' Returns the expected finite difference space for this
            argument as specified by the kernel argument metadata.'''
        return self._arg.function_space

class GOKernelGridArgument(object):
    ''' Describes arguments that supply grid properties to a kernel.
        These arguments are provided by the PSy layer rather than in
        the Algorithm layer. '''

    def __init__(self, arg):

        if GRID_PROPERTY_DICT.has_key(arg.grid_prop):
            self._name = GRID_PROPERTY_DICT[arg.grid_prop]
        else:
            raise GenerationError("Unrecognised grid property specified. "
                                  "Expected one of {0} but found '{1}'".\
                                  format(str(GRID_PROPERTY_DICT.keys()),
                                         arg.grid_prop))

        # This object always represents an argument that is a grid_property
        self._type = "grid_property"

    @property
    def name(self):
        ''' Returns the Fortran name of the grid property. This name is
            used in the generated code like so: <fld>%grid%name '''
        return self._name

    @property
    def type(self):
        ''' The type of this argument. We have this for compatibility with
            GOKernelArgument objects since, for this class, it will always be
            "grid_property". '''
        return self._type

    @property
    def text(self):
        ''' The raw text used to pass data from the algorithm layer
            for this argument. Grid properties are not passed from the
            algorithm layer so None is returned.'''
        return None

class GO1p0Descriptor(Descriptor):
    '''Description of a GOcean 1.0 kernel argument, as obtained by
        parsing the kernel meta-data

    '''

    def __init__(self, kernel_name, kernel_arg):

        nargs = len(kernel_arg.args)

        if nargs == 3:
            # This kernel argument is supplied by the Algorithm layer
            # and is either a field or a scalar

            access = kernel_arg.args[0].name
            funcspace = kernel_arg.args[1].name
            stencil = kernel_arg.args[2].name

            # Valid values for the grid-point type that a kernel argument
            # may have. (We use the funcspace argument for this as it is
            # similar to the space in Finite-Element world.)
            valid_func_spaces = VALID_FIELD_GRID_TYPES + VALID_SCALAR_TYPES

            self._grid_prop = ""
            if funcspace.lower() in VALID_FIELD_GRID_TYPES:
                self._type = "field"
            elif funcspace.lower() in VALID_SCALAR_TYPES:
                self._type = "scalar"
            else:
                raise ParseError("Meta-data error in kernel {0}: argument "
                                 "grid-point type is '{1}' but must be one "
                                 "of {2} ".format(kernel_name, funcspace,
                                                 valid_func_spaces))

            if stencil.lower() not in VALID_STENCILS:
                raise ParseError("Meta-data error in kernel {0}: 3rd "
                                 "descriptor (stencil) of field argument "
                                 "is '{1}' but must be one of {2}".\
                                 format(kernel_name, stencil, VALID_STENCILS))

        elif nargs == 2:
            # This kernel argument is a property of the grid
            access = kernel_arg.args[0].name
            grid_var = kernel_arg.args[1].name
            funcspace = ""
            stencil = ""

            self._grid_prop = grid_var
            self._type = "grid_property"

            if not GRID_PROPERTY_DICT.has_key(grid_var.lower()):
                raise ParseError("Meta-data error in kernel {0}: "
                                 "un-recognised grid property '{1}' "
                                 "requested. Must be "
                                 "one of {2}".format(kernel_name, grid_var,
                                                    str(GRID_PROPERTY_DICT.\
                                                        keys())))
        else:
            raise ParseError("Meta-data error in kernel {0}: 'arg' type "
                             "expects 2 or 3 arguments but "
                             "found '{1}' in '{2}'".\
                             format(kernel_name, str(len(kernel_arg.args)),
                                    kernel_arg.args))

        if access.lower() not in VALID_ARG_ACCESSES:
            raise ParseError("Meta-data error in kernel {0}: argument "
                             "access  is given as '{1}' but must be "
                             "one of {2}".\
                             format(kernel_name, access, VALID_ARG_ACCESSES))

        # Finally we can call the __init__ method of our base class
        Descriptor.__init__(self, access, funcspace, stencil)

    def __str__(self):
        return repr(self)
    @property
    def grid_prop(self):
        ''' The name of the grid-property that this argument is to supply
            to the kernel '''
        return self._grid_prop
    @property
    def type(self):
        ''' The type of this argument - whether it is a scalar, a field or
            a grid-property. The latter are special because they must be
            supplied by the PSy layer. '''
        return self._type

class GOKernelType1p0(KernelType):
    ''' Description of a kernel including the grid index-offset it
        expects and the region of the grid that it expects to
        operate upon '''

    def __str__(self):
        return 'GOcean 1.0 kernel '+self._name+', index-offset = '+\
            self._index_offset +', iterates-over = '+self._iterates_over

    def __init__(self, name, ast):
        # Initialise the base class
        KernelType.__init__(self, name, ast)

        # What grid offset scheme this kernel expects
        self._index_offset = self._ktype.get_variable('index_offset').init

        if self._index_offset is None:
            raise ParseError("Meta-data error in kernel {0}: an INDEX_OFFSET "
                             "must be specified and must be one of {1}".\
                             format(name, VALID_OFFSET_NAMES))

        if self._index_offset.lower() not in VALID_OFFSET_NAMES:
            raise ParseError("Meta-data error in kernel {0}: INDEX_OFFSET "
                             "has value '{1}' but must be one of {2}".\
                             format(name,
                                    self._index_offset,
                                    VALID_OFFSET_NAMES))

        # Check that the meta-data for this kernel is valid
        if self._iterates_over is None:
            raise ParseError("Meta-data error in kernel {0}: ITERATES_OVER "
                             "is missing. (Valid values are: {1})".\
                             format(name, VALID_ITERATES_OVER))

        if self._iterates_over.lower() not in VALID_ITERATES_OVER:
            raise ParseError("Meta-data error in kernel {0}: ITERATES_OVER "
                             "has value '{1}' but must be one of {2}".\
                             format(name,
                                    self._iterates_over.lower(),
                                    VALID_ITERATES_OVER))

        # The list of kernel arguments
        self._arg_descriptors = []
        for init in self._inits:
            if init.name != 'arg':
                raise ParseError("Each meta_arg value must be of type "+
                                 "'arg' for the gocean1.0 api, but "+
                                 "found '{0}'".format(init.name))
            # Pass in the name of this kernel for the purposes
            # of error reporting
            self._arg_descriptors.append(GO1p0Descriptor(name, init))

    # Override nargs from the base class so that it returns the no.
    # of args specified in the algorithm layer (and thus excludes those
    # that must be added in the PSy layer). This is done to simplify the
    # check on the no. of arguments supplied in any invoke of the kernel.
    @property
    def nargs(self):
        ''' Count and return the number of arguments that this kernel
            expects the Algorithm layer to provide '''
        count = 0
        for arg in self.arg_descriptors:
            if arg.type != "grid_property":
                count += 1
        return count

    @property
    def index_offset(self):
        ''' Return the grid index-offset that this kernel expects '''
        return self._index_offset
