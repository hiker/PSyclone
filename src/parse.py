#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2014.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author L. Mitchell Imperial College
# Modified by R. Ford STFC Daresbury Lab

import fparser
from fparser import parsefortran
from fparser import api as fpapi
import expression as expr
import logging
import os

class ParseError(Exception):
    def __init__(self, value):
        self.value = "Parse Error: "+value
    def __str__(self):
        return repr(self.value)

class Descriptor(object):
    """A description of how a kernel argument is accessed"""
    def __init__(self,access,space,stencil):
        self._access=access
        self._space=space
        self._stencil=stencil

    @property
    def access(self):
        return self._access

    @property
    def function_space(self):
        return self._space

    @property
    def stencil(self):
        return self._stencil

    def __repr__(self):
        return 'Descriptor(%s, %s)' % (self.stencil, self.access)

class GODescriptor(Descriptor):
    def __init__(self, access, space, stencil):
        Descriptor.__init__(self,access,space,stencil)

class DynFuncDescriptor03():
    ''' The Dynamo 0.3 API has a function space descriptor as well as an argument descriptor. This class captures the information from one of these '''

    def __init__(self,func_type):
        self._func_type = func_type
        if func_type.name != 'func_type':
                raise ParseError("Each meta_func value must be of type 'func_type' for the dynamo0.3 api, but found '{0}'".format(func_type.name))
        if len(func_type.args) < 2:
            raise ParseError("Each meta_func value must have at least 2 args for the dynamo0.3 api, but found '{0}'".format(len(func_type.args)))
        self._operator_names = []
        self._valid_function_space_names = ["w0","w1","w2","w3"]
        self._valid_operator_names = ["gh_basis", "gh_diff_basis"]
        for idx,arg in enumerate(func_type.args):
            if idx==0:
                if arg.name not in self._valid_function_space_names:
                    raise ParseError("Each meta_func 1st argument must be one of {0} for the dynamo0.3 api, but found '{1}' in '{2}".format(self._valid_function_space_names,arg.name,func_type))
                self._function_space_name=arg.name
            else:
                if arg.name not in self._valid_operator_names:
                    raise ParseError("Each meta_func 2nd argument onwards must be one of {0} for the dynamo0.3 api, but found '{1}' in '{2}".format(self._valid_operator_names,arg.name,func_type))
                if arg.name in self._operator_names:
                    raise ParseError("Each meta_func 2nd argument onwards must be unique for the dynamo0.3 api, but found '{0}' specified more than once in '{1}".format(arg.name,func_type))
                self._operator_names.append(arg.name)
        self._name = func_type.name
        print str(self)

    @property
    def function_space_name(self):
        return self._function_space_name

    @property
    def operator_names(self):
        return self._operator_names

    def __repr__(self):
        return "DynFuncDescriptor03({0})".format(self._func_type)

    def __str__(self):
        res="DynFuncDescriptor03 object"+os.linesep
        res += "  name='{0}'".format(self._name)+os.linesep
        res += "  nargs={0}".format(len(self._operator_names)+1)+os.linesep
        res += "  function_space_name[{0}] = '{1}'".format(0,self._function_space_name)+os.linesep
        for idx,arg in enumerate(self._operator_names):
            res += "  operator_name[{0}] = '{1}'".format(idx+1,arg)+os.linesep
        return res

