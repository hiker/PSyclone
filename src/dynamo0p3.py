# ------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# ------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

''' This module implements the PSyclone Dynamo 0.3 API by 1)
    specialising the required base classes in parser.py (Descriptor,
    KernelType) and adding a new class (DynFuncDescriptor03) to
    capture function descriptor metadata and 2) specialising the
    required base classes in psyGen.py (PSy, Invokes, Invoke, Schedule,
    Loop, Kern, Inf, Arguments and Argument). '''

# first section : Parser specialisations and classes

# imports
from parse import Descriptor, KernelType, ParseError
import expression as expr
import fparser
import os

# constants
VALID_ANY_SPACE_NAMES = ["any_space_1", "any_space_2", "any_space_3",
                         "any_space_4", "any_space_5", "any_space_6",
                         "any_space_7", "any_space_8", "any_space_9"]

VALID_FUNCTION_SPACE_NAMES = ["w0", "w1", "w2", "w3"] + VALID_ANY_SPACE_NAMES

VALID_OPERATOR_NAMES = ["gh_basis", "gh_diff_basis", "gh_orientation"]

VALID_ARG_TYPE_NAMES = ["gh_field", "gh_operator"]

VALID_ACCESS_DESCRIPTOR_NAMES = ["gh_read", "gh_write", "gh_inc"]

# classes


class DynFuncDescriptor03(object):
    ''' The Dynamo 0.3 API includes a function-space descriptor as
    well as an argument descriptor which is not supported by the base
    classes. This class captures the information specified in a
    function-space descriptor. '''

    def __init__(self, func_type):
        self._func_type = func_type
        if func_type.name != 'func_type':
            raise ParseError(
                "In the dynamo0.3 API each meta_func entry must be of type "
                "'func_type' but found '{0}'".format(func_type.name))
        if len(func_type.args) < 2:
            raise ParseError(
                "In the dynamo0.3 API each meta_func entry must have at "
                "least 2 args, but found '{0}'".format(len(func_type.args)))
        self._operator_names = []
        for idx, arg in enumerate(func_type.args):
            if idx == 0:  # first func_type arg
                if arg.name not in VALID_FUNCTION_SPACE_NAMES:
                    raise ParseError(
                        "In the dynamo0p3 API the 1st argument of a "
                        "meta_func entry should be a valid function space "
                        "name (one of {0}), but found '{1}' in '{2}'".format(
                            VALID_FUNCTION_SPACE_NAMES, arg.name, func_type))
                self._function_space_name = arg.name
            else:  # subsequent func_type args
                if arg.name not in VALID_OPERATOR_NAMES:
                    raise ParseError(
                        "In the dynamo0.3 API, the 2nd argument and all "
                        "subsequent arguments of a meta_func entry should "
                        "be a valid operator name (one of {0}), but found "
                        "'{1}' in '{2}".format(VALID_OPERATOR_NAMES,
                                               arg.name, func_type))
                if arg.name in self._operator_names:
                    raise ParseError(
                        "In the dynamo0.3 API, it is an error to specify an "
                        "operator name more than once in a meta_func entry, "
                        "but '{0}' is replicated in '{1}".format(arg.name,
                                                                 func_type))
                self._operator_names.append(arg.name)
        self._name = func_type.name

    @property
    def function_space_name(self):
        ''' Returns the name of the descriptors function space '''
        return self._function_space_name

    @property
    def operator_names(self):
        ''' Returns a list of operators that are associated with this
        descriptors function space '''
        return self._operator_names

    def __repr__(self):
        return "DynFuncDescriptor03({0})".format(self._func_type)

    def __str__(self):
        res = "DynFuncDescriptor03 object" + os.linesep
        res += "  name='{0}'".format(self._name) + os.linesep
        res += "  nargs={0}".format(len(self._operator_names)+1) + os.linesep
        res += "  function_space_name[{0}] = '{1}'".\
               format(0, self._function_space_name) + os.linesep
        for idx, arg in enumerate(self._operator_names):
            res += "  operator_name[{0}] = '{1}'".format(idx+1, arg) + \
                   os.linesep
        return res


