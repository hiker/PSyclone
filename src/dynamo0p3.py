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
        # include the lfric module
        lfric_use = UseGen(psy_module, name = "lfric")
        psy_module.add(lfric_use)
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
        self._psy_proxy_unique_declarations = []
        self._psy_field_info = {}
        self._proxy_name = {}
        for call in self.schedule.calls():
            for arg in call.arguments.args:
                if arg.text is not None:
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

    def gen_code(self, parent):
        ''' Generates Dynamo specific invocation code (the subroutine called
            by the associated invoke call in the algorithm layer). This
            consists of the PSy invocation subroutine and the declaration of
            its arguments.'''
        from f2pygen import SubroutineGen, TypeDeclGen, AssignGen, DeclGen, AllocateGen, DeallocateGen, CallGen, CommentGen
        # create the subroutine
        invoke_sub = SubroutineGen(parent, name = self.name,
                                   args = self.psy_unique_vars+self._psy_unique_qr_vars)

        # add the subroutine argument declarations
        invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "field_type",
                                  entity_decls = self._psy_unique_declarations,
                                  intent = "inout"))
        if len(self._psy_unique_qr_vars) > 0:
            invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "quadrature_type",
                                      entity_decls = self._psy_unique_qr_vars,
                                      intent = "in"))
        # declare and initialise proxies for each of the arguments
        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(CommentGen(invoke_sub," Initialise field proxies"))
        invoke_sub.add(CommentGen(invoke_sub,""))
        first_arg=""
        for arg in self.psy_unique_vars:
            if self._psy_field_info[arg].vector_size>1:
                if first_arg == "":
                    first_arg = self._proxy_name[arg]+"(1)"
                for idx in range(1,self._psy_field_info[arg].vector_size+1):
                    invoke_sub.add(AssignGen(invoke_sub, lhs = self._proxy_name[arg]+"("+str(idx)+")",
                                             rhs = arg+"("+str(idx)+")"+"%get_proxy()"))
            else:
                if first_arg == "":
                    first_arg = self._proxy_name[arg]
                invoke_sub.add(AssignGen(invoke_sub, lhs = self._proxy_name[arg],
                                         rhs = arg+"%get_proxy()"))
        invoke_sub.add(TypeDeclGen(invoke_sub, datatype = "field_proxy_type",
                                   entity_decls = self._psy_proxy_unique_declarations))

        # Initialise the number of layers using the first argument
        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(CommentGen(invoke_sub," Initialise number of layers"))
        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(AssignGen(invoke_sub, lhs="nlayers", rhs=first_arg+"%vspace%get_nlayers()"))
        invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                               entity_decls = ["nlayers"]))

        if self._qr_required:
            # initialise qr values
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Initialise qr values"))
            invoke_sub.add(CommentGen(invoke_sub,""))
            qr_vars = ["nqp_h","nqp_v","zp","xp","wh","wv"]
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
            for qr_var in qr_vars:
                invoke_sub.add(AssignGen(invoke_sub, lhs=qr_var, rhs=qr_var_name+"%get_"+qr_var+"()"))

        # declare and create required basis functions
        function_spaces = {}
        for call in self.schedule.calls():
            for func_descriptor in call.func_descriptors:
                if func_descriptor.function_space_name not in function_spaces.keys():
                    function_spaces[func_descriptor.function_space_name] = []
                for operator_name in func_descriptor.operator_names:
                    if operator_name not in function_spaces[func_descriptor.function_space_name]:
                        if operator_name in ["gh_basis", "gh_diff_basis"]:
                            function_spaces[func_descriptor.function_space_name].append(operator_name)

        arg_for_funcspace = {}
        for call in self.schedule.calls():
            for func_descriptor in call.func_descriptors:
                if func_descriptor.function_space_name not in arg_for_funcspace.keys():
                    found = False
                    for idx, arg_descriptor in enumerate(call.arg_descriptors):
                        if arg_descriptor.function_space_name1 == func_descriptor.function_space_name and not found:
                            arg_for_funcspace[func_descriptor.function_space_name] = self._proxy_name[call.arguments.args[idx].name]
                            found = True

        operator_declarations = []
        for function_space in function_spaces:
            for operator_name in function_spaces[function_space]:
                op_name = self.get_operator_name(operator_name, function_space)
                operator_declarations.append(op_name+"(:,:,:,:)")
        if not operator_declarations == []:
            invoke_sub.add(DeclGen(invoke_sub, datatype = "real", allocatable = True,
                                   kind = "r_def", entity_decls = operator_declarations))
        var_list = []
        var_dim_list = []
        for function_space in function_spaces:
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Initialise sizes and allocate basis arrays for "+function_space))
            invoke_sub.add(CommentGen(invoke_sub,""))

            name = arg_for_funcspace[function_space]
            ndf_name = self.ndf_name(function_space)
            var_list.append(ndf_name)
            invoke_sub.add(AssignGen(invoke_sub, lhs = ndf_name,
                                         rhs = name+"%vspace%get_ndf()"))
            undf_name = self.undf_name(function_space)
            var_list.append(undf_name)
            invoke_sub.add(AssignGen(invoke_sub, lhs = undf_name,
                                         rhs = name+"%vspace%get_undf()"))
            for operator_name in function_spaces[function_space]:
                if operator_name == 'gh_basis':
                    lhs = "dim_"+function_space
                    var_dim_list.append(lhs)
                    rhs = name+"%vspace%get_dim_space()"
                    alloc_args = "dim_"+function_space+", "+self.ndf_name(function_space)+", nqp_h, nqp_v"
                elif operator_name == 'gh_diff_basis':
                    lhs = "diff_dim_"+function_space
                    var_dim_list.append(lhs)
                    rhs = name+"%vspace%get_dim_space_diff()"
                    alloc_args = "diff_dim_"+function_space+", "+self.ndf_name(function_space)+", nqp_h, nqp_v"
                else:
                    raise GenerationError("Unsupported function space '{0}' found!.format(operator_name)")
                invoke_sub.add(AssignGen(invoke_sub, lhs=lhs, rhs=rhs))
                op_name = self.get_operator_name(operator_name, function_space)
                invoke_sub.add(AllocateGen(invoke_sub,op_name+"("+alloc_args+")"))
        if not var_list == []:
            invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                                   entity_decls = var_list))
        if not var_dim_list == []:
            invoke_sub.add(DeclGen(invoke_sub, datatype = "integer",
                                   entity_decls = var_dim_list))

        if self._qr_required:
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Compute basis arrays"))
            invoke_sub.add(CommentGen(invoke_sub,""))
            for function_space in function_spaces:
                for operator_name in function_spaces[function_space]:
                    args=[]
                    op_name = self.get_operator_name(operator_name, function_space)
                    args.append(op_name)
                    args.append(self.ndf_name(function_space))
                    args.extend(["nqp_h","nqp_v","xp","zp"])
                    name = arg_for_funcspace[function_space]
                    op_type_name = operator_name[3:]
                    invoke_sub.add(CallGen(invoke_sub,name=name+"%vspace%compute_"+op_type_name+"_function",args=args))

        invoke_sub.add(CommentGen(invoke_sub,""))
        invoke_sub.add(CommentGen(invoke_sub," Call our kernels"))
        invoke_sub.add(CommentGen(invoke_sub,""))
        # add content from the schedule
        self.schedule.gen_code(invoke_sub)

        if self._qr_required:
            invoke_sub.add(CommentGen(invoke_sub,""))
            invoke_sub.add(CommentGen(invoke_sub," Deallocate basis arrays"))
            invoke_sub.add(CommentGen(invoke_sub,""))
            
            func_space_var_names=[]
            for function_space in function_spaces:
                for operator_name in function_spaces[function_space]:
                    op_name = self.get_operator_name(operator_name, function_space)
                    func_space_var_names.append(op_name)
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
            self._stop = self.field_name+"_proxy%vspace%get_ncell()"
        Loop.gen_code(self,parent)