class DynArgDescriptor03(Descriptor):

    def __init__(self, arg_type):
        self._arg_type = arg_type
        if arg_type.name != 'arg_type':
            raise ParseError("Each meta_arg value must be of type 'arg_type' for the dynamo0.3 api, but found '{0}'".format(arg_type.name))
        # at least 3 args
        if len(arg_type.args) < 3:
            raise ParseError("Each meta_arg value must have at least 3 arguments for the dynamo0.3 api")
        # first arg is the type of field, possibly with a *n appended
        self._valid_arg_type_names = ["gh_field","gh_operator"]
        self._vector_size=1
        if isinstance(arg_type.args[0],expr.BinaryOperator): # we expect 'field_type * n'
            self._type = arg_type.args[0].toks[0].name
            operator=arg_type.args[0].toks[1]
            self._vector_size=arg_type.args[0].toks[2]
            if not self._type in self._valid_arg_type_names:
                raise ParseError("Each meta_arg 1st argument must be one of {0} for the dynamo0.3 api, but found '{1}'".format(self._valid_arg_type_names,self._type))
            if not operator == "*":
                raise ParseError("Each meta_arg 1st argument must use '*' if it is to be a vector for the dynamo0.3 api, but found '{0}'".format(operator))
            if not int(self._vector_size)>0:
                raise ParseError("Each meta_arg 1st argument must use a positive integer if it is to be a vector for the dynamo0.3 api, but found '{0}'".format(self._vector_size))
                
        elif isinstance(arg_type.args[0],expr.FunctionVar):
            if arg_type.args[0].name not in self._valid_arg_type_names:
                raise ParseError("Each meta_arg 1st argument must be one of {0} for the dynamo0.3 api, but found '{1}'".format(self._valid_arg_type_names,arg_type.args[0].name))
            self._type = arg_type.args[0].name
        else:
            raise ParseError("Internal error in DynArgDescriptor03, should not get to here")
        # 2nd arg is access descriptor
        self._valid_access_descriptor_names = ["gh_read","gh_write","gh_inc"]
        if arg_type.args[1].name not in self._valid_access_descriptor_names:
            raise ParseError("Each meta_arg 2nd argument must be one of {0} for the dynamo0.3 api, but found '{1}'".format(self._valid_access_descriptor_names,arg_type.args[1].name))
        self._access_descriptor = arg_type.args[1]
        self._valid_function_space_names = ["w0","w1","w2","w3"]
        if self._type == "gh_field":
            # we expect 3 arguments with the 3rd being a function space
            if len(arg_type.args) != 3:
                raise ParseError("Each meta_arg value must have 3 arguments for the dynamo0.3 api if its first argument is gh_field")
            if arg_type.args[2].name not in self._valid_function_space_names:
                raise ParseError("Each meta_arg 3rd argument must be one of {0} for the dynamo0.3 api, but found '{1}' in '{2}".format(self._valid_function_space_names,arg_type.args[2].name,arg_type))
            self._function_space1 = arg_type.args[2].name
        elif self._type == "gh_operator":
            # we expect 4 arguments with the 3rd and 4th each being a function space
            if len(arg_type.args) != 4:
                raise ParseError("Each meta_arg value must have 4 arguments for the dynamo0.3 api if its first argument is gh_operator")
            if arg_type.args[2] not in self._valid_function_space_names:
                raise ParseError("Each meta_arg 3rd argument must be one of {0} in the dynamo0.3 api, but found '{1}' in '{2}".format(self._valid_function_space_names,arg_type.args[2],arg_type))
            self._function_space1 = arg_type.args[2].name
            if arg_type.args[3] not in self._valid_function_space_names:
                raise ParseError("Each meta_arg 4th argument must be one of {0} in the dynamo0.3 api, but found '{1}' in '{2}".format(self._valid_function_space_names,arg_type.args[2],arg_type))
            self._function_space2 = arg_type.args[3].name
        else: # we should never get to here
            raise ParseError("Internal logic error in DynArgDescriptor03")
            
        Descriptor.__init__(self,self._access_descriptor.name,self._function_space1,None)
        print str(self)
        #@property
        #def access(self):
        #return self._access_descriptor.name
        #self._access = self._access_descriptor.name
        #self._space = self._function_space1
        #self.basis = ".false."
        #self.diff_basis = ".false."
        #self.gauss_quad = ".false."

    def __str__(self):
        res="DynArgDescriptor03 object"+os.linesep
        res += "  argument_type[0]='{0}'".format(self._type)
        if int(self._vector_size>1):
            res += "*"+self._vector_size
        res += os.linesep
        res += "  access_descriptor[1]='{0}'".format(self._access_descriptor)+os.linesep
        if self._type == "gh_field":
            res += "  function_space[2]='{0}'".format(self._function_space1)+os.linesep
        elif self._type == "gh_operator":
            res += "  function_space_out[2]='{0}'".format(self._function_space1)+os.linesep
            res += "  function_space_in[3]='{0}'".format(self._function_space2)+os.linesep
        else: # we should never get to here
            raise ParseError("Internal logic error in DynArgDescriptor03")
        return res
        
    def __repr__(self):
        return "DynArgDescriptor03({0})".format(self._arg_type)
        

