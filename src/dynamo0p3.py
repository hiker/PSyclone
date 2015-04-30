#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2014.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

''' This module implements the PSyclone Dynamo 0.3 API by specialising the
    required base classes (PSy, Invokes, Invoke, Schedule, Loop, Kern,
    Inf, Arguments and Argument). '''

from psyGen import PSy, Invokes, Invoke, Schedule, Loop, Kern, Arguments, \
                   Argument, GenerationError, Inf, NameSpaceFactory

class DynamoPSy(PSy):
    ''' The Dynamo specific PSy class. This creates a Dynamo specific
        invokes object (which controls all the required invocation calls).
        Also overrides the PSy gen method so that we generate dynamo
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
        psy_module.add(UseGen(psy_module, name = "field_mod", only=True, funcnames=["field_type", "field_proxy_type"]))
        psy_module.add(UseGen(psy_module, name = "operator_mod", only=True, funcnames=["operator_type", "operator_proxy_type"]))
        psy_module.add(UseGen(psy_module, name = "quadrature_mod", only=True, funcnames=["quadrature_type"]))
        psy_module.add(UseGen(psy_module, name = "constants_mod", only=True, funcnames=["r_def"]))
        # add all invoke specific information
        self.invokes.gen_code(psy_module)
        return psy_module.root

class DynamoInvokes(Invokes):
    ''' The Dynamo specific invokes class. This passes the Dynamo specific
        invoke class to the base class so it creates the one we require. '''
    def __init__(self, alg_calls):
        if False:
            self._0_to_n = DynInvoke(None, None) # for pyreverse
        Invokes.__init__(self, alg_calls, DynInvoke)

class DynInvoke(Invoke):
    ''' The Dynamo specific invoke class. This passes the Dynamo specific
        schedule class to the base class so it creates the one we require.
        Also overrides the gen_code method so that we generate dynamo
        specific invocation code. '''
    def __init__(self, alg_invocation, idx):
        if False:
            self._schedule = DynSchedule(None) # for pyreverse
        Invoke.__init__(self, alg_invocation, idx, DynSchedule)
        # determine the number of qr arguments required and make sure the names are unique
        self._alg_unique_qr_args = []
        self._psy_unique_qr_vars = []
        self._qr_required = False
        for call in self.schedule.calls():
            if call.qr_required:
                self._qr_required = True
                if not call.qr_text in self._alg_unique_qr_args:
                    self._alg_unique_qr_args.append(call.qr_text)
                if not call.qr_name in self._psy_unique_qr_vars:
                    self._psy_unique_qr_vars.append(call.qr_name)
        self._alg_unique_args.extend(self._alg_unique_qr_args)
        # this api supports vector fields so we need to declare and use them
        # correctly in the psy layer.
        self._psy_unique_declarations = []
        self._psy_unique_operator_declarations = []
        self._psy_proxy_unique_declarations = []
        self._psy_proxy_unique_operator_declarations = []
        self._psy_field_info = {}
        self._proxy_name = {}
        for call in self.schedule.calls():
            for arg in call.arguments.args:
                if arg.text is not None:
                    if arg.type == "gh_operator":
                        if not arg.name in self._psy_unique_operator_declarations:
                            self._psy_unique_operator_declarations.append(arg.name)
                            self._psy_field_info[arg.name] = arg
                            self._proxy_name[arg.name] = arg.name+"_proxy"
                            tmp_name_proxy = arg.name+"_proxy"
                            self._psy_proxy_unique_operator_declarations.append(tmp_name_proxy)
                    elif arg.type == "gh_field":
                        if not arg.name in self._psy_unique_declarations:
                            if arg.vector_size>1:
                                tmp_name = arg.name+"("+str(arg.vector_size)+")"
                                tmp_name_proxy = arg.name+"_proxy("+str(arg.vector_size)+")"
                            else:
                                tmp_name = arg.name
                                tmp_name_proxy = arg.name+"_proxy"
                            self._psy_unique_declarations.append(tmp_name)
                            self._psy_proxy_unique_declarations.append(tmp_name_proxy)
                            self._psy_field_info[arg.name] = arg
                            self._proxy_name[arg.name] = arg.name+"_proxy"
                    else:
                        raise GenerationError("Usupported arg type '{0}' found ".format(arg.type))

    def arg_for_funcspace(self,fs_name):
        for kern_call in self.schedule.kern_calls():
            if fs_name in kern_call.arguments.unique_fss:
                for arg in kern_call.arguments.args:
                    if arg.function_space == fs_name:
                        return arg
        raise ParserError("Functionspace name not found")

    def unique_fss(self):
        ''' returns the unique function space names over all kernel calls in this invoke '''
        unique_fs_names=[]
        for kern_call in self.schedule.kern_calls():
            for fs in kern_call.arguments.unique_fss:
                if fs not in unique_fs_names:
                    unique_fs_names.append(fs)
        return unique_fs_names

    def basis_required(self,fs):
        '''Returns true if at least one of the kernels in this invoke requires a basis function for this function space, otherwise it returns False.'''
        # look in each kernel
        for kern_call in self.schedule.kern_calls():
            # is there a descriptor for this function space?
            if kern_call._fs_descriptors.exists(fs):
                descriptor = kern_call._fs_descriptors.get_descriptor(fs)
                # does this descriptor specify that a basis function is required?
                if descriptor.requires_basis:
                    # found a kernel that requires a basis function for this function space
                    return True
        # none of my kernels require a basis function for this function space
        return False

    def diff_basis_required(self,fs):
        '''Returns true if at least one of the kernels in this invoke requires a basis function for this function space, otherwise it returns False.'''
        # look in each kernel
        for kern_call in self.schedule.kern_calls():
            # is there a descriptor for this function space?
            if kern_call._fs_descriptors.exists(fs):
                descriptor = kern_call._fs_descriptors.get_descriptor(fs)
                # does this descriptor specify that a basis function is required?
                if descriptor.requires_diff_basis:
                    # found a kernel that requires a diff basis function for this function space
                    return True
        # none of my kernels require a diff basis function for this function space
        return False

    def ndf_name(self,fs):
        kern_calls = self.schedule.kern_calls()
        if len(kern_calls)==0:
            raise GenerationError("ndf_name makes no sense if there are no kernel calls")
        return kern_calls[0]._fs_descriptors.ndf_name(fs)

    def undf_name(self,fs):
        kern_calls = self.schedule.kern_calls()
        if len(kern_calls)==0:
            raise GenerationError("undf_name makes no sense if there are no kernel calls")
        return kern_calls[0]._fs_descriptors.undf_name(fs)

    def get_operator_name(self, operator_name, function_space):
        for kern_call in self.schedule.kern_calls():
            if kern_call._fs_descriptors.exists(function_space):
                descriptor = kern_call._fs_descriptors.get_descriptor(function_space)
                return descriptor.name(operator_name)
        raise GenerationError("Dyn_invoke:get_operator_name: no kern call with function space '{0}' and operator '{1}'".format(function_space,operator_name))

    def field_on_space(self,fs):
        ''' returns true if a field exists on this space for any
        kernel in this invoke.'''
        for kern_call in self.schedule.kern_calls():
            if kern_call.field_on_space(fs):
                return True
        return False

    def gen_code(self, parent):
        ''' Generates Dynamo specific invocation code (the subroutine called
            by the associated invoke call in the algorithm layer). This
            consists of the PSy invocation subroutine and the declaration of
            its arguments.'''
        from f2pygen import SubroutineGen, TypeDeclGen, AssignGen, DeclGen, AllocateGen, DeallocateGen, CallGen, CommentGen
        # create the subroutine
        invoke_sub = SubroutineGen(parent, name = self.name,
                                   args = self.psy_unique_var_names+self._psy_unique_qr_vars)

        # add the subroutine argument declarations
        # fields
        if len(self._psy_unique_declarations) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "field_type",
                                       entity_decls = self._psy_unique_declarations,
                                       intent = "inout"))
        # operators
        if len(self._psy_unique_operator_declarations) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "operator_type",
                                       entity_decls = self._psy_unique_operator_declarations,
                                       intent = "inout"))
        # qr
        if len(self._psy_unique_qr_vars) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "quadrature_type",
                                      entity_decls = self._psy_unique_qr_vars,
                                      intent = "in"))
        # declare and initialise proxies for each of the arguments
        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(CommentGen(invoke_sub," Initialise field proxies"))
        invoke_sub.add(CommentGen(invoke_sub,""))
        
        for arg in self.psy_unique_vars:
            if arg.vector_size>1:
                for idx in range(1,arg.vector_size+1):
                    invoke_sub.add(AssignGen(invoke_sub, lhs = arg.proxy_name+"("+str(idx)+")",
                                             rhs = arg.name+"("+str(idx)+")"+"%get_proxy()"))
            else:
                invoke_sub.add(AssignGen(invoke_sub, lhs = arg.proxy_name,
                                         rhs = arg.name+"%get_proxy()"))

        if len(self._psy_proxy_unique_declarations)>0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "field_proxy_type",
                                       entity_decls = self._psy_proxy_unique_declarations))
        if len(self._psy_proxy_unique_operator_declarations)>0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "operator_proxy_type",
                                       entity_decls = self._psy_proxy_unique_operator_declarations))

        # Initialise the number of layers
        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(CommentGen(invoke_sub," Initialise number of layers"))
        invoke_sub.add(CommentGen(invoke_sub,""))
        # use the first argument
        first_var = self.psy_unique_vars[0]
        invoke_sub.add(AssignGen(invoke_sub, lhs="nlayers", rhs=first_var.proxy_name_indexed+"%"+first_var.ref_name+"%get_nlayers()"))
        invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                               entity_decls = ["nlayers"]))

        if self._qr_required:
            # declare and initialise qr values
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Initialise qr values"))
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                               entity_decls = ["nqp_h","nqp_v"]))
            invoke_sub.add(DeclGen(invoke_sub, datatype = "real", pointer=True,
                               kind="r_def",entity_decls = ["xp(:,:) => null()"]))
            decl_list=["zp(:) => null()","wh(:) => null()","wv(:) => null()"]
            invoke_sub.add(DeclGen(invoke_sub, datatype = "real", pointer=True,
                               kind="r_def",entity_decls = decl_list))
            if len(self._psy_unique_qr_vars)>1:
                raise GenerationError("Oops, not yet coded for multiple qr values")
            qr_var_name = self._psy_unique_qr_vars[0]
            qr_ptr_vars = {"zp":"xqp_v","xp":"xqp_h","wh":"wqp_h","wv":"wqp_v"}
            qr_vars = ["nqp_h", "nqp_v"]
            for qr_var in qr_ptr_vars.keys():
                invoke_sub.add(AssignGen(invoke_sub, pointer=True, lhs=qr_var, rhs=qr_var_name+"%get_"+qr_ptr_vars[qr_var]+"()"))

            for qr_var in qr_vars:
                invoke_sub.add(AssignGen(invoke_sub, lhs=qr_var, rhs=qr_var_name+"%get_"+qr_var+"()"))

        operator_declarations = []
        var_list = []
        var_dim_list = []
        # loop over all function spaces used by the kernels in this invoke
        for function_space in self.unique_fss():
            # Initialise information associated with this function space
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Initialise sizes and allocate any basis arrays for "+function_space))
            invoke_sub.add(CommentGen(invoke_sub,""))

            # Find an argument on this space to use to dereference
            arg = self.arg_for_funcspace(function_space)
            name = arg.proxy_name_indexed

            # initialise ndf for this function space and add name to list to declare later
            ndf_name = self.ndf_name(function_space)
            var_list.append(ndf_name)
            invoke_sub.add(AssignGen(invoke_sub, lhs = ndf_name,
                                         rhs = name+"%"+arg.ref_name+"%get_ndf()"))

            # if there is a field on this space then initialise undf for this function space and add name to list to declare later
            if self.field_on_space(function_space):
                undf_name = self.undf_name(function_space)
                var_list.append(undf_name)
                invoke_sub.add(AssignGen(invoke_sub, lhs = undf_name,
                                         rhs = name+"%"+arg.ref_name+"%get_undf()"))

            if self.basis_required(function_space):
                # initialise 'dim' variable for this function space and add name to list to declare later
                lhs = "dim_"+function_space
                var_dim_list.append(lhs)
                rhs = name+"%"+arg.ref_name+"%get_dim_space()"
                invoke_sub.add(AssignGen(invoke_sub, lhs=lhs, rhs=rhs))
                # allocate the basis function variable
                alloc_args = "dim_"+function_space+", "+self.ndf_name(function_space)+", nqp_h, nqp_v"
                op_name = self.get_operator_name("gh_basis", function_space)
                invoke_sub.add(AllocateGen(invoke_sub,op_name+"("+alloc_args+")"))

                # add basis function variable to list to declare later
                operator_declarations.append(op_name+"(:,:,:,:)")

            if self.diff_basis_required(function_space):
                # initialise 'diff_dim' variable for this function space and add name to list to declare later
                lhs = "diff_dim_"+function_space
                var_dim_list.append(lhs)
                rhs = name+"%"+arg.ref_name+"%get_dim_space_diff()"
                invoke_sub.add(AssignGen(invoke_sub, lhs=lhs, rhs=rhs))
                # allocate the diff basis function variable
                alloc_args = "diff_dim_"+function_space+", "+self.ndf_name(function_space)+", nqp_h, nqp_v"
                op_name = self.get_operator_name("gh_diff_basis", function_space)
                invoke_sub.add(AllocateGen(invoke_sub,op_name+"("+alloc_args+")"))

                # add diff basis function variable to list to declare later
                operator_declarations.append(op_name+"(:,:,:,:)")

        if not var_list == []:
            # declare ndf and undf for all function spaces
            invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                                   entity_decls = var_list))
            
        if not var_dim_list == []:
            # declare dim and diff_dim for all function spaces
            invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                                   entity_decls = var_dim_list))

        if not operator_declarations == []:
            # declare the basis function operators
            invoke_sub.add(DeclGen(invoke_sub, datatype = "real", allocatable = True,
                                   kind = "r_def", entity_decls = operator_declarations))

        if self._qr_required:
            # add calls to compute the values of any basis arrays
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Compute basis arrays"))
            invoke_sub.add(CommentGen(invoke_sub,""))
            # only look at function spaces that are used by the kernels in this invoke
            for function_space in self.unique_fss():
                # see if a basis function is needed for this function space
                if self.basis_required(function_space):
                    # Create the argument list
                    args=[]
                    op_name = self.get_operator_name("gh_basis", function_space)
                    args.append(op_name)
                    args.append(self.ndf_name(function_space))
                    args.extend(["nqp_h","nqp_v","xp","zp"])
                    # find an appropriate field to access
                    arg = self.arg_for_funcspace(function_space)
                    name = arg.proxy_name_indexed
                    # insert the basis array call
                    invoke_sub.add(CallGen(invoke_sub,name=name+"%"+arg.ref_name+"%compute_basis_function",args=args))
                if self.diff_basis_required(function_space):
                    # Create the argument list
                    args=[]
                    op_name = self.get_operator_name("gh_diff_basis", function_space)
                    args.append(op_name)
                    args.append(self.ndf_name(function_space))
                    args.extend(["nqp_h","nqp_v","xp","zp"])
                    # find an appropriate field to access
                    arg = self.arg_for_funcspace(function_space)
                    name = arg.proxy_name_indexed
                    # insert the diff basis array call
                    invoke_sub.add(CallGen(invoke_sub,name=name+"%"+arg.ref_name+"%compute_diff_basis_function",args=args))

        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(CommentGen(invoke_sub," Call our kernels"))
        invoke_sub.add(CommentGen(invoke_sub,""))
        # add content from the schedule
        self.schedule.gen_code(invoke_sub)

        if self._qr_required:
            # deallocate all allocated basis function arrays
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Deallocate basis arrays"))
            invoke_sub.add(CommentGen(invoke_sub,""))
            
            func_space_var_names=[]
            # loop over all function spaces used by the kernels in this invoke
            for function_space in self.unique_fss():
                if self.basis_required(function_space):
                    # add the basis array name to the list to use later
                    op_name = self.get_operator_name("gh_basis", function_space)
                    func_space_var_names.append(op_name)
                if self.diff_basis_required(function_space):
                    # add the diff_basis array name to the list to use later
                    op_name = self.get_operator_name("gh_diff_basis", function_space)
                    func_space_var_names.append(op_name)
            # add the required deallocate call
            invoke_sub.add(DeallocateGen(invoke_sub,func_space_var_names))
        invoke_sub.add(CommentGen(invoke_sub,""))

        # finally, add me to my parent
        parent.add(invoke_sub)


class DynSchedule(Schedule):
    ''' The Dynamo specific schedule class. This passes the Dynamo specific
        loop and infrastructure classes to the base class so it creates the
        ones we require. '''
    def __init__(self, arg):
        pass
        Schedule.__init__(self, DynLoop, DynInf, arg)

class DynLoop(Loop):
    ''' The Dynamo specific Loop class. This passes the Dynamo specific
        loop information to the base class so it creates the one we require.
        Creates Dynamo specific loop bounds when the code is being generated.
    '''
    def __init__(self, call = None, parent = None):
        Loop.__init__(self, DynInf, DynKern, call = call, parent = parent,
                      valid_loop_types = ["colours", "colour"])
    def gen_code(self,parent):
        ''' Work out the appropriate loop bounds and variable name depending
            on the loop type and then call the base class to generate the
            code '''
        self._start = "1"
        if self._loop_type == "colours":
            self._variable_name = "colour"
            self._stop = "ncolour"
        elif self._loop_type == "colour":
            self._variable_name = "cell"
            self._stop = "ncp_ncolour(colour)"
        else:
            self._variable_name = "cell"
            self._stop = self.field.name+"_proxy%"+self.field.ref_name+"%get_ncell()"
        Loop.gen_code(self,parent)

class DynInf(Inf):
    ''' A Dynamo 0.3 specific infrastructure call factory. No infrastructure
        calls are supported in Dynamo at the moment so we just call the base
        class (which currently recognises the set() infrastructure call). '''
    @staticmethod
    def create(call, parent = None):
        ''' Creates a specific infrastructure call. Currently just calls
            the base class method. '''
        return(Inf.create(call, parent))

class DynKern(Kern):
    ''' Stores information about Dynamo Kernels as specified by the Kernel
        metadata. Uses this information to generate appropriate PSy layer
        code for the Kernel instance. '''
    def __init__(self, call, parent = None):
        if False:
            self._arguments = DynKernelArguments(None, None) # for pyreverse
        Kern.__init__(self, DynKernelArguments, call, parent, check=False)
        self._func_descriptors = call.ktype.func_descriptors
        self._fs_descriptors=FS_Descriptors(call.ktype.func_descriptors)
        # dynamo 0.3 api kernels require quadrature rule arguments to be
        # passed in if one or more basis functions are used by the kernel.
        self._qr_required = False
        self._qr_args = ["nqp_h","nqp_v","wh","wv"]
        for descriptor in call.ktype.func_descriptors:
            if len(descriptor.operator_names)>0:
                self._qr_required=True
                break

        # perform some consistency checks as we have switched these off in the base class
        if self._qr_required:
            # check we have an extra argument in the algorithm call
            if len(call.ktype.arg_descriptors)+1 !=  len(call.args):
                raise GenerationError("error: QR is required for kernel '{0}' which means that a QR argument must be passed by the algorithm layer. Therefore the number of arguments specified in the kernel metadata '{1}', must be one less than the number of arguments in the algorithm layer. However, I found '{2}'".format(call.ktype.procedure.name, len(call.ktype.arg_descriptors), len(call.args)))
        else:
            # check we have the same number of arguments in the algorithm call and the kernel metadata
            if len(call.ktype.arg_descriptors) !=  len(call.args):
                raise GenerationError("error: QR is not required for kernel '{0}'. Therefore the number of arguments specified in the kernel metadata '{1}', must equal the number of arguments in the algorithm layer. However, I found '{2}'".format(call.ktype.procedure.name, len(call.ktype.arg_descriptors), len(call.args)))

        # if there is a quadrature rule, what is the name of the algorithm argument?
        self._qr_text=""
        self._qr_name=""
        if self._qr_required:
            qr_arg = call.args[len(call.args)-1]
            self._qr_text=qr_arg.text
            self._name_space_manager = NameSpaceFactory().create()
            self._qr_name=self._name_space_manager.add_name(self._qr_text, qr_arg.varName)

    @property
    def func_descriptors(self):
        return self._func_descriptors

    @property
    def qr_required(self):
        # does this kernel make use of a quadrature rule?
        return self._qr_required

    @property
    def qr_text(self):
        # what is the QR argument text used by the algorithm layer?
        return self._qr_text

    @property
    def qr_name(self):
        # what is the QR name to be used by the PSy layer?
        return self._qr_name

    def local_vars(self):
        return ["cell","map"]

    def field_on_space(self,fs):
        ''' returns true if a field exists on this space for this kernel'''
        if fs in self.arguments.unique_fss:
            for arg in self.arguments.args:
                if arg.function_space == fs and \
                        arg.type == "gh_field":
                    return True
        return False

    def gen_code(self, parent):
        ''' Generates dynamo version 0.3 specific psy code for a call to
            the dynamo kernel instance. '''
        from f2pygen import CallGen, DeclGen, AssignGen, UseGen, CommentGen

        parent.add(DeclGen(parent, datatype = "integer",
                           entity_decls = ["cell"]))

        # create a maps_required logical which we can use to add in spacer comments if necessary
        maps_required = False
        for unique_fs in self.arguments.unique_fss:
            if self.field_on_space(unique_fs):
                maps_required = True

        # function-space maps initialisation and their declarations
        if maps_required:
            parent.add(CommentGen(parent,""))

        for unique_fs in self.arguments.unique_fss:
            if self.field_on_space(unique_fs):
                # A map is required as there is a field on this space
                map_name = self._fs_descriptors.map_name(unique_fs)
                field = self._arguments.get_field(unique_fs)
                parent.add(AssignGen(parent, pointer = True, lhs = map_name,
                                     rhs = field.proxy_name_indexed+"%"+field.ref_name+"%get_cell_dofmap(cell)"))
        if maps_required:
            parent.add(CommentGen(parent,""))

        decl_map_names=[]
        for unique_fs in self.arguments.unique_fss:
            if self.field_on_space(unique_fs):
                # A map is required as there is a field on this space
                map_name=self._fs_descriptors.map_name(unique_fs)
                decl_map_names.append(map_name+"(:) => null()")
        if len(decl_map_names)>0:
            parent.add(DeclGen(parent, datatype = "integer", pointer = True,
                               entity_decls = decl_map_names))

        # orientation arrays initialisation and their declarations
        for unique_fs in self.arguments.unique_fss:
            if self._fs_descriptors.exists(unique_fs):
                fs_descriptor = self._fs_descriptors.get_descriptor(unique_fs)
                if fs_descriptor.orientation:
                    field = self._arguments.get_field(unique_fs)
                    parent.add(AssignGen(parent, pointer = True, lhs = fs_descriptor.orientation_name,
                                         rhs = field.proxy_name_indexed+"%vspace%get_cell_orientation(cell)"))
        if self._fs_descriptors.orientation:
            orientation_decl_names=[]
            for orientation_name in self._fs_descriptors.orientation_names:
                orientation_decl_names.append(orientation_name+"(:) => null()")
            parent.add(DeclGen(parent, datatype = "integer", pointer = True,
                               entity_decls = orientation_decl_names))
            parent.add(CommentGen(parent,""))
            
        # create the argument list
        arglist = []
        if self._arguments.has_operator:
            # 0.5: provide cell position
            arglist.append("cell")
        # 1: provide mesh height
        arglist.append("nlayers")
        # 2: Provide data associated with fields in the order specified in the metadata.
        #    If we have a vector field then generate the appropriate number of arguments.
        for arg in self._arguments.args:
            if arg.type == "gh_field":
                dataref = "%data"
                if arg.vector_size>1:
                    for idx in range(1,arg.vector_size+1):
                        arglist.append(arg.proxy_name+"("+str(idx)+")"+dataref)
                else:
                    arglist.append(arg.proxy_name+dataref)
            elif arg.type == "gh_operator":
                arglist.append(arg.proxy_name_indexed+"%ncell_3d")
                arglist.append(arg.proxy_name_indexed+"%local_stencil")
            else:
                raise GenerationError("Unexpected arg type found in dynamo0p3.py:DynKern:gen_code(). Expected one of [gh_field,gh_operator] but found "+arg.type)
        # 3: For each function space (in the order they appear in the metadata arguments)
        for unique_fs in self.arguments.unique_fss:
            # 3.1 Provide compulsory arguments common to operators and fields on a space
            arglist.extend(self._fs_descriptors.compulsory_args(unique_fs))
            # 3.1.1 Provide additional compulsory arguments if there is a field on this space
            if self.field_on_space(unique_fs):
                arglist.extend(self._fs_descriptors.compulsory_args_field(unique_fs))
            # 3.2 Provide optional arguments
            if self._fs_descriptors.exists(unique_fs):
                descriptor = self._fs_descriptors.get_descriptor(unique_fs)
                arglist.extend(descriptor.operator_names)
            # 3.3 Fix for boundary_dofs array in ru_kernel
            if self.name == "ru_code" and unique_fs == "w2":
                arglist.append("boundary_dofs_w2")
                parent.add(DeclGen(parent, datatype = "integer", pointer = True,
                                   entity_decls = ["boundary_dofs_w2(:,:) => null()"]))
                proxy_name=self._arguments.get_field("w2").proxy_name
                new_parent, position = parent.start_parent_loop()
                new_parent.add(AssignGen(new_parent, pointer = True,
                                         lhs = "boundary_dofs_w2",
                                         rhs = proxy_name+"%vspace%get_boundary_dofs()"),
                               position = ["before",position])
        # 4: Provide qr arguments if required
        if self._qr_required:
            arglist.extend(self._qr_args)

        # generate the kernel call and associated use statement
        parent.add(CallGen(parent, self._name, arglist))
        parent.parent.add(UseGen(parent.parent, name = self._module_name,
                                 only = True, funcnames = [self._name]))

class FS_Descriptor:

    def __init__(self, descriptor):
        self._descriptor = descriptor

    @property
    def requires_basis(self):
        if "gh_basis" in self._descriptor.operator_names:
            return True
        else:
            return False

    @property
    def requires_diff_basis(self):
        if "gh_diff_basis" in self._descriptor.operator_names:
            return True
        else:
            return False

    @property
    def operator_names(self):
        names=[]
        for operator_name in self._descriptor.operator_names:
            if operator_name == "gh_orientation":
                names.append(self.orientation_name)
            elif operator_name == "gh_basis":
                names.append(self.basis_name)
            elif operator_name == "gh_diff_basis":
                names.append(self.diff_basis_name)
            else:
                raise GenerationError("FS_Descriptor:operator_names: unsupported name '{0}' found".format(operator_name))
        return names

    def name(self,operator_name):
            if operator_name == "gh_orientation":
                return self.orientation_name
            elif operator_name == "gh_basis":
                return self.basis_name
            elif operator_name == "gh_diff_basis":
                return self.diff_basis_name
            else:
                raise GenerationError("FS_Descriptor:name: unsupported name '{0}' found".format(operator_name))
        
    @property
    def basis_name(self):
        return "basis"+"_"+self._descriptor.function_space_name

    @property
    def diff_basis_name(self):
        return "diff_basis"+"_"+self._descriptor.function_space_name

    @property
    def fs_name(self):
        return self._descriptor.function_space_name

    @property
    def orientation_name(self):
        for operator_name in self._descriptor.operator_names:
            if operator_name == "gh_orientation":
                return "orientation"+"_"+self._descriptor.function_space_name
        raise GenerationError("Internal logic error: FS-Descriptor:orientation_name: This descriptor has no orientation so can not have a name")

    @property
    def orientation(self):
        for operator_name in self._descriptor.operator_names:
            if operator_name == "gh_orientation":
                return True
        return False

class FS_Descriptors:

    def __init__(self,descriptors):
        self._orig_descriptors=descriptors
        self._descriptors=[]
        for descriptor in descriptors:
            self._descriptors.append(FS_Descriptor(descriptor))

    def compulsory_args(self,fs):
        ''' args that all fields and operators require for a function space '''
        return [self.ndf_name(fs)]

    def compulsory_args_field(self,fs):
        ''' args that a field requires for a function space in addition to the compulsory args'''
        return [self.undf_name(fs),self.map_name(fs)]

    def ndf_name(self,fs):
        return "ndf_"+fs

    def undf_name(self,fs):
        return "undf_"+fs

    def map_name(self,fs):
        return "map_"+fs

    @property
    def orientation(self):
        ''' Return true if at least one descriptor specifies orientation, otherwise return false '''
        for descriptor in self._descriptors:
            if descriptor.orientation:
                return True
        return False

    @property
    def orientation_names(self):
        names=[]
        for descriptor in self._descriptors:
            if descriptor.orientation:
                names.append(descriptor.orientation_name)
        return names

    def exists(self,fs_name):
        ''' Return true if a descriptor with the specified function name exists, otherwise return false '''
        for descriptor in self._descriptors:
            if descriptor.fs_name == fs_name:
                return True
        return False

    def get_descriptor(self,fs_name):
        ''' Return the descriptor with the specified function name. If it does not exist raise an error '''
        for descriptor in self._descriptors:
            if descriptor.fs_name == fs_name:
                return descriptor
        raise GenerationError("FS_Descriptors:get_descriptor: there is no descriptor for function space {0}".format(fs_name))

class DynKernelArguments(Arguments):
    ''' Provides information about Dynamo kernel call arguments collectively,
        as specified by the kernel argument metadata. This class currently
        adds no additional functionality to its base class other than
        ensuring that initialisation is performed correctly. '''
    def __init__(self, call, parent_call):
        if False:
            self._0_to_n = DynKernelArgument(None, None, None) # for pyreverse
        Arguments.__init__(self, parent_call)
        self._args = []
        for (idx, arg) in enumerate (call.ktype.arg_descriptors):
            self._args.append(DynKernelArgument(arg, call.args[idx],
                                                parent_call))
        self._dofs = []

    def get_field(self,fs):
        for arg in self._args:
            if arg.function_space == fs:
                return arg
        raise GenerationError("DynKernelArguments:get_field: there is no field with function space {0)".format(fs))

    @property
    def has_operator(self):
        for arg in self._args:
            if arg.type=="gh_operator":
                return True
        return False

    @property
    def unique_fss(self):
        ''' Returns a unique list of function spaces used by the arguments '''
        fs=[]
        for arg in self._args:
            if arg.function_space not in fs:
                fs.append(arg.function_space)
        return fs

    def iteration_space_arg(self, mapping={}):
        if mapping != {}:
            my_mapping = mapping
        else:
            my_mapping = {"write":"gh_write", "read":"gh_read","readwrite":"gh_rw", "inc":"gh_inc"}
        arg = Arguments.iteration_space_arg(self,my_mapping)
        return arg

    @property
    def dofs(self):
        ''' Currently required for invoke base class although this makes no
            sense for dynamo. Need to refactor the invoke class and pull out
            dofs into the gunghoproto api '''
        return self._dofs

class DynKernelArgument(Argument):
    ''' Provides information about individual Dynamo kernel call arguments
        as specified by the kernel argument metadata. '''
    def __init__(self, arg, arg_info, call):
        self._arg = arg
        Argument.__init__(self, call, arg_info, arg.access)
        self._vector_size = arg._vector_size
        self._type = arg._type

    @property
    def ref_name(self):
        if self._type == "gh_field":
            return "vspace"
        elif self._type == "gh_operator":
            return "fs_from"
        else:
            raise GenerationError("ref_name: Error, unsupported arg type '{0}' found".format(self._type))

    @property
    def type(self):
        return self._type

    @property
    def vector_size(self):
        return self._vector_size

    @property
    def proxy_name(self):
        return self._name+"_proxy"

    @property
    def proxy_name_indexed(self):
        if self._vector_size>1:
            return self._name+"_proxy(1)"
        else:
            return self._name+"_proxy"

    @property
    def function_space(self):
        ''' Returns the expected finite element function space for this
            argument as specified by the kernel argument metadata.'''
        return self._arg.function_space