class DynInf(Inf):
    ''' A Dynamo 0.1 specific infrastructure call factory. No infrastructure
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

    def gen_code(self, parent):
        ''' Generates dynamo version 0.3 specific psy code for a call to
            the dynamo kernel instance. '''
        from f2pygen import CallGen, DeclGen, AssignGen, UseGen, CommentGen

        parent.add(DeclGen(parent, datatype = "integer",
                           entity_decls = ["cell"]))

        # function-space maps initialisation and their declarations
        for idx, unique_fs in enumerate(self.arguments.unique_fss):
            if idx == 0:
                parent.add(CommentGen(parent,""))
            map_name = self._fs_descriptors.map_name(unique_fs)
            field_proxy_name = self._arguments.get_field(unique_fs).proxy_name
            parent.add(AssignGen(parent, pointer = True, lhs = map_name,
                                 rhs = field_proxy_name+"%vspace%get_cell_dofmap(cell)"))
            if idx == len(self.arguments.unique_fss)-1:
                parent.add(CommentGen(parent,""))

        if len(self.arguments.unique_fss)>0:
            decl_map_names=[]
            for unique_fs in self.arguments.unique_fss:
                map_name=self._fs_descriptors.map_name(unique_fs)
                decl_map_names.append(map_name+"(:) ==> null()")
            parent.add(DeclGen(parent, datatype = "integer", pointer = True,
                               entity_decls = decl_map_names))

        # orientation arrays initialisation and their declarations
        for unique_fs in self.arguments.unique_fss:
            if self._fs_descriptors.exists(unique_fs):
                fs_descriptor = self._fs_descriptors.get_descriptor(unique_fs)
                if fs_descriptor.orientation:
                    field = self._arguments.get_field(unique_fs)
                    parent.add(AssignGen(parent, pointer = True, lhs = fs_descriptor.orientation_name,
                                         rhs = field.proxy_name+"%vspace%get_cell_orientation(cell)"))
        if self._fs_descriptors.orientation:
            orientation_decl_names=[]
            for orientation_name in self._fs_descriptors.orientation_names:
                orientation_decl_names.append(orientation_name+"(:) ==> null()")
            parent.add(DeclGen(parent, datatype = "integer", pointer = True,
                               entity_decls = orientation_decl_names))
            parent.add(CommentGen(parent,""))
            
        # create the argument list
        arglist = []
        # 1: provide mesh height
        arglist.append("nlayers")
        # 2: Provide data associated with fields in the order specified in the metadata.
        #    If we have a vector field then generate the appropriate number of arguments.
        for arg in self._arguments.args:
            dataref = "%data"
            if arg.vector_size>1:
                for idx in range(1,arg.vector_size+1):
                    arglist.append(arg.proxy_name+"("+str(idx)+")"+dataref)
            else:
                arglist.append(arg.proxy_name+dataref)
        # 3: For each function space (in the order they appear in the metadata arguments)
        for unique_fs in self.arguments.unique_fss:
            # 3.1 Provide compulsory arguments
            arglist.extend(self._fs_descriptors.compulsory_args(unique_fs))
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
        return [self.ndf_name(fs),self.undf_name(fs),self.map_name(fs)]

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

    @property
    def vector_size(self):
        return self._vector_size

    @property
    def proxy_name(self):
        return self._name+"_proxy"

    @property
    def function_space(self):
        ''' Returns the expected finite element function space for this
            argument as specified by the kernel argument metadata.'''
        return self._arg.function_space
    @property
    def requires_basis(self):
        ''' Returns true if the metadata for this argument specifies that
            its basis function values should be passed into the routine. '''
        if self._arg.basis.lower() == ".true.":
            return True
        if self._arg.basis.lower() == ".false.":
            return False
        raise GenerationError("error: basis is not set to .true. or .false.")
    @property
    def requires_diff_basis(self):
        ''' Returns true if the metadata for this argument specifies that
            its differential basis function values should be passed into
            the routine. '''
        if self._arg.diff_basis.lower() == ".true.":
            return True
        if self._arg.diff_basis.lower() == ".false.":
            return False
        raise GenerationError("error: diff_basis is not set to .true. "
                              "or .false.")
    @property
    def requires_gauss_quad(self):
        ''' Returns true if the metadata for this argument specifies that
            its gausian quadrature values should be passed into the
            routine. '''
        if self._arg.gauss_quad.lower() == ".true.":
            return True
        if self._arg.gauss_quad.lower() == ".false.":
            return False
        raise GenerationError("error: gaussian quadrature is not set to "
                              ".true. or .false.")