class DynArgDescriptor03(Descriptor):
    ''' This class captures the information specified in an argument
    descriptor.'''

    def __init__(self, arg_type):
        self._arg_type = arg_type
        if arg_type.name != 'arg_type':
            raise ParseError(
                "In the dynamo0.3 API aach meta_arg entry must be of type "
                "'arg_type', but found '{0}'".format(arg_type.name))
        # we require at least 3 args
        if len(arg_type.args) < 3:
            raise ParseError(
                "In the dynamo0.3 API each meta_arg entry must have at least "
                "3 args, but found '{0}'".format(len(arg_type.args)))
        # the first arg is the type of field, possibly with a *n appended
        self._vector_size = 1
        if isinstance(arg_type.args[0], expr.BinaryOperator):
            # we expect 'field_type * n' to have been specified
            self._type = arg_type.args[0].toks[0].name
            operator = arg_type.args[0].toks[1]
            try:
                self._vector_size = int(arg_type.args[0].toks[2])
            except TypeError:
                raise ParseError(
                    "In the dynamo0.3 API vector notation expects the format "
                    "(field*n) where n is an integer, but the following was "
                    "found '{0}' in '{1}'.".
                    format(str(arg_type.args[0].toks[2]), arg_type))
            if self._type not in VALID_ARG_TYPE_NAMES:
                raise ParseError(
                    "In the dynamo0.3 API the 1st argument of a meta_arg "
                    "entry should be a valid argument type (one of {0}), but "
                    "found '{1}' in '{2}'".format(VALID_ARG_TYPE_NAMES,
                                                  self._type, arg_type))
            if not operator == "*":
                raise ParseError(
                    "In the dynamo0.3 API the 1st argument of a meta_arg "
                    "entry may be a vector but if so must use '*' as the "
                    "separator in the format (field*n), but found '{0}' in "
                    "'{1}'".format(operator, arg_type))
            if not self._vector_size > 1:
                raise ParseError(
                    "In the dynamo0.3 API the 1st argument of a meta_arg "
                    "entry may be a vector but if so must contain a valid "
                    "integer vector size in the format (field*n where n>1), "
                    "but found '{0}' in '{1}'".format(self._vector_size,
                                                      arg_type))

        elif isinstance(arg_type.args[0], expr.FunctionVar):
            # we expect 'field_type' to have been specified
            if arg_type.args[0].name not in VALID_ARG_TYPE_NAMES:
                raise ParseError(
                    "In the dynamo0.3 API Each the 1st argument of a "
                    "meta_arg entry should be a valid argument type (one of "
                    "{0}), but found '{1}' in '{2}'".
                    format(VALID_ARG_TYPE_NAMES, arg_type.args[0].name,
                           arg_type))
            self._type = arg_type.args[0].name
        else:
            raise ParseError(
                "Internal error in DynArgDescriptor03.__init__, (1) should "
                "not get to here")
        # The 2nd arg is an access descriptor
        if arg_type.args[1].name not in VALID_ACCESS_DESCRIPTOR_NAMES:
            raise ParseError(
                "In the dynamo0.3 API the 2nd argument of a meta_arg entry "
                "must be a valid access descriptor (one of {0}), but found "
                "'{1}' in '{2}'".format(VALID_ACCESS_DESCRIPTOR_NAMES,
                                        arg_type.args[1].name, arg_type))
        self._access_descriptor = arg_type.args[1]
        if self._type == "gh_field":
            # we expect 3 arguments in total with the 3rd being a
            # function space
            if len(arg_type.args) != 3:
                raise ParseError(
                    "In the dynamo0.3 API each meta_arg entry must have 3 "
                    "arguments if its first argument is gh_field, but found "
                    "{0} in '{1}'").format(len(arg_type.args), arg_type)
            if arg_type.args[2].name not in VALID_FUNCTION_SPACE_NAMES:
                raise ParseError(
                    "In the dynamo0.3 API the 3rd argument of a meta_arg "
                    "entry must be a valid function space name (one of {0}), "
                    "but found '{1}' in '{2}".
                    format(VALID_FUNCTION_SPACE_NAMES, arg_type.args[2].name,
                           arg_type))
            self._function_space1 = arg_type.args[2].name
        elif self._type == "gh_operator":
            # we expect 4 arguments with the 3rd and 4th each being a
            # function space
            if len(arg_type.args) != 4:
                raise ParseError(
                    "In the dynamo0.3 API each meta_arg entry must have 4 "
                    "arguments if its first argument is gh_operator, but "
                    "found {0} in '{1}'").format(len(arg_type.args), arg_type)
            if arg_type.args[2].name not in VALID_FUNCTION_SPACE_NAMES:
                raise ParseError(
                    "In the dynamo0.3 API the 3rd argument of a meta_arg "
                    "entry must be a valid function space name (one of {0}), "
                    "but found '{1}' in '{2}".
                    format(VALID_FUNCTION_SPACE_NAMES, arg_type.args[2].name,
                           arg_type))
            self._function_space1 = arg_type.args[2].name
            if arg_type.args[3].name not in VALID_FUNCTION_SPACE_NAMES:
                raise ParseError(
                    "In the dynamo0.3 API the 4th argument of a meta_arg "
                    "entry must be a valid function space name (one of {0}), "
                    "but found '{1}' in '{2}".
                    format(VALID_FUNCTION_SPACE_NAMES, arg_type.args[2].name,
                           arg_type))
            self._function_space2 = arg_type.args[3].name
        else:  # we should never get to here
            raise ParseError(
                "Internal error in DynArgDescriptor03.__init__, (2) should "
                "not get to here")
        Descriptor.__init__(self, self._access_descriptor.name,
                            self._function_space1, None)

    @property
    def function_space_to(self):
        ''' Return the "to" function space for a gh_operator. This is
        the first function space specified in the metadata. Raise an
        error if this is not an operator. '''
        if self._type == "gh_operator":
            return self._function_space1
        else:
            raise RuntimeError(
                "function_space_to only makes sense for a gh_operator, but "
                "this is a '{0}'".format(self._type))

    @property
    def function_space_from(self):
        ''' Return the "from" function space for a gh_operator. This is
        the second function space specified in the metadata. Raise an
        error if this is not an operator. '''
        if self._type == "gh_operator":
            return self._function_space2
        else:
            raise RuntimeError(
                "function_space_from only makes sense for a gh_operator, but "
                "this is a '{0}'".format(self._type))

    @property
    def function_space(self):
        ''' Return the function space name that this instance operates
        on. In the case of a gh_operator, where there are 2 function
        spaces, return function_space_from. '''
        if self._type == "gh_field":
            return self._function_space1
        elif self._type == "gh_operator":
            return self._function_space2
        else:
            raise RuntimeError(
                "Internal error, DynArgDescriptor03:function_space(), should "
                "not get to here.")

    @property
    def is_any_space(self):
        ''' Returns True if this descriptor is of type any_space. This
        could be any on the any_space spaces, i.e. any of any_space_1,
        any_space_2, ... any_space_9, otherwise returns False. For
        operators, returns True if the source descriptor is of type
        any_space, else returns False. '''
        if self.function_space in VALID_ANY_SPACE_NAMES:
            return True
        else:
            return False

    @property
    def vector_size(self):
        ''' Returns the vector size of the argument. This will be 1 if *n
        has not been specified. '''
        return self._vector_size

    @property
    def type(self):
        ''' returns the type of the argument (gh_field, gh_operator, ...). '''
        return self._type

    def __str__(self):
        res = "DynArgDescriptor03 object" + os.linesep
        res += "  argument_type[0]='{0}'".format(self._type)
        if self._vector_size > 1:
            res += "*"+str(self._vector_size)
        res += os.linesep
        res += "  access_descriptor[1]='{0}'".format(self._access_descriptor) \
               + os.linesep
        if self._type == "gh_field":
            res += "  function_space[2]='{0}'".format(self._function_space1) \
                   + os.linesep
        elif self._type == "gh_operator":
            res += "  function_space_to[2]='{0}'".\
                   format(self._function_space1) + os.linesep
            res += "  function_space_from[3]='{0}'".\
                   format(self._function_space2) + os.linesep
        else:  # we should never get to here
            raise ParseError("Internal error in DynArgDescriptor03.__str__")
        return res

    def __repr__(self):
        return "DynArgDescriptor03({0})".format(self._arg_type)


class DynKernelType03(KernelType):
    ''' Captures the Kernel subroutine code and metadata describing
    the subroutine for the Dynamo 0.3 API. '''

    def __init__(self, ast, name=None):
        KernelType.__init__(self, ast, name=name)
        # parse the arg_type metadata
        self._arg_descriptors = []
        for arg_type in self._inits:
            self._arg_descriptors.append(DynArgDescriptor03(arg_type))
        # parse the func_type metadata if it exists
        found = False
        for line in self._ktype.content:
            if isinstance(line, fparser.typedecl_statements.Type):
                for entry in line.selector:
                    if entry == "func_type":
                        if line.entity_decls[0].split()[0].split("(")[0] == \
                                "meta_funcs":
                            found = True
                            break
        if not found:
            func_types = []
        else:
            # use the base class method to extract the information
            func_types = self.getkerneldescriptors(self._ktype,
                                                   var_name="meta_funcs")
        self._func_descriptors = []
        # populate a list of function descriptor objects which we
        # return via the func_descriptors method.
        arg_fs_names = []
        for descriptor in self._arg_descriptors:
            arg_fs_names.append(descriptor.function_space)
        used_fs_names = []
        for func_type in func_types:
            descriptor = DynFuncDescriptor03(func_type)
            fs_name = descriptor.function_space_name
            # check that function space names in meta_funcs are specified in
            # meta_args
            if fs_name not in arg_fs_names:
                raise ParseError(
                    "In the dynamo0.3 API all function spaces specified in "
                    "meta_funcs must exist in meta_args, but '{0}' breaks "
                    "this rule in ...\n'{1}'.".
                    format(fs_name, self._ktype.content))
            if fs_name not in used_fs_names:
                used_fs_names.append(fs_name)
            else:
                raise ParseError(
                    "In the dynamo0.3 API function spaces specified in "
                    "meta_funcs must be unique, but '{0}' is replicated in "
                    "...\n'{1}'.".format(fs_name, self._ktype.content))
            self._func_descriptors.append(descriptor)

    @property
    def func_descriptors(self):
        ''' Returns metadata about the function spaces within a
        Kernel. This metadata is provided within Kernel code via the
        meta_funcs variable. Information is returned as a list of
        DynFuncDescriptor03 objects, one for each function space. '''
        return self._func_descriptors

# Second section : PSy specialisations