class DynDescriptor(Descriptor):
    def __init__(self,access,funcspace,stencil,basis,diff_basis,gauss_quad):
        Descriptor.__init__(self,access,funcspace,stencil)
        self._basis=basis
        self._diff_basis=diff_basis
        self._gauss_quad=gauss_quad
    @property
    def basis(self):
        return self._basis
    @property
    def diff_basis(self):
        return self._diff_basis
    @property
    def gauss_quad(self):
        return self._gauss_quad

class GHProtoDescriptor(Descriptor):
    def __init__(self, access, space, stencil):
        self._space = FunctionSpace.unpack(space)
        Descriptor.__init__(self,access,self._space,stencil)

    @property
    def element(self):
        return self._space.element

    def __repr__(self):
        return 'Descriptor(%s, %s, %s)' % (self.stencil, self.element, self.access)


class FunctionSpace(object):
    @staticmethod
    def unpack(string):
        p = expr.expression.parseString(string)[0]
        dim = 1
        if isinstance(p, expr.BinaryOperator) and p.symbols[0] == '**':
            dim = int(p.operands[1])
            p = p.operands[0]
        ele = Element.unpack(p)
        return FunctionSpace(ele, dim)

    def __init__(self, element, dimension):
        self._element = element
        self._dimension = dimension

    @property
    def element(self):
        return self._element

    @property
    def dimension(self):
        return self._dimension


class Element(object):
    @staticmethod
    def unpack(string_or_expr):
        if isinstance(string_or_expr, str):
            p = expr.expression.parseString(string_or_expr)[0]
        else:
            p = string_or_expr
        if isinstance(p, expr.Grouping):
            p = p.expr
        if isinstance(p, expr.BinaryOperator):
            assert all(a == '*' for a in p.symbols)
            eles = p.operands
        else:
            assert isinstance(p, expr.FunctionVar)
            eles = [p]
        order = eles[0].args[0] if eles[0].args else None
        ele = Element(eles[0].name, order)
        for e in eles[1:]:
            order = e.args[0] if e.args else None
            ele *= Element(e.name, order)
        return ele

    def __init__(self, name=None, order=None):
        self._name = name
        if isinstance(order, str):
            order = int(order)
        self._order = order

    def __repr__(self):
        if self._order:
            return "%s%d" % (self._name, self._order)
        return "%s" % self._name

    def __mul__(self, other):
        assert isinstance(other, Element), \
            'Can only take tensor products with Elements'
        return TensorProductElement(self, other)


class TensorProductElement(Element):
    def __init__(self, *elements):
        assert all(isinstance(e, Element) for e in elements), 'All arguments to build a TensorProductElement should be Elements'
        self._elements = elements

    @property
    def elements(self):
        return self._elements

    def __repr__(self):
        s = " * ".join("%s" % e for e in self.elements)
        return s

    def __mul__(self, other):
        assert isinstance(other, Element), 'Can only take tensor products with Elements not %s' % type(other)
        if isinstance(other, TensorProductElement):
            return TensorProductElement(*(self.elements + other.elements))
        else:
            return TensorProductElement(*(self.elements + (other, )))


