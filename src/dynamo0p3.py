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
                operator_declarations.append(operator_name+"_"+function_space+"(:,:,:,:)")
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
            ndf_name = "ndf_"+function_space
            var_list.append(ndf_name)
            invoke_sub.add(AssignGen(invoke_sub, lhs = ndf_name,
                                         rhs = name+"%vspace%get_ndf()"))
            undf_name = "undf_"+function_space
            var_list.append(undf_name)
            invoke_sub.add(AssignGen(invoke_sub, lhs = undf_name,
                                         rhs = name+"%vspace%get_undf()"))
            for operator_name in function_spaces[function_space]:
                if operator_name == 'gh_basis':
                    lhs = "dim_"+function_space
                    var_dim_list.append(lhs)
                    rhs = name+"%vspace%get_dim_space()"
                    alloc_args = "dim_"+function_space+", ndf_"+function_space+", nqp_h, nqp_v"
                elif operator_name == 'gh_diff_basis':
                    lhs = "diff_dim_"+function_space
                    var_dim_list.append(lhs)
                    rhs = name+"%vspace%get_dim_space_diff()"
                    alloc_args = "diff_dim_"+function_space+", ndf_"+function_space+", nqp_h, nqp_v"
                else:
                    raise GenerationError("Not sorted out yet but when the code works this should not be called!")
                invoke_sub.add(AssignGen(invoke_sub, lhs=lhs, rhs=rhs))
                invoke_sub.add(AllocateGen(invoke_sub,operator_name+"_"+function_space+"("+alloc_args+")"))
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
                    args.append(operator_name+"_"+function_space)
                    args.append("ndf_"+function_space)
                    args.extend(["nqp_h","nqp_v","xp","zp"])
                    name = arg_for_funcspace[function_space]
                    invoke_sub.add(CallGen(invoke_sub,name=name+"%vspace%compute_"+operator_name+"_function",args=args))

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
                    func_space_var_names.append(operator_name+"_"+function_space)
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
        # dynamo 0.3 api kernels require quadrature rule arguments to be
        # passed in if one or more basis functions are used by the kernel.
        self._qr_required = False
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
        map_names = []
        for idx,arg_descriptor in enumerate(self.arg_descriptors):
            if idx == 0:
                parent.add(CommentGen(parent,""))
            fs = arg_descriptor.function_space
            map_name = "map_"+fs
            if map_name not in map_names:
                map_names.append(map_name)
                proxy_name = self.arguments.args[idx].name
                parent.add(AssignGen(parent, pointer = True, lhs = map_name,
                                     rhs = proxy_name+"%vspace%get_cell_dofmap( cell )"))
            if idx == len(self.arg_descriptors)-1:
                parent.add(CommentGen(parent,""))
        if len(map_names) > 0:
            decl_map_names = []
            for map_name in map_names:
                decl_map_names.append(map_name+"(:) ==> NULL")
            parent.add(DeclGen(parent, datatype = "integer", pointer = True,
                               entity_decls = decl_map_names))

        # create the argument list on the fly so we can also create
        # appropriate variables and lookups
        arglist = []
        # 1: provide mesh height
        arglist.append("nlayers")
        # 2: Provide data associated with fields in the order specified in the metadata.
        #    If we have a vector field then generate the appropriate number of arguments.
        for arg in self._arguments.args:
            dataref = "%data"
            if arg.vector_size>1:
                for idx in range(1,arg.vector_size+1):
                    arglist.append(arg.name+"_proxy("+str(idx)+")"+dataref)
            else:
                arglist.append(arg.name+"_proxy"+dataref)
        # 3: For each function space in the order they appear in the metadata arguments
        processed_fs=[]
        for arg in self.arguments.args:
            fs = arg.function_space
            if fs not in processed_fs:
                processed_fs.append(fs)
                # 3.1 Provide compulsory arguments
                arglist.append("ndf_"+fs)
                arglist.append("undf_"+fs)
                arglist.append("map_"+fs)
            # 3.2 TBD Provide optional arguments

        # 4: Provide qr arguments if required
        if self._qr_required:
            arglist.extend(["nqp_h","nqp_v","wh","wv"])



        #found_gauss_quad = False
        #gauss_quad_arg = None
        #for arg in self._arguments.args:
        if False:
            pass
            #if arg.requires_basis:
            #    basis_name = arg.function_space+"_basis_"+arg.name
            #    arglist.append(basis_name)
            #    position = parent.start_parent_loop()
            #    new_parent = position.parent
            #    new_parent.add(CallGen(new_parent,
            #                           field_name+"%vspace%get_basis",
            #                           [basis_name]),
            #                   position = ["before",
            #                               position])
            #    parent.add(DeclGen(parent, datatype = "real", kind = "dp",
            #                       pointer = True,
            #                       entity_decls = [basis_name+"(:,:,:,:,:)"]))
            #if arg.requires_diff_basis:
            #    raise GenerationError("differential basis has not yet "
            #                          "been coded")
            #if arg.requires_gauss_quad:
            #    if found_gauss_quad:
            #        raise GenerationError("found more than one gaussian "
            #                              "quadrature in this kernel")
            #    found_gauss_quad = True
            #    gauss_quad_arg = arg

        #if found_gauss_quad:
        #    gq_name = "gaussian_quadrature"
        #    arglist.append(gauss_quad_arg.name+"%"+gq_name)

        # generate the kernel call and associated use statement
        parent.add(CallGen(parent, self._name, arglist))
        parent.parent.add(UseGen(parent.parent, name = self._module_name,
                                 only = True, funcnames = [self._name]))

        # declare and initialise the number of layers and the number
        # of degrees of freedom. Needs to be generalised.
        #parent.add(DeclGen(parent, datatype = "integer",
        #                   entity_decls = ["nlayers", "ndf"]))
        #position = parent.start_parent_loop()
        #new_parent=position.parent
        #new_parent.add(AssignGen(new_parent, lhs = "nlayers",
        #                            rhs = field_name+"%get_nlayers()"),
        #                  position = ["before", position])
        #new_parent.add(AssignGen(new_parent, lhs = "ndf",
        #                         rhs = field_name+"%vspace%get_ndf()"),
        #               position = ["before", position])

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