# imports
from psyGen import PSy, Invokes, Invoke, Schedule, Loop, Kern, Arguments, \
    Argument, GenerationError, Inf, NameSpaceFactory

# classes


class DynamoPSy(PSy):
    ''' The Dynamo specific PSy class. This creates a Dynamo specific
    invokes object (which controls all the required invocation calls).
    It also overrides the PSy gen method so that we generate dynamo
    specific PSy module code. '''

    def __init__(self, invoke_info):
        PSy.__init__(self, invoke_info)
        self._invokes = DynamoInvokes(invoke_info.calls)

    @property
    def gen(self):
        '''
        Generate PSy code for the Dynamo0.3 api.

        :rtype: ast

        '''
        from f2pygen import ModuleGen, UseGen
        # create an empty PSy layer module
        psy_module = ModuleGen(self.name)
        # include required infrastructure modules
        psy_module.add(UseGen(psy_module, name="field_mod", only=True,
                              funcnames=["field_type", "field_proxy_type"]))
        psy_module.add(UseGen(psy_module, name="operator_mod", only=True,
                              funcnames=["operator_type",
                                         "operator_proxy_type"]))
        psy_module.add(UseGen(psy_module, name="quadrature_mod", only=True,
                              funcnames=["quadrature_type"]))
        psy_module.add(UseGen(psy_module, name="constants_mod", only=True,
                              funcnames=["r_def"]))
        # add all invoke specific information
        self.invokes.gen_code(psy_module)
        # return the generated code
        return psy_module.root


class DynamoInvokes(Invokes):
    ''' The Dynamo specific invokes class. This passes the Dynamo
    specific invoke class to the base class so it creates the one we
    require. '''

    def __init__(self, alg_calls):
        if False:
            self._0_to_n = DynInvoke(None, None)  # for pyreverse
        Invokes.__init__(self, alg_calls, DynInvoke)