class KernelProcedure(object):
    """An elemental kernel procedure"""
    def __init__(self, ktype_ast, ktype_name, modast):
        a, n = KernelProcedure.get_procedure(ktype_ast, ktype_name, modast)
        self._ast = a
        self._name = n

    @staticmethod
    def get_procedure(ast, name, modast):
        bname = None
        for statement in ast.content:
            if isinstance(statement, fparser.statements.SpecificBinding):
                if statement.name=="code" and statement.bname!="":
                    # prototype gungho style
                    bname = statement.bname
                elif statement.name.lower()!="code" and statement.bname!="":
                    raise ParseError("Kernel type %s binds to a specific procedure but does not use 'code' as the generic name." % \
                                     name)
                else:
                    # psyclone style
                    bname=statement.name
        if bname is None:
            raise RuntimeError("Kernel type %s does not bind a specific procedure" % \
                               name)
        if bname=='':
            raise ParseError("Internal error: empty kernel name returned for Kernel type %s." % \
                               name)
        code = None
        default_public=True
        declared_private=False
        declared_public=False
        for statement, depth in fpapi.walk(modast, -1):
            if isinstance(statement, fparser.statements.Private):
                if len(statement.items)==0:
                    default_public=False
                elif bname in statement.items:
                    declared_private=True
            if isinstance(statement, fparser.statements.Public):
                if len(statement.items)==0:
                    default_public=True
                elif bname in statement.items:
                    declared_public=True
            if isinstance(statement, fparser.block_statements.Subroutine) and \
               statement.name == bname:
                if statement.is_public():
                    declared_public=True
                code = statement
        if code is None:
            raise RuntimeError("Kernel subroutine %s not implemented" % bname)
        if declared_private or (not default_public and not declared_public):
            raise ParseError("Kernel subroutine '%s' is not public" % bname)
        return code, bname


    @property
    def name(self):
        return self._name

    @property
    def ast(self):
        return self._ast

    def __repr__(self):
        return 'KernelProcedure(%s, %s)' % (self.name, self.ast)

    def __str__(self):
        return self._ast.__str__()


class KernelTypeFactory(object):
    def __init__(self,api=""):
        if api=="":
            from config import DEFAULTAPI
            self._type=DEFAULTAPI
        else:
            from config import SUPPORTEDAPIS as supportedTypes
            self._type=api
            if self._type not in supportedTypes:
                raise ParseError("KernelTypeFactory: Unsupported API '{0}' specified. Supported types are {1}.".format(self._type, supportedTypes))

    def create(self,name,ast):
        if self._type=="gunghoproto":
            return GHProtoKernelType(name,ast)
        elif self._type=="dynamo0.1":
            return DynKernelType(name,ast)
        elif self._type=="dynamo0.3":
            return DynKernelType03(name,ast)
        elif self._type=="gocean":
            return GOKernelType(name,ast)
        else:
            raise ParseError("KernelTypeFactory: Internal Error: Unsupported kernel type '{0}' found. Should not be possible.".format(self._myType))