class DynInvoke(Invoke):
    ''' The Dynamo specific invoke class. This passes the Dynamo
    specific schedule class to the base class so it creates the one we
    require.  Also overrides the gen_code method so that we generate
    dynamo specific invocation code. '''

    def __init__(self, alg_invocation, idx):
        if False:
            self._schedule = DynSchedule(None)  # for pyreverse
        Invoke.__init__(self, alg_invocation, idx, DynSchedule)
        # check whether we have more than one kernel call within this
        # invoke which specifies any_space. This is not supported at
        # the moment so we raise an error.  any_space with different
        # kernels in an invoke must either inherit the space from the
        # variable (which needs analysis) or have a unique name for
        # the space used by each kernel and at the moment neither of
        # these has been coded for.
        any_space_call_count = 0
        for call in self.schedule.calls():
            found_any_space = False
            for arg_descriptor in call.arg_descriptors:
                if arg_descriptor.is_any_space:
                    found_any_space = True
                    break
            if found_any_space:
                any_space_call_count += 1
        if any_space_call_count > 1:
            raise GenerationError(
                "Error, there are multiple kernels within this invoke with "
                "kernel arguments declared as any_space. This is not yet "
                "supported.")
        # the baseclass works out the algorithms codes unique argument
        # list and stores it in the self._alg_unique_args
        # list. However, the base class currently ignores any qr
        # arguments so we need to add them in.
        self._alg_unique_qr_args = []
        for call in self.schedule.calls():
            if call.qr_required:
                if call.qr_text not in self._alg_unique_qr_args:
                    self._alg_unique_qr_args.append(call.qr_text)
        self._alg_unique_args.extend(self._alg_unique_qr_args)
        # we also need to work out the names to use for the qr
        # arguments within the psy layer. These are stored in the
        # _psy_unique_qr_vars list
        self._psy_unique_qr_vars = []
        for call in self.schedule.calls():
            if call.qr_required:
                if call.qr_name not in self._psy_unique_qr_vars:
                    self._psy_unique_qr_vars.append(call.qr_name)

    @property
    def qr_required(self):
        ''' Returns True if at least one of the kernels in this invoke
        requires QR, otherwise returns False. '''
        required = False
        for call in self.schedule.calls():
            if call.qr_required:
                required = True
                break
        return required

    def unique_declarations(self, datatype, proxy=False):
        ''' Returns a list of all required declarations for the
        specified datatype. If proxy is set to True then the
        equivalent proxy declarations are returned instead. '''
        if datatype not in VALID_ARG_TYPE_NAMES:
            raise GenerationError(
                "unique_declarations called with an invalid datatype. "
                "Expected one of '{0}' but found '{1}'".
                format(str(VALID_ARG_TYPE_NAMES), datatype))
        declarations = []
        for call in self.schedule.calls():
            for arg in call.arguments.args:
                if arg.text is not None:
                    if arg.type == datatype:
                        if proxy:
                            test_name = arg.proxy_declaration_name
                        else:
                            test_name = arg.declaration_name
                        if test_name not in declarations:
                            declarations.append(test_name)
        return declarations

    def arg_for_funcspace(self, fs_name):
        ''' Returns an argument object which is on the requested
        function space. Searches through all Kernel calls in this
        invoke. Currently the first argument object that is found is
        used. Throws an exception if no argument exists. '''
        for kern_call in self.schedule.kern_calls():
            if fs_name in kern_call.arguments.unique_fss:
                for arg in kern_call.arguments.args:
                    if arg.function_space == fs_name:
                        return arg
        raise GenerationError("Functionspace name not found")

    def unique_fss(self):
        ''' Returns the unique function space names over all kernel
        calls in this invoke. '''
        unique_fs_names = []
        for kern_call in self.schedule.kern_calls():
            for fs_name in kern_call.arguments.unique_fss:
                if fs_name not in unique_fs_names:
                    unique_fs_names.append(fs_name)
        return unique_fs_names

    def basis_required(self, func_space):
        ''' Returns true if at least one of the kernels in this invoke
        requires a basis function for this function space, otherwise
        it returns False. '''
        # look in each kernel
        for kern_call in self.schedule.kern_calls():
            # is there a descriptor for this function space?
            if kern_call.fs_descriptors.exists(func_space):
                descriptor = kern_call.fs_descriptors.get_descriptor(
                    func_space)
                # does this descriptor specify that a basis function
                # is required?
                if descriptor.requires_basis:
                    # found a kernel that requires a basis function
                    # for this function space
                    return True
        # none of my kernels require a basis function for this function space
        return False

    def diff_basis_required(self, func_space):
        ''' Returns true if at least one of the kernels in this invoke
        requires a differential basis function for this function
        space, otherwise it returns False.'''
        # look in each kernel
        for kern_call in self.schedule.kern_calls():
            # is there a descriptor for this function space?
            if kern_call.fs_descriptors.exists(func_space):
                descriptor = kern_call.fs_descriptors.get_descriptor(
                    func_space)
                # does this descriptor specify that a basis function
                # is required?
                if descriptor.requires_diff_basis:
                    # found a kernel that requires a diff basis
                    # function for this function space
                    return True
        # none of my kernels require a diff basis function for this
        # function space
        return False

    def ndf_name(self, func_space):
        ''' A convenience method that returns an ndf name for a
        particular function space. These names are specified in
        function_space_descriptors objects contained within Kernel
        objects. The first Kernel in the invoke is used to return the
        name. If no Kernel exist in this invoke an error is thrown. '''
        kern_calls = self.schedule.kern_calls()
        if len(kern_calls) == 0:
            raise GenerationError(
                "ndf_name makes no sense if there are no kernel calls")
        return kern_calls[0].fs_descriptors.ndf_name(func_space)

    def undf_name(self, func_space):
        ''' A convenience method that returns an undf name for a
        particular function space. These names are specified in
        function_space_descriptors objects contained within Kernel
        objects. The first Kernel in the invoke is used to return the
        name. If no Kernel exists in this invoke an error is thrown. '''
        kern_calls = self.schedule.kern_calls()
        if len(kern_calls) == 0:
            raise GenerationError(
                "undf_name makes no sense if there are no kernel calls")
        return kern_calls[0].fs_descriptors.undf_name(func_space)

    def get_operator_name(self, operator_name, function_space):
        ''' A convenience method that returns an operator name for a
        particular operator on a particular function space. These
        names are specified in function_space_descriptors objects
        contained within Kernel objects. The first Kernel which uses
        the specified function space is used to return the name. If no
        Kernel using this function space exists in this invoke, an
        error is thrown. '''
        for kern_call in self.schedule.kern_calls():
            if kern_call.fs_descriptors.exists(function_space):
                descriptor = kern_call.fs_descriptors.get_descriptor(
                    function_space)
                return descriptor.name(operator_name)
        raise GenerationError(
            "Dyn_invoke:get_operator_name: no kern call with function space "
            "'{0}' and operator '{1}'".format(function_space, operator_name))

    def field_on_space(self, func_space):
        ''' Returns true if a field exists on this space for any
        kernel in this invoke. '''
        for kern_call in self.schedule.kern_calls():
            if kern_call.field_on_space(func_space):
                return True
        return False

    def gen_code(self, parent):
        ''' Generates Dynamo specific invocation code (the subroutine
        called by the associated invoke call in the algorithm
        layer). This consists of the PSy invocation subroutine and the
        declaration of its arguments. '''
        from f2pygen import SubroutineGen, TypeDeclGen, AssignGen, DeclGen, \
            AllocateGen, DeallocateGen, CallGen, CommentGen
        # create a namespace manager so we can avoid name clashes
        self._name_space_manager = NameSpaceFactory().create()
        # create the subroutine
        invoke_sub = SubroutineGen(parent, name=self.name,
                                   args=self.psy_unique_var_names +
                                   self._psy_unique_qr_vars)
        # add the subroutine argument declarations fields
        field_declarations = self.unique_declarations("gh_field")
        if len(field_declarations) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype="field_type",
                                       entity_decls=field_declarations,
                                       intent="inout"))
        # operators
        operator_declarations = self.unique_declarations("gh_operator")
        if len(operator_declarations) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype="operator_type",
                                       entity_decls=operator_declarations,
                                       intent="inout"))
        # qr
        if len(self._psy_unique_qr_vars) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype="quadrature_type",
                                       entity_decls=self._psy_unique_qr_vars,
                                       intent="in"))
        # declare and initialise proxies for each of the arguments
        invoke_sub.add(CommentGen(invoke_sub, ""))
        invoke_sub.add(CommentGen(invoke_sub, " Initialise field proxies"))
        invoke_sub.add(CommentGen(invoke_sub, ""))
        for arg in self.psy_unique_vars:
            if arg.vector_size > 1:
                for idx in range(1, arg.vector_size+1):
                    invoke_sub.add(AssignGen(invoke_sub,
                                   lhs=arg.proxy_name+"("+str(idx)+")",
                                   rhs=arg.name+"("+str(idx)+")%get_proxy()"))
            else:
                invoke_sub.add(AssignGen(invoke_sub, lhs=arg.proxy_name,
                                         rhs=arg.name+"%get_proxy()"))

        field_proxy_decs = self.unique_declarations("gh_field", proxy=True)
        if len(field_proxy_decs) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub,
                           datatype="field_proxy_type",
                           entity_decls=field_proxy_decs))
        op_proxy_decs = self.unique_declarations("gh_operator", proxy=True)
        if len(op_proxy_decs) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub,
                           datatype="operator_proxy_type",
                           entity_decls=op_proxy_decs))
        # Initialise the number of layers
        invoke_sub.add(CommentGen(invoke_sub, ""))
        invoke_sub.add(CommentGen(invoke_sub, " Initialise number of layers"))
        invoke_sub.add(CommentGen(invoke_sub, ""))
        # use the first argument
        first_var = self.psy_unique_vars[0]
        # use our namespace manager to create a unique name unless
        # the context and label match and in this case return the
        # previous name
        nlayers_name = self._name_space_manager.create_name(
            root_name="nlayers", context="PSyVars", label="nlayers")
        invoke_sub.add(AssignGen(invoke_sub, lhs=nlayers_name,
                       rhs=first_var.proxy_name_indexed + "%" +
                       first_var.ref_name + "%get_nlayers()"))
        invoke_sub.add(DeclGen(invoke_sub, datatype="integer",
                               entity_decls=[nlayers_name]))
        if self.qr_required:
            # declare and initialise qr values
            invoke_sub.add(CommentGen(invoke_sub, ""))
            invoke_sub.add(CommentGen(invoke_sub, " Initialise qr values"))
            invoke_sub.add(CommentGen(invoke_sub, ""))
            invoke_sub.add(DeclGen(invoke_sub, datatype="integer",
                           entity_decls=["nqp_h", "nqp_v"]))
            invoke_sub.add(DeclGen(invoke_sub, datatype="real", pointer=True,
                           kind="r_def", entity_decls=["xp(:,:) => null()"]))
            decl_list = ["zp(:) => null()", "wh(:) => null()",
                         "wv(:) => null()"]
            invoke_sub.add(DeclGen(invoke_sub, datatype="real", pointer=True,
                           kind="r_def", entity_decls=decl_list))
            if len(self._psy_unique_qr_vars) > 1:
                raise GenerationError(
                    "Oops, not yet coded for multiple qr values")
            qr_var_name = self._psy_unique_qr_vars[0]
            qr_ptr_vars = {"zp": "xqp_v", "xp": "xqp_h", "wh": "wqp_h",
                           "wv": "wqp_v"}
            qr_vars = ["nqp_h", "nqp_v"]
            for qr_var in qr_ptr_vars.keys():
                invoke_sub.add(AssignGen(invoke_sub, pointer=True, lhs=qr_var,
                               rhs=qr_var_name + "%get_" +
                               qr_ptr_vars[qr_var] + "()"))
            for qr_var in qr_vars:
                invoke_sub.add(AssignGen(invoke_sub, lhs=qr_var,
                               rhs=qr_var_name + "%get_" + qr_var + "()"))
        operator_declarations = []
        var_list = []
        var_dim_list = []
        # loop over all function spaces used by the kernels in this invoke
        for function_space in self.unique_fss():
            # Initialise information associated with this function space
            invoke_sub.add(CommentGen(invoke_sub, ""))
            invoke_sub.add(CommentGen(invoke_sub, " Initialise sizes and "
                           "allocate any basis arrays for "+function_space))
            invoke_sub.add(CommentGen(invoke_sub, ""))
            # Find an argument on this space to use to dereference
            arg = self.arg_for_funcspace(function_space)
            name = arg.proxy_name_indexed
            # initialise ndf for this function space and add name to
            # list to declare later
            ndf_name = self.ndf_name(function_space)
            var_list.append(ndf_name)
            invoke_sub.add(AssignGen(invoke_sub, lhs=ndf_name,
                                     rhs=name+"%"+arg.ref_name+"%get_ndf()"))
            # if there is a field on this space then initialise undf
            # for this function space and add name to list to declare
            # later
            if self.field_on_space(function_space):
                undf_name = self.undf_name(function_space)
                var_list.append(undf_name)
                invoke_sub.add(AssignGen(invoke_sub, lhs=undf_name,
                               rhs=name+"%"+arg.ref_name+"%get_undf()"))
            if self.basis_required(function_space):
                # initialise 'dim' variable for this function space
                # and add name to list to declare later
                lhs = "dim_"+function_space
                var_dim_list.append(lhs)
                rhs = name+"%"+arg.ref_name+"%get_dim_space()"
                invoke_sub.add(AssignGen(invoke_sub, lhs=lhs, rhs=rhs))
                # allocate the basis function variable
                alloc_args = "dim_" + function_space + ", " + \
                             self.ndf_name(function_space) + ", nqp_h, nqp_v"
                op_name = self.get_operator_name("gh_basis", function_space)
                invoke_sub.add(AllocateGen(invoke_sub,
                                           op_name+"("+alloc_args+")"))
                # add basis function variable to list to declare later
                operator_declarations.append(op_name+"(:,:,:,:)")
            if self.diff_basis_required(function_space):
                # initialise 'diff_dim' variable for this function
                # space and add name to list to declare later
                lhs = "diff_dim_"+function_space
                var_dim_list.append(lhs)
                rhs = name+"%"+arg.ref_name+"%get_dim_space_diff()"
                invoke_sub.add(AssignGen(invoke_sub, lhs=lhs, rhs=rhs))
                # allocate the diff basis function variable
                alloc_args = "diff_dim_" + function_space + ", " + \
                             self.ndf_name(function_space) + ", nqp_h, nqp_v"
                op_name = self.get_operator_name("gh_diff_basis",
                                                 function_space)
                invoke_sub.add(AllocateGen(invoke_sub,
                                           op_name+"("+alloc_args+")"))
                # add diff basis function variable to list to declare later
                operator_declarations.append(op_name+"(:,:,:,:)")
        if not var_list == []:
            # declare ndf and undf for all function spaces
            invoke_sub.add(DeclGen(invoke_sub, datatype="integer",
                                   entity_decls=var_list))
        if not var_dim_list == []:
            # declare dim and diff_dim for all function spaces
            invoke_sub.add(DeclGen(invoke_sub, datatype="integer",
                                   entity_decls=var_dim_list))
        if not operator_declarations == []:
            # declare the basis function operators
            invoke_sub.add(DeclGen(invoke_sub, datatype="real",
                                   allocatable=True,
                                   kind="r_def",
                                   entity_decls=operator_declarations))
        if self.qr_required:
            # add calls to compute the values of any basis arrays
            invoke_sub.add(CommentGen(invoke_sub, ""))
            invoke_sub.add(CommentGen(invoke_sub, " Compute basis arrays"))
            invoke_sub.add(CommentGen(invoke_sub, ""))
            # only look at function spaces that are used by the
            # kernels in this invoke
            for function_space in self.unique_fss():
                # see if a basis function is needed for this function space
                if self.basis_required(function_space):
                    # Create the argument list
                    args = []
                    op_name = self.get_operator_name("gh_basis",
                                                     function_space)
                    args.append(op_name)
                    args.append(self.ndf_name(function_space))
                    args.extend(["nqp_h", "nqp_v", "xp", "zp"])
                    # find an appropriate field to access
                    arg = self.arg_for_funcspace(function_space)
                    name = arg.proxy_name_indexed
                    # insert the basis array call
                    invoke_sub.add(CallGen(invoke_sub,
                                   name=name + "%" + arg.ref_name +
                                   "%compute_basis_function", args=args))
                if self.diff_basis_required(function_space):
                    # Create the argument list
                    args = []
                    op_name = self.get_operator_name("gh_diff_basis",
                                                     function_space)
                    args.append(op_name)
                    args.append(self.ndf_name(function_space))
                    args.extend(["nqp_h", "nqp_v", "xp", "zp"])
                    # find an appropriate field to access
                    arg = self.arg_for_funcspace(function_space)
                    name = arg.proxy_name_indexed
                    # insert the diff basis array call
                    invoke_sub.add(CallGen(invoke_sub, name=name + "%" +
                                   arg.ref_name +
                                   "%compute_diff_basis_function", args=args))
        invoke_sub.add(CommentGen(invoke_sub, ""))
        invoke_sub.add(CommentGen(invoke_sub, " Call our kernels"))
        invoke_sub.add(CommentGen(invoke_sub, ""))
        # add content from the schedule
        self.schedule.gen_code(invoke_sub)
        if self.qr_required:
            # deallocate all allocated basis function arrays
            invoke_sub.add(CommentGen(invoke_sub, ""))
            invoke_sub.add(CommentGen(invoke_sub, " Deallocate basis arrays"))
            invoke_sub.add(CommentGen(invoke_sub, ""))
            func_space_var_names = []
            # loop over all function spaces used by the kernels in this invoke
            for function_space in self.unique_fss():
                if self.basis_required(function_space):
                    # add the basis array name to the list to use later
                    op_name = self.get_operator_name("gh_basis",
                                                     function_space)
                    func_space_var_names.append(op_name)
                if self.diff_basis_required(function_space):
                    # add the diff_basis array name to the list to use later
                    op_name = self.get_operator_name("gh_diff_basis",
                                                     function_space)
                    func_space_var_names.append(op_name)
            # add the required deallocate call
            invoke_sub.add(DeallocateGen(invoke_sub, func_space_var_names))
        invoke_sub.add(CommentGen(invoke_sub, ""))
        # finally, add me to my parent
        parent.add(invoke_sub)