class KernelType(object):
    """ Kernel Metadata baseclass

    This contains the elemental procedure and metadata associated with
    how that procedure is mapped over mesh entities."""

    def __init__(self,name,ast):
        self._name = name
        self._ast = ast
        self.checkMetadataPublic(name,ast)
        self._ktype=self.getKernelMetadata(name,ast)
        #print self._ktype
        self._iterates_over = self._ktype.get_variable('iterates_over').init
        #print  self._ktype.get_variable('iterates_over')
        #print self._iterates_over
        self._procedure = KernelProcedure(self._ktype, name, ast)
        self._inits=self.getkerneldescriptors(self._ktype)
        self._arg_descriptors=None # this is set up by the subclasses
        
    def getkerneldescriptors(self,ast, var_name='meta_args'):
        descs = ast.get_variable(var_name)
        if descs is None:
            raise ParseError("kernel call does not contain a {0} type".format(var_name))
        try:
            nargs=int(descs.shape[0])
        except AttributeError as e:
            raise ParseError("kernel metadata {0}: {1} variable must be an array".format(self._name, var_name))
        if len(descs.shape) is not 1:
            raise ParseError("kernel metadata {0}: {1} variable must be a 1 dimensional array".format(self._name, var_name))
        if descs.init.find("[") is not -1 and descs.init.find("]") is not -1:
            # there is a bug in f2py
            raise ParseError("Parser does not currently support [...] initialisation for {0}, please use (/.../) instead".format(var_name))
        inits = expr.expression.parseString(descs.init)[0]
        nargs=int(descs.shape[0])
        if len(inits) != nargs:
            raise ParseError("Error, in {0} specification, the number of args {1} and number of dimensions {2} do not match".format(var_name, nargs, len(inits)))
        return inits

    @property
    def name(self):
        return self._name

    @property
    def iterates_over(self):
        return self._iterates_over

    @property
    def procedure(self):
        return self._procedure

    @property
    def nargs(self):
        return len(self._arg_descriptors)

    @property
    def arg_descriptors(self):
        return self._arg_descriptors

    def __repr__(self):
        return 'KernelType(%s, %s)' % (self.name, self.iterates_over)

    def checkMetadataPublic(self,name,ast):
        default_public=True
        declared_private=False
        declared_public=False
        for statement, depth  in fpapi.walk(ast, -1):
            if isinstance(statement, fparser.statements.Private):
                if len(statement.items)==0:
                    default_public=False
                elif name in statement.items:
                    declared_private=True
            if isinstance(statement, fparser.statements.Public):
                if len(statement.items)==0:
                    default_public=True
                elif name in statement.items:
                    declared_public=True
            if isinstance(statement, fparser.block_statements.Type) \
               and statement.name == name and statement.is_public():
                    declared_public=True
        if declared_private or (not default_public and not declared_public):
            raise ParseError("Kernel type '%s' is not public" % name)

    def getKernelMetadata(self,name, ast):
        ktype = None
        for statement, depth  in fpapi.walk(ast, -1):
            if isinstance(statement, fparser.block_statements.Type) \
               and statement.name == name:
                ktype = statement
        if ktype is None:
            raise RuntimeError("Kernel type %s not implemented" % name)
        return ktype

class DynKernelType03(KernelType):
    def __init__(self,name,ast):
        KernelType.__init__(self,name,ast)

        # parse arg_type metadata
        self._arg_descriptors=[]
        for arg_type in self._inits:
            self._arg_descriptors.append(DynArgDescriptor03(arg_type))
            
        # parse func_type metadata if it exists
        found = False
        for line in self._ktype.content:
            if isinstance(line,fparser.typedecl_statements.Type):
                for entry in line.selector:
                    if entry == "func_type":
                        if line.entity_decls[0].split()[0].split("(")[0] == "meta_funcs":
                            found=True
                            break
        if not found:
            func_types = []
        else:
            func_types = self.getkerneldescriptors(self._ktype,var_name="meta_funcs")
        self._func_descriptors=[]
        for func_type in func_types:
            self._func_descriptors.append(DynFuncDescriptor03(func_type))

    @property
    def func_descriptors(self):
        return self._func_descriptors

class DynKernelType(KernelType):
    def __init__(self,name,ast):
        KernelType.__init__(self,name,ast)
        self._arg_descriptors=[]
        for init in self._inits:
            if init.name != 'arg_type':
                raise ParseError("Each meta_arg value must be of type 'arg_type' for the dynamo0.1 api, but found '{0}'".format(init.name))
            access=init.args[0].name
            funcspace=init.args[1].name
            stencil=init.args[2].name
            x1=init.args[3].name
            x2=init.args[4].name
            x3=init.args[5].name
            self._arg_descriptors.append(DynDescriptor(access,funcspace,stencil,x1,x2,x3))

class GOKernelType(KernelType):
    def __init__(self,name,ast):
        KernelType.__init__(self,name,ast)
        self._arg_descriptors=[]
        for init in self._inits:
            if init.name != 'arg':
                raise ParseError("Each meta_arg value must be of type 'arg' for the gocean0.1 api, but found '{0}'".format(init.name))
            access=init.args[0].name
            funcspace=init.args[1].name
            stencil=init.args[2].name
            if len(init.args) != 3:
                raise ParseError("'arg' type expects 3 arguments but found '{}' in '{}'".format(str(len(init.args)), init.args))
            self._arg_descriptors.append(GODescriptor(access,funcspace,stencil))
        