class DynSchedule(Schedule):
    ''' The Dynamo specific schedule class. This passes the Dynamo
    specific loop and infrastructure classes to the base class so it
    creates the ones we require. '''

    def __init__(self, arg):
        Schedule.__init__(self, DynLoop, DynInf, arg)


class DynLoop(Loop):
    ''' The Dynamo specific Loop class. This passes the Dynamo
    specific loop information to the base class so it creates the one
    we require.  Creates Dynamo specific loop bounds when the code is
    being generated. '''

    def __init__(self, call=None, parent=None):
        Loop.__init__(self, DynInf, DynKern, call=call, parent=parent,
                      valid_loop_types=["colours", "colour"])

    def gen_code(self, parent):
        ''' Work out the appropriate loop bounds and variable name
        depending on the loop type and then call the base class to
        generate the code. '''
        self._start = "1"
        if self._loop_type == "colours":
            self._variable_name = "colour"
            self._stop = "ncolour"
        elif self._loop_type == "colour":
            self._variable_name = "cell"
            self._stop = "ncp_ncolour(colour)"
        else:
            self._variable_name = "cell"
            self._stop = self.field.proxy_name_indexed + "%" + \
                self.field.ref_name + "%get_ncell()"
        Loop.gen_code(self, parent)


class DynInf(Inf):
    ''' A Dynamo 0.3 specific infrastructure call factory. No
    infrastructure calls are supported in Dynamo at the moment so we
    just call the base class (which currently recognises the set()
    infrastructure call). '''

    @staticmethod
    def create(call, parent=None):
        ''' Creates a specific infrastructure call. Currently just calls
            the base class method. '''
        return Inf.create(call, parent)


class DynKern(Kern):
    ''' Stores information about Dynamo Kernels as specified by the
    Kernel metadata and associated algorithm call. Uses this
    information to generate appropriate PSy layer code for the Kernel
    instance or to generate a Kernel stub'''

    def __init__(self):
        if False:
            self._arguments = DynKernelArguments(None, None)  # for pyreverse

    def load(self, call, parent=None):
        ''' sets up kernel information with the call object which is
        created by the parser. This object includes information about
        the invoke call and the associated kernel'''
        self._setup(call.ktype, call.module_name, call.args, parent)

    def load_meta(self, ktype):
        ''' sets up kernel information with the kernel type object
        which is created by the parser. The object includes the
        metadata describing the kernel code '''

        #create a name for each argument
        from parse import Arg
        args=[]
        for idx, descriptor in enumerate(ktype.arg_descriptors):
            args.append(Arg("variable", "field_"+str(idx)))
        args.append(Arg("variable", "qr"))
        self._setup(ktype, "dummy_name", args, None)

    def _setup(self, ktype, module_name, args, parent):
        ''' internal setup of kernel information. Kernel metadata (ktype) is passed separately to invoke metadata (args). This allows us to generate xxx '''
        Kern.__init__(self, DynKernelArguments, ktype, module_name, args, parent, check=False)
        self._func_descriptors = ktype.func_descriptors
        self._fs_descriptors = FSDescriptors(ktype.func_descriptors)
        # dynamo 0.3 api kernels require quadrature rule arguments to be
        # passed in if one or more basis functions are used by the kernel.
        self._qr_required = False
        self._qr_args = ["nqp_h", "nqp_v", "wh", "wv"]
        for descriptor in ktype.func_descriptors:
            if len(descriptor.operator_names) > 0:
                self._qr_required = True
                break
        if args is not None:
            # perform some consistency checks as we have switched these
            # off in the base class
            if self._qr_required:
                # check we have an extra argument in the algorithm call
                if len(ktype.arg_descriptors)+1 != len(args):
                    raise GenerationError(
                        "error: QR is required for kernel '{0}' which means that "
                        "a QR argument must be passed by the algorithm layer. "
                        "Therefore the number of arguments specified in the "
                        "kernel metadata '{1}', must be one less than the number "
                        "of arguments in the algorithm layer. However, I found "
                        "'{2}'".format(ktype.procedure.name,
                                       len(ktype.arg_descriptors),
                                       len(args)))
            else:
                # check we have the same number of arguments in the
                # algorithm call and the kernel metadata
                if len(ktype.arg_descriptors) != len(args):
                    raise GenerationError(
                        "error: QR is not required for kernel '{0}'. Therefore "
                        "the number of arguments specified in the kernel "
                        "metadata '{1}', must equal the number of arguments in "
                        "the algorithm layer. However, I found '{2}'".
                        format(ktype.procedure.name,
                               len(ktype.arg_descriptors), len(args)))
        # if there is a quadrature rule, what is the name of the
        # algorithm argument?
        self._qr_text = ""
        self._qr_name = ""
        if self._qr_required and args is not None:
            qr_arg = args[len(args)-1]
            self._qr_text = qr_arg.text
            self._name_space_manager = NameSpaceFactory().create()
            # use our namespace manager to create a unique name unless
            # the context and label match and in this case return the
            # previous name
            self._qr_name = self._name_space_manager.create_name(
                root_name=qr_arg.varName, context="AlgArgs",
                label=self._qr_text)

    @property
    def fs_descriptors(self):
        ''' Returns a list of function space descriptor objects of
        type FSDescriptor which contain information about the function
        spaces. '''
        return self._fs_descriptors

    @property
    def qr_required(self):
        ''' Returns True if this kernel makes use of a quadrature
        rule, else returns False. '''
        return self._qr_required

    @property
    def qr_text(self):
        ''' Returns the QR argument-text used by the algorithm layer
        in the calling argument list. '''
        return self._qr_text

    @property
    def qr_name(self):
        ''' Returns a Quadrature-rule name for this Kernel. '''
        return self._qr_name

    def local_vars(self):
        ''' Returns the names used by the Kernel that vary from one
        invocation to the next and therefore require privatisation
        when parallelised. '''
        raise GenerationError("DynKern:local_vars is not yet implemented")

    def field_on_space(self, func_space):
        ''' Returns True if a field exists on this space for this kernel. '''
        if func_space in self.arguments.unique_fss:
            for arg in self.arguments.args:
                if arg.function_space == func_space and \
                        arg.type == "gh_field":
                    return True
        return False

    def _create_arg_list(self, parent):
        from f2pygen import DeclGen, AssignGen
        # create the argument list
        arglist = []
        if self._arguments.has_operator:
            # 0.5: provide cell position
            arglist.append("cell")
        # 1: provide mesh height
        arglist.append("nlayers")
        # 2: Provide data associated with fields in the order
        #    specified in the metadata.  If we have a vector field
        #    then generate the appropriate number of arguments.
        for arg in self._arguments.args:
            if arg.type == "gh_field":
                dataref = "%data"
                if arg.vector_size > 1:
                    for idx in range(1, arg.vector_size+1):
                        arglist.append(arg.proxy_name+"("+str(idx)+")"+dataref)
                else:
                    arglist.append(arg.proxy_name+dataref)
            elif arg.type == "gh_operator":
                arglist.append(arg.proxy_name_indexed+"%ncell_3d")
                arglist.append(arg.proxy_name_indexed+"%local_stencil")
            else:
                raise GenerationError(
                    "Unexpected arg type found in "
                    "dynamo0p3.py:DynKern:gen_code(). Expected one of"
                    " [gh_field, gh_operator] but found " + arg.type)
        # 3: For each function space (in the order they appear in the
        # metadata arguments)
        for unique_fs in self.arguments.unique_fss:
            # 3.1 Provide compulsory arguments common to operators and
            # fields on a space
            arglist.extend(self._fs_descriptors.compulsory_args(unique_fs))
            # 3.1.1 Provide additional compulsory arguments if there
            # is a field on this space
            if self.field_on_space(unique_fs):
                arglist.extend(self._fs_descriptors.compulsory_args_field(
                        unique_fs))
            # 3.2 Provide optional arguments
            if self._fs_descriptors.exists(unique_fs):
                descriptor = self._fs_descriptors.get_descriptor(unique_fs)
                arglist.extend(descriptor.operator_names)
            # 3.3 Fix for boundary_dofs array in ru_kernel
            if self.name == "ru_code" and unique_fs == "w2":
                arglist.append("boundary_dofs_w2")
                parent.add(DeclGen(parent, datatype="integer", pointer=True,
                                   entity_decls=[
                            "boundary_dofs_w2(:,:) => null()"]))
                proxy_name = self._arguments.get_field("w2").proxy_name
                new_parent, position = parent.start_parent_loop()
                new_parent.add(AssignGen(new_parent, pointer=True,
                                         lhs="boundary_dofs_w2",
                                         rhs=proxy_name +
                                         "%vspace%get_boundary_dofs()"),
                               position=["before", position])
        # 4: Provide qr arguments if required
        if self._qr_required:
            arglist.extend(self._qr_args)
        return arglist

    @property
    def gen_stub(self):
        ''' output a kernel stub '''
        from f2pygen import ModuleGen, SubroutineGen
        # create an empty PSy layer module
        psy_module = ModuleGen(self.name+"_mod")

        arglist = self._create_arg_list(psy_module)
        # create the subroutine
        sub_stub = SubroutineGen(psy_module, name=self.name+"_code",
                                   args=arglist)
        psy_module.add(sub_stub)
        return psy_module.root

    def gen_code(self, parent):
        ''' Generates dynamo version 0.3 specific psy code for a call to
            the dynamo kernel instance. '''
        from f2pygen import CallGen, DeclGen, AssignGen, UseGen, CommentGen, \
            IfThenGen
        parent.add(DeclGen(parent, datatype="integer",
                           entity_decls=["cell"]))
        # create a maps_required logical which we can use to add in
        # spacer comments if necessary
        maps_required = False
        for unique_fs in self.arguments.unique_fss:
            if self.field_on_space(unique_fs):
                maps_required = True
        # function-space maps initialisation and their declarations
        if maps_required:
            parent.add(CommentGen(parent, ""))
        for unique_fs in self.arguments.unique_fss:
            if self.field_on_space(unique_fs):
                # A map is required as there is a field on this space
                map_name = self._fs_descriptors.map_name(unique_fs)
                field = self._arguments.get_field(unique_fs)
                parent.add(AssignGen(parent, pointer=True, lhs=map_name,
                                     rhs=field.proxy_name_indexed +
                                     "%" + field.ref_name +
                                     "%get_cell_dofmap(cell)"))
        if maps_required:
            parent.add(CommentGen(parent, ""))
        decl_map_names = []
        for unique_fs in self.arguments.unique_fss:
            if self.field_on_space(unique_fs):
                # A map is required as there is a field on this space
                map_name = self._fs_descriptors.map_name(unique_fs)
                decl_map_names.append(map_name+"(:) => null()")
        if len(decl_map_names) > 0:
            parent.add(DeclGen(parent, datatype="integer", pointer=True,
                               entity_decls=decl_map_names))
        # orientation arrays initialisation and their declarations
        for unique_fs in self.arguments.unique_fss:
            if self._fs_descriptors.exists(unique_fs):
                fs_descriptor = self._fs_descriptors.get_descriptor(unique_fs)
                if fs_descriptor.orientation:
                    field = self._arguments.get_field(unique_fs)
                    parent.add(AssignGen(parent, pointer=True,
                               lhs=fs_descriptor.orientation_name,
                               rhs=field.proxy_name_indexed + "%" +
                                         field.ref_name +
                                         "%get_cell_orientation(cell)"))
        if self._fs_descriptors.orientation:
            orientation_decl_names = []
            for orientation_name in self._fs_descriptors.orientation_names:
                orientation_decl_names.append(orientation_name +
                                              "(:) => null()")
            parent.add(DeclGen(parent, datatype="integer", pointer=True,
                               entity_decls=orientation_decl_names))
            parent.add(CommentGen(parent, ""))

        arglist = self._create_arg_list(parent)

        # generate the kernel call and associated use statement
        parent.add(CallGen(parent, self._name, arglist))
        parent.parent.add(UseGen(parent.parent, name=self._module_name,
                                 only=True, funcnames=[self._name]))
        # 5: Fix for boundary_dofs array in matrix_vector_mm_code
        if self.name == "matrix_vector_mm_code":
            # In matrix_vector_mm_code, all fields are on the same
            # (unknown) space. Therefore we can use any field to
            # dereference. We choose the 2nd one as that is what is
            # done in the manual implementation.
            reference_arg = self.arguments.args[1]
            enforce_bc_arg = self.arguments.args[0]
            space_name = "w2"
            kern_func_space_name = enforce_bc_arg.function_space
            ndf_name = self.fs_descriptors.ndf_name(kern_func_space_name)
            undf_name = self.fs_descriptors.undf_name(kern_func_space_name)
            map_name = self.fs_descriptors.map_name(kern_func_space_name)
            w2_proxy_name = reference_arg.proxy_name
            self._name_space_manager = NameSpaceFactory().create()
            fs_name = self._name_space_manager.create_name(root_name="fs")
            boundary_dofs_name = self._name_space_manager.create_name(
                root_name="boundary_dofs_"+space_name)
            parent.add(UseGen(parent, name="function_space_mod",
                              only=True, funcnames=[space_name]))
            parent.add(DeclGen(parent, datatype="integer", pointer=True,
                               entity_decls=[boundary_dofs_name +
                                             "(:,:) => null()"]))
            parent.add(DeclGen(parent, datatype="integer",
                               entity_decls=[fs_name]))
            new_parent, position = parent.start_parent_loop()
            new_parent.add(AssignGen(new_parent, lhs=fs_name,
                                     rhs=reference_arg.name +
                                     "%which_function_space()"),
                           position=["before", position])
            if_then = IfThenGen(new_parent, fs_name+" .eq. "+space_name)
            new_parent.add(if_then, position=["before", position])
            if_then.add(AssignGen(if_then, pointer=True,
                                  lhs=boundary_dofs_name,
                                  rhs=w2_proxy_name +
                                  "%vspace%get_boundary_dofs()"))
            parent.add(CommentGen(parent, ""))
            if_then = IfThenGen(parent, fs_name+" .eq. "+space_name)
            parent.add(if_then)
            nlayers_name = self._name_space_manager.create_name(
                root_name="nlayers", context="PSyVars", label="nlayers")
            parent.add(UseGen(parent, name="enforce_bc_mod", only=True,
                              funcnames=["enforce_bc_w2"]))
            if_then.add(CallGen(if_then, "enforce_bc_w2",
                                [nlayers_name, ndf_name, undf_name,
                                 map_name, boundary_dofs_name,
                                 enforce_bc_arg.proxy_name+"%data"]))
            parent.add(CommentGen(parent, ""))