class GHProtoKernelType(KernelType):

    def __init__(self, name, ast):
        KernelType.__init__(self,name,ast)
        self._arg_descriptors = []
        for init in self._inits:
            if init.name != 'arg':
                raise ParseError("Each meta_arg value must be of type 'arg' for the GungHo prototype API, but found '"+init.name+"'")
            if len(init.args) != 3:
                raise ParseError("'arg' type expects 3 arguments but found '{}' in '{}'".format(str(len(init.args)), init.args))
            self._arg_descriptors.append(GHProtoDescriptor(init.args[0].name,
                                         str(init.args[1]),
                                         init.args[2].name))

class InfCall(object):
    """An infrastructure call (appearing in
    `call invoke(kernel_name(field_name, ...))`"""
    def __init__(self, module_name,func_name, args):
        self._module_name = module_name
        self._args = args
        self._func_name=func_name

    @property
    def args(self):
        return self._args

    @property
    def module_name(self):
        return self._module_name

    @property
    def func_name(self):
        return self._func_name

    @property
    def type(self):
        return "InfrastructureCall"

    def __repr__(self):
        return 'InfrastructureCall(%s, %s)' % (self.module_name, self.args)


class KernelCall(object):
    """A kernel call (appearing in
    `call invoke(kernel_name(field_name, ...))`"""

    def __init__(self, module_name, ktype, args):
        self._module_name = module_name
        self._ktype = ktype
        self._args = args
        if len(self._args) < self._ktype.nargs:
            # we cannot test for equality here as API's may have extra arguments
            # passed in from the algorithm layer (e.g. 'QR' in dynamo0.3), but
            # we do expect there to be at least the same number of real
            # arguments as arguments specified in the metadata.
            raise ParseError("Kernel '{0}' called from the algorithm layer with an insufficient number of arguments as specified by the metadata. Expected at least '{1}' but found '{2}'.".format(self._ktype.name, self._ktype.nargs, len(self._args)))

    @property
    def ktype(self):
        return self._ktype

    @property
    def args(self):
        return self._args

    @property
    def module_name(self):
        return self._module_name

    @property
    def type(self):
        return "kernelCall"

    def __repr__(self):
        return 'KernelCall(%s, %s)' % (self.ktype, self.args)
        
class Arg(object):
    ''' Descriptions of an argument '''
    def __init__(self,form,text,varName=None):
        formOptions=["literal","variable","indexed_variable"]
        self._form=form
        self._text=text
        self._varName=varName
        if form not in formOptions:
            raise ParseError("Unknown arg type provided. Expected one of {0} but found {1}".format(str(formOptions),form))
    @property
    def form(self):
        return self._form
    @property
    def text(self):
        return self._text
    @property
    def varName(self):
        return self._varName
    def is_literal(self):
        if self._form=="literal":
            return True
        return False

class InvokeCall(object):
    def __init__(self, kcalls, name=None, myid=1, invoke_name="invoke"):
        self._kcalls = kcalls
        self._name=name

    @property
    def name(self):
        """Return the name of this invoke call"""
        return self._name

    @property
    def kcalls(self):
        """Return the list of kernel calls in this invoke call"""
        return self._kcalls

class FileInfo(object):
    def __init__(self,name,calls):
        self._name=name
        self._calls=calls
    @property
    def name(self):
        return self._name
    @property
    def calls(self):
        return self._calls