class FSDescriptor(object):
    ''' Provides information about a particular function space. '''

    def __init__(self, descriptor):
        self._descriptor = descriptor

    @property
    def requires_basis(self):
        ''' Returns True if a basis function is associated with this
        function space, otherwise it returns False. '''
        if "gh_basis" in self._descriptor.operator_names:
            return True
        else:
            return False

    @property
    def requires_diff_basis(self):
        ''' Returns True if a differential basis function is
        associated with this function space, otherwise it returns
        False. '''
        if "gh_diff_basis" in self._descriptor.operator_names:
            return True
        else:
            return False

    @property
    def operator_names(self):
        ''' Returns a list of the names of the operators associated
        with this function space. The names are unique to the function
        space, they are not the raw metadata values. '''
        names = []
        for operator_name in self._descriptor.operator_names:
            if operator_name == "gh_orientation":
                names.append(self.orientation_name)
            elif operator_name == "gh_basis":
                names.append(self.basis_name)
            elif operator_name == "gh_diff_basis":
                names.append(self.diff_basis_name)
            else:
                raise GenerationError(
                    "FSDescriptor:operator_names: unsupported name '{0}' "
                    "found".format(operator_name))
        return names

    def name(self, operator_name):
        ''' Returns the names of the specified operator for this
        function space. The name is unique to the function space, it
        is not the raw metadata value. '''
        if operator_name == "gh_orientation":
            return self.orientation_name
        elif operator_name == "gh_basis":
            return self.basis_name
        elif operator_name == "gh_diff_basis":
            return self.diff_basis_name
        else:
            raise GenerationError("FSDescriptor:name: unsupported name '{0}'"
                                  " found".format(operator_name))

    @property
    def basis_name(self):
        ''' Returns a name for the basis function on this function
        space. The name is unique to the function space, it is not the
        raw metadata value. '''

        return "basis"+"_"+self._descriptor.function_space_name

    @property
    def diff_basis_name(self):
        ''' Returns a name for the differential basis function on this
        function space. The name is unique to the function space, it
        is not the raw metadata value. '''
        return "diff_basis"+"_"+self._descriptor.function_space_name

    @property
    def fs_name(self):
        ''' Returns the raw metadata value of this function space. '''
        return self._descriptor.function_space_name

    @property
    def orientation_name(self):
        ''' Returns a name for orientation on this function space. The
        name is unique to the function space, it is not the raw
        metadata value. '''
        for operator_name in self._descriptor.operator_names:
            if operator_name == "gh_orientation":
                return "orientation"+"_"+self._descriptor.function_space_name
        raise GenerationError(
            "Internal logic error: FS-Descriptor:orientation_name: This "
            "descriptor has no orientation so can not have a name")

    @property
    def orientation(self):
        ''' Returns True if orientation is associated with this
        function space, otherwise it returns False. '''
        for operator_name in self._descriptor.operator_names:
            if operator_name == "gh_orientation":
                return True
        return False


class FSDescriptors(object):
    ''' Contains a collection of FSDescriptor objects and methods
    that provide information across these objects. '''

    def __init__(self, descriptors):
        self._orig_descriptors = descriptors
        self._descriptors = []
        for descriptor in descriptors:
            self._descriptors.append(FSDescriptor(descriptor))

    def compulsory_args(self, func_space):
        ''' Args that all fields and operators require for the
        specified function space. '''
        return [self.ndf_name(func_space)]

    def compulsory_args_field(self, func_space):
        ''' Args that a field requires for the specified function
        space in addition to the compulsory args. '''
        return [self.undf_name(func_space), self.map_name(func_space)]

    def ndf_name(self, func_space):
        ''' Returns a ndf name for this function space. '''
        return "ndf_"+func_space

    def undf_name(self, func_space):
        ''' Returns a undf name for this function space. '''
        return "undf_"+func_space

    def map_name(self, func_space):
        ''' Returns a dofmap name for this function space. '''
        return "map_"+func_space

    @property
    def orientation(self):
        ''' Return True if at least one descriptor specifies
        orientation, otherwise return False. '''
        for descriptor in self._descriptors:
            if descriptor.orientation:
                return True
        return False

    @property
    def orientation_names(self):
        ''' Returns a list of all orientation names used in this
        objects collection of FSDescriptor objects. '''
        names = []
        for descriptor in self._descriptors:
            if descriptor.orientation:
                names.append(descriptor.orientation_name)
        return names

    def exists(self, fs_name):
        ''' Return True if a descriptor with the specified function
        space name exists, otherwise return False. '''
        for descriptor in self._descriptors:
            if descriptor.fs_name == fs_name:
                return True
        return False

    def get_descriptor(self, fs_name):
        ''' Return the descriptor with the specified function space
        name. If it does not exist raise an error.'''
        for descriptor in self._descriptors:
            if descriptor.fs_name == fs_name:
                return descriptor
        raise GenerationError(
            "FSDescriptors:get_descriptor: there is no descriptor for "
            "function space {0}".format(fs_name))


class DynKernelArguments(Arguments):
    ''' Provides information about Dynamo kernel call arguments
    collectively, as specified by the kernel argument metadata. '''

    def __init__(self, ktype, args, parent_call):
        if False:  # for pyreverse
            self._0_to_n = DynKernelArgument(None, None, None)
        Arguments.__init__(self, parent_call)
        if args is None:
            self._args = None # we may have no algorithm argument information
        else:
            self._args = []
            for (idx, arg) in enumerate(ktype.arg_descriptors):
                self._args.append(DynKernelArgument(arg, args[idx], parent_call))
        self._dofs = []

    def get_field(self, func_space):
        ''' Returns the first field found that is on the specified
        function space. If no field is found an exception is raised. '''
        for arg in self._args:
            if arg.function_space == func_space:
                return arg
        raise GenerationError("DynKernelArguments:get_field: there is no"
                              " field with function space {0)".
                              format(func_space))

    @property
    def has_operator(self):
        ''' Returns true if at least one of the arguments is an operator. '''
        for arg in self._args:
            if arg.type == "gh_operator":
                return True
        return False

    @property
    def unique_fss(self):
        ''' Returns a unique list of function spaces used by the
        arguments. '''
        func_space = []
        for arg in self._args:
            if arg.function_space not in func_space:
                func_space.append(arg.function_space)
        return func_space

    def iteration_space_arg(self, mapping=None):
        ''' Returns the first argument that is written to. This can be
        used to dereference for the iteration space. '''
        if mapping is not None:
            my_mapping = mapping
        else:
            my_mapping = {"write": "gh_write", "read": "gh_read",
                          "readwrite": "gh_rw", "inc": "gh_inc"}
        arg = Arguments.iteration_space_arg(self, my_mapping)
        return arg

    @property
    def dofs(self):
        ''' Currently required for invoke base class although this
        makes no sense for dynamo. Need to refactor the invoke class
        and pull out dofs into the gunghoproto api. '''
        return self._dofs


class DynKernelArgument(Argument):
    ''' Provides information about individual Dynamo kernel call
    arguments as specified by the kernel argument metadata. '''

    def __init__(self, arg, arg_info, call):
        self._arg = arg
        Argument.__init__(self, call, arg_info, arg.access)
        self._vector_size = arg.vector_size
        self._type = arg.type

    @property
    def ref_name(self):
        ''' Returns the name used to dereference this type of argument. '''
        if self._type == "gh_field":
            return "vspace"
        elif self._type == "gh_operator":
            return "fs_from"
        else:
            raise GenerationError(
                "ref_name: Error, unsupported arg type '{0}' found".
                format(self._type))

    @property
    def type(self):
        ''' Returns the type of this argument. '''
        return self._type

    @property
    def vector_size(self):
        ''' Returns the vector size of this argument as specified in
        the Kernel metadata. '''
        return self._vector_size

    @property
    def proxy_name(self):
        ''' Returns the proxy name for this argument. '''
        return self._name+"_proxy"

    @property
    def proxy_declaration_name(self):
        ''' Returns the proxy name for this argument with the array
        dimensions added if required. '''
        if self._vector_size > 1:
            return self.proxy_name+"("+str(self._vector_size)+")"
        else:
            return self.proxy_name

    @property
    def declaration_name(self):
        ''' Returns the name for this argument with the array
        dimensions added if required. '''
        if self._vector_size > 1:
            return self._name+"("+str(self._vector_size)+")"
        else:
            return self._name

    @property
    def proxy_name_indexed(self):
        ''' Returns the proxy name for this argument with an
        additional index which accesses the first element for a vector
        argument. '''
        if self._vector_size > 1:
            return self._name+"_proxy(1)"
        else:
            return self._name+"_proxy"

    @property
    def function_space(self):
        ''' Returns the expected finite element function space for this
            argument as specified by the kernel argument metadata. '''
        return self._arg.function_space