def parse(filename, api="", invoke_name="invoke", inf_name="inf"):
    '''
    Takes a GungHo algorithm specification as input and outputs an AST of this specification and an object containing information about the invocation calls in the algorithm specification and any associated kernel implementations.

    :param str filename: The file containing the algorithm specification.
    :param str invoke_name: The expected name of the invocation calls in the algorithm specification
    :param str inf_name: The expected module name of any required infrastructure routines.
    :rtype: ast,invoke_info
    :raises IOError: if the filename does not exist
    :raises ParseError: if there is an error in the parsing
    :raises RuntimeError: if there is an error in the parsing

    For example:

    >>> from parse import parse
    >>> ast,info=parse("argspec.F90")

    '''
    if api=="":
        from config import DEFAULTAPI
        api=DEFAULTAPI
    else:
        from config import SUPPORTEDAPIS
        if api not in SUPPORTEDAPIS:
            raise ParseError("parse: Unsupported API '{0}' specified. Supported types are {1}.".format(api, SUPPORTEDAPIS))


    # drop cache
    fparser.parsefortran.FortranParser.cache.clear()
    fparser.logging.disable('CRITICAL')
    if not os.path.isfile(filename):
        raise IOError("File %s not found" % filename)
    try:
        ast = fpapi.parse(filename, ignore_comments = False, analyze = False)
    except:
        import traceback
        traceback.print_exc()
	raise ParseError("Fatal error in external fparser tool")
    name_to_module = {}
    try:
        from collections import OrderedDict
    except:
        try:
            from ordereddict import OrderedDict
        except:
            import sys
            python_version=sys.version_info
            if python_version[0]<=2 and python_version[1]<7:
                raise ParseError("OrderedDict not provided natively pre python 2.7 (you are running {0}. Try installing with 'sudo pip install ordereddict'".format(python_version))
            else:
                raise ParseError("OrderedDict not found which is unexpected as it is meant to be part of the Python library from 2.7 onwards")
    invokecalls = OrderedDict()

    container_name=None
    for child in ast.content:
        if isinstance(child,fparser.block_statements.Program) or \
           isinstance(child,fparser.block_statements.Module) or \
           isinstance(child,fparser.block_statements.Subroutine):
            container_name=child.name
            break
    if container_name is None:
        raise ParseError("Error, program, module or subroutine not found in ast")

    for statement, depth in fpapi.walk(ast, -1):
        if isinstance(statement, fparser.statements.Use):
            for name in statement.items:
                name_to_module[name] = statement.name
        if isinstance(statement, fparser.statements.Call) \
           and statement.designator == invoke_name:
            statement_kcalls = []
            for arg in statement.items:
                parsed = expr.expression.parseString(arg)[0]
                argname = parsed.name
                argargs=[]
                for a in parsed.args:
                    if type(a) is str: # a literal is being passed by argument
                        argargs.append(Arg('literal',a))
                    else: # assume argument parsed as a FunctionVar
                        variableName = a.name
                        if a.args is not None:
                            # argument is an indexed array so extract the full text
                            fullText = ""
                            for tok in a.walk2():
                                fullText+=str(tok)
                            argargs.append(Arg('indexed_variable',fullText,variableName))
                        else:
                            # argument is a standard variable
                            argargs.append(Arg('variable',variableName,variableName))
                if argname in ['set']: # this is an infrastructure call
                    statement_kcalls.append(InfCall(inf_name,argname,argargs))
                else:
                    try:
                        modulename = name_to_module[argname]
                    except KeyError:
                        raise ParseError("kernel call '%s' must be named in a use statement" % argname)
                    root_dir = os.path.abspath(os.path.dirname(filename))
                    if not os.path.isfile(os.path.join(root_dir,'%s.F90' % modulename)):
                        if not os.path.isfile(os.path.join(root_dir,'%s.f90' % modulename)):
                            raise IOError("Kernel file '%s.[fF]90' not found" % modulename)
                        else:
                            #modast = fpapi.parse('%s.f90' % modulename, ignore_comments = False, analyze = False )
                            modast = fpapi.parse(os.path.join(root_dir,'%s.f90' % modulename))
                    else:
                        #modast = fpapi.parse('%s.F90' % modulename, ignore_comments = False, analyze = False )
                        modast = fpapi.parse(os.path.join(root_dir,'%s.F90' % modulename))
                    statement_kcalls.append(KernelCall(modulename, KernelTypeFactory(api=api).create(argname, modast),argargs))
            invokecalls[statement] = InvokeCall(statement_kcalls)
    return ast, FileInfo(container_name,invokecalls)
