''' xxx '''
from psyGen import Node

valid_loop_types = {
    "vertical_quadrature":{"index":"qp2", "start":"1", "end":"nqp_v"},
    "horizontal_quadrature":{"index":"qp1", "start":"1", "end":"nqp_h"},
    "dofs":{"index":"df", "start":"1", "end":"ndf_*"},
    "vertical_column":{"index":"k", "start":"0", "end":"nlayers"},
    "vertical_column":{"index":"k", "start":"1", "end":"nlayers"}}

def get_loop_type(index, start, end, step):
    ''' xxx '''
    for valid_loop_name in valid_loop_types:
        if (check_loop_type(index, start, end, step, valid_loop_types[valid_loop_name])):
            return valid_loop_name
    return "unknown"

def check_loop_type(index, start, end, step, loop_type_info):
    ''' xxx '''
    if index in loop_type_info["index"]:
        return True
    else:
        return False

class Data(object):
    def __init__(self):
        self._datatype = None
    def hack_init(self, datatype):
        self._datatype = datatype
    @property
    def datatype(self):
        return self._datatype
    def view(self):
        return "[Data][{0}]".format(self.datatype)

class Variable(Data):
    ''' xxx '''
    def __init__(self):
        self._name = "unknown"
        self._datatype = "unknown"
        self._accesses = []
    def hack_init(self, name, datatype="real"):
        Data.hack_init(self, datatype)
        self._name = name
    def access(self, assignment, access_type):
        self._accesses.append([access_type, assignment])
    def accesses(self):
        return self._accesses
    @property
    def name(self):
        return self._name
    def view(self):
        return "[Variable][{0}][{1}]".format(self.datatype, self.name)
        

class Literal(Data):
    def __init__(self):
        self._value = None
    def hack_init(self, datatype, value):
        Data.hack_init(self, datatype)
        self._value = value
    @property
    def value(self):
        return self._value
    def view(self):
        return "[Literal][{0}][{1}]".format(self.datatype, self.value)

class Scalar(Variable):
    ''' xxx '''
    def __init__(self):
        self._declare = None
        Variable.__init__(self)
    @property
    def declare(self):
        return self._declare
    @declare.setter
    def declare(self, value):
        self._declare = value
    def view(self):
        return "[Scalar][{0}][{1}]".format(self.datatype, self.name)

class Array(Variable):
    ''' xxx '''
    def __init__(self):
        Variable.__init__(self)
        self._ndims = None
    def hack_init(self, name, datatype="real", ndims=1):
        Variable.hack_init(self, name, datatype)
        self._ndims = ndims
    @property
    def ndims(self):
        return self._ndims
    def view(self):
        return "[Array][{0}][{1}][{2}]".format(self.datatype, self.name, self.ndims)

class ArrayAccess(object):
    def __init__(self):
        self._array = None
        self._indices = None
    def hack_init(self, array, indices):
        self._array = array
        self._indices = indices
    @property
    def array(self):
        return self._array
    @property
    def indices(self):
        return self._indices
    def view(self):
        indices_str = list_to_str(self._indices, "indices")
        return "[{0}{1}]".format(self._array.name, indices_str)

class Kernel(Node):
    ''' xxx '''
    def __init__(self, name):
        self._name = name
        self._children = []
        self._variables = []
    @property
    def variables(self):
        return self._variables
    def view_variables(self):
        for variable in self._variables:
            print variable.name + "[",
            for access in variable.accesses():
                print " " + access[0],
            print "]"
    def view(self, indent=0):
        ''' xxx '''
        print self.indent(indent) + "Kernel[name='{0}']".format(self._name)
        for child in self.children:
            child.view(indent + 1)

class Function(Node):
    ''' xxx '''
    def __init__(self, name):
        self._name = name
    @property
    def name(self):
        return self._name
        
class Loop(Node):
    ''' xxx '''
    def __init__(self):
        self._loop_reference_start = None
        self._loop_reference_end = None
        self._children = []
    def hack_init(self, index, start, end, step=None):
        ''' xxx '''
        self._index = index
        self._start = start
        self._end = end
        self._step = step
        self._type = get_loop_type(index.name,start,end,step)
    def view(self, indent=0):
        ''' xxx '''
        print self.indent(indent) + "Loop[type='{0}',[{1}],'{2}','{3}','{4}']".format(self._type, self._index.name, self._start, self._end, self._step)
        for child in self.children:
            child.view(indent + 1)

class Assignment(Node):
    ''' xxx '''
    def __init__(self):
        self._children = []
    def hack_init(self, write=None, read=None, functions=None):
        self._writer = write
        if isinstance (write, ArrayAccess):
            write.array.access(self, "write")
        else:
            write.access(self, "write")
        self._readers = read
        self._functions = functions
    def view(self, indent=0):
        readers_str = list_to_str(self._readers, "read")
        functions_str = list_to_str(self._functions, "functions")
        print self.indent(indent) + "Assign[write='{0}'{1}{2}]".format(self._writer.view(), readers_str, functions_str)


def list_to_str(list_in, name):
        str_out = ""
        if not list_in:
            return str_out
        str_out = ", {0}=[".format(name)
        for idx, entry in enumerate(list_in):
            if isinstance(entry, str):
                str_out += entry
            else:
                str_out += entry.name
            if idx<(len(list_in)-1):
                str_out += ", "
        str_out += "]"
        return str_out


class Declaration(Node):
    ''' xxx '''
    def __init__(self):
        pass
    def hack_init(self, variable):
        self._variable = variable
        variable.declare = self
    def view(self, indent=0):
        print self.indent(indent) + "Declare{0}".format(self._variable.view())


pert_pressure_gradient_kernel = Kernel("pert_pressure_gradient_kernel")

# variable creation and declaration
rho_e = Array()
rho_e.hack_init("rho_e", ndims=1)
declare = Declaration()
declare.hack_init(rho_e)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(rho_e)

rho = Array()
rho.hack_init("rho", ndims=1)
declare = Declaration()
declare.hack_init(rho)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(rho)

rho_ref_e = Array()
rho_ref_e.hack_init("rho_ref_e", ndims=1)
declare = Declaration()
declare.hack_init(rho_ref_e)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(rho_ref_e)

rho_ref = Array()
rho_ref.hack_init("rho_ref", ndims=1)
declare = Declaration()
declare.hack_init(rho_ref)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(rho_ref)

theta_e = Array()
theta_e.hack_init("theta_e", ndims=1)
declare = Declaration()
declare.hack_init(theta_e)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(theta_e)

theta = Array()
theta.hack_init("theta", ndims=1)
declare = Declaration()
declare.hack_init(theta)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(theta)

theta_ref_e = Array()
theta_ref_e.hack_init("theta_ref_e", ndims=1)
declare = Declaration()
declare.hack_init(theta_ref_e)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(theta_ref_e)

theta_ref = Array()
theta_ref.hack_init("theta_ref", ndims=1)
declare = Declaration()
declare.hack_init(theta_ref)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(theta_ref)

ru_e = Array()
ru_e.hack_init("ru_e", ndims=1)
declare = Declaration()
declare.hack_init(ru_e)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(ru_e)

rho_at_quad = Scalar()
rho_at_quad.hack_init("rho_at_quad")
declare = Declaration()
declare.hack_init(rho_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(rho_at_quad)

rho_ref_at_quad = Scalar()
rho_ref_at_quad.hack_init("rho_ref_at_quad")
declare = Declaration()
declare.hack_init(rho_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(rho_ref_at_quad)

w3_basis = Array()
w3_basis.hack_init("w3_basis", ndims=4)
declare = Declaration()
declare.hack_init(w3_basis)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(w3_basis)

theta_at_quad = Scalar()
theta_at_quad.hack_init("theta_at_quad")
declare = Declaration()
declare.hack_init(theta_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(theta_at_quad)

grad_theta_at_quad = Array()
grad_theta_at_quad.hack_init("grad_theta_at_quad", ndims=3)
declare = Declaration()
declare.hack_init(grad_theta_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(grad_theta_at_quad)

theta_ref_at_quad = Scalar()
theta_ref_at_quad.hack_init("theta_ref_at_quad")
declare = Declaration()
declare.hack_init(theta_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(theta_ref_at_quad)

grad_theta_ref_at_quad = Array()
grad_theta_ref_at_quad.hack_init("grad_theta_ref_at_quad", ndims=1)
declare = Declaration()
declare.hack_init(grad_theta_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(grad_theta_ref_at_quad)

w0_basis = Array()
w0_basis.hack_init("w0_basis", ndims=4)
declare = Declaration()
declare.hack_init(w0_basis)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(w0_basis)

w0_diff_basis = Array()
w0_diff_basis.hack_init("w0_diff_basis", ndims=4)
declare = Declaration()
declare.hack_init(w0_diff_basis)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(w0_diff_basis)

exner_ref_at_quad = Scalar()
exner_ref_at_quad.hack_init("exner_ref_at_quad")
declare = Declaration()
declare.hack_init(exner_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(exner_ref_at_quad)

exner_at_quad = Array()
exner_at_quad.hack_init("exner_at_quad")
declare = Declaration()
declare.hack_init(exner_at_quad)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(exner_at_quad)

kappa = Scalar()
kappa.hack_init("kappa")
declare = Declaration()
declare.hack_init(kappa)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(kappa)

v = Array()
v.hack_init("v", ndims=1)
declare = Declaration()
declare.hack_init(v)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(v)

dv = Scalar()
dv.hack_init("dv")
declare = Declaration()
declare.hack_init(dv)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(dv)

w2_basis = Array()
w2_basis.hack_init("w2_basis", ndims=4)
declare = Declaration()
declare.hack_init(w2_basis)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(w2_basis)

w2_diff_basis = Array()
w2_diff_basis.hack_init("w2_diff_basis", ndims=4)
declare = Declaration()
declare.hack_init(w2_diff_basis)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(w2_diff_basis)

grad_term = Scalar()
grad_term.hack_init("grad_term")
declare = Declaration()
declare.hack_init(grad_term)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(grad_term)

cp = Scalar()
cp.hack_init("cp")
declare = Declaration()
declare.hack_init(cp)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(cp)

wqp_h = Array()
wqp_h.hack_init("wqp_h", ndims=1)
declare = Declaration()
declare.hack_init(wqp_h)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(wqp_h)

wqp_v = Array()
wqp_v.hack_init("wqp_v", ndims=1)
declare = Declaration()
declare.hack_init(wqp_v)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(wqp_v)

r_u = Array()
r_u.hack_init("r_u", ndims=1)
declare = Declaration()
declare.hack_init(r_u)
pert_pressure_gradient_kernel.addchild(declare)
pert_pressure_gradient_kernel.variables.append(r_u)

# loop indices
k = Scalar()
k.hack_init("k", datatype="integer")

df = Scalar()
df.hack_init("df", datatype="integer")

qp2 = Scalar()
qp2.hack_init("qp2", datatype="integer")

qp1 = Scalar()
qp1.hack_init("qp1", datatype="integer")

#Loops
levels_loop = Loop()
levels_loop.hack_init(k, "0", "nlayers-1")
pert_pressure_gradient_kernel.addchild(levels_loop)
levels_loop.parent = pert_pressure_gradient_kernel

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w3")
levels_loop.addchild(df_loop)
df_loop.parent = levels_loop

rho_e_access = ArrayAccess()
rho_e_access.hack_init(rho_e, [df])
assign = Assignment()
assign.hack_init(write=rho_e_access, read=[rho])
df_loop.addchild(assign)
assign.parent = df_loop

rho_ref_e_access = ArrayAccess()
rho_ref_e_access.hack_init(rho_ref_e, [df])
assign = Assignment()
assign.hack_init(write=rho_ref_e_access, read=[rho_ref])
df_loop.addchild(assign)
assign.parent = df_loop

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w0")
levels_loop.addchild(df_loop)
df_loop.parent = levels_loop

theta_e_access = ArrayAccess()
theta_e_access.hack_init(theta_e, [df])
assign = Assignment()
assign.hack_init(write=theta_e_access, read=[theta])
df_loop.addchild(assign)
assign.parent = df_loop

theta_ref_e_access = ArrayAccess()
theta_ref_e_access.hack_init(theta_ref_e, [df])
assign = Assignment()
assign.hack_init(write=theta_ref_e_access, read=[theta_ref])
df_loop.addchild(assign)
assign.parent = df_loop

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w2")
levels_loop.addchild(df_loop)
df_loop.parent = levels_loop

ru_e_access = ArrayAccess()
ru_e_access.hack_init(ru_e, [df])
assign = Assignment()
assign.hack_init(write=ru_e_access, read=[])
df_loop.addchild(assign)
assign.parent = df_loop

qp2_loop = Loop()
qp2_loop.hack_init(qp2, "1", "nqp_v")
levels_loop.addchild(qp2_loop)
qp2_loop.parent = levels_loop

qp1_loop = Loop()
qp1_loop.hack_init(qp1, "1", "nqp_h")
qp2_loop.addchild(qp1_loop)
qp1_loop.parent = levels_loop

assign = Assignment()
assign.hack_init(write=rho_at_quad, read=[])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

assign = Assignment()
assign.hack_init(write=rho_ref_at_quad, read=[])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w3")
qp1_loop.addchild(df_loop)
df_loop.parent = qp1_loop

assign = Assignment()
assign.hack_init(write=rho_at_quad, read=[rho_at_quad, rho_e, w3_basis])
df_loop.addchild(assign)
assign.parent = df_loop

assign = Assignment()
assign.hack_init(write=rho_ref_at_quad, read=[rho_ref_at_quad, rho_ref_e, w3_basis])
df_loop.addchild(assign)
assign.parent = df_loop

assign = Assignment()
assign.hack_init(write=theta_at_quad, read=[])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

grad_theta_at_quad_access = ArrayAccess()
grad_theta_at_quad_access.hack_init(grad_theta_at_quad, [":"])
assign = Assignment()
assign.hack_init(write=grad_theta_at_quad_access, read=[])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

assign = Assignment()
assign.hack_init(write=theta_ref_at_quad, read=[])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

grad_theta_ref_at_quad_access = ArrayAccess()
grad_theta_ref_at_quad_access.hack_init(grad_theta_ref_at_quad, [":"])
assign = Assignment()
assign.hack_init(write=grad_theta_ref_at_quad_access, read=[])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w0")
qp1_loop.addchild(df_loop)
df_loop.parent = qp1_loop

assign = Assignment()
assign.hack_init(write=theta_at_quad, read=[theta_at_quad, theta_e, w0_basis])
df_loop.addchild(assign)
assign.parent = df_loop

grad_theta_at_quad_access = ArrayAccess()
grad_theta_at_quad_access.hack_init(grad_theta_at_quad, [":"])
assign = Assignment()
assign.hack_init(write=grad_theta_at_quad_access, read=[grad_theta_at_quad, theta_e, w0_diff_basis])
df_loop.addchild(assign)
assign.parent = df_loop

assign = Assignment()
assign.hack_init(write=theta_ref_at_quad, read=[theta_ref_at_quad, theta_ref_e, w0_basis])
df_loop.addchild(assign)
assign.parent = df_loop

grad_theta_ref_at_quad_access = ArrayAccess()
grad_theta_ref_at_quad_access.hack_init(grad_theta_ref_at_quad, [":"])
assign = Assignment()
assign.hack_init(write=grad_theta_ref_at_quad_access, read=[grad_theta_ref_at_quad, theta_ref_e, w0_diff_basis])
df_loop.addchild(assign)
assign.parent = df_loop

calc_exner_pointwise = Function("calc_exner_pointwise")

assign = Assignment()
assign.hack_init(write=exner_ref_at_quad, read=[], functions=[calc_exner_pointwise])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

assign = Assignment()
assign.hack_init(write=exner_at_quad, read=[kappa, exner_ref_at_quad, theta_at_quad, theta_ref_at_quad, rho_at_quad, rho_ref_at_quad])
qp1_loop.addchild(assign)
assign.parent = qp1_loop

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w2")
qp1_loop.addchild(df_loop)
df_loop.parent = qp1_loop

assign = Assignment()
assign.hack_init(write=v, read=[w2_basis])
df_loop.addchild(assign)
assign.parent = df_loop

assign = Assignment()
assign.hack_init(write=dv, read=[w2_diff_basis])
df_loop.addchild(assign)
assign.parent = df_loop

dot_product = Function("dot_product")

assign = Assignment()
assign.hack_init(write=grad_term, read=[cp, exner_ref_at_quad, theta_at_quad, dv], functions=[dot_product])
df_loop.addchild(assign)
assign.parent = df_loop

assign = Assignment()
assign.hack_init(write=grad_term, read=[grad_term, cp, exner_at_quad, theta_ref_at_quad, dv], functions=[dot_product])
df_loop.addchild(assign)
assign.parent = df_loop

ru_e_access = ArrayAccess()
ru_e_access.hack_init(ru_e, [df])
assign = Assignment()
assign.hack_init(write=ru_e_access, read=[ru_e, wqp_h, wqp_v, grad_term])
df_loop.addchild(assign)
assign.parent = df_loop

df_loop = Loop()
df_loop.hack_init(df, "1", "ndf_w2")
levels_loop.addchild(df_loop)
df_loop.parent = levels_loop

r_u_access = ArrayAccess()
r_u_access.hack_init(r_u, [k])
assign = Assignment()
assign.hack_init(write=r_u_access, read=[r_u, ru_e])
df_loop.addchild(assign)
assign.parent = df_loop

pert_pressure_gradient_kernel.view()

kvec = Scalar()
kvec.hack_init("kvec", datatype="integer")

def modify_tree(orig, new):
    assign_region = False
    for idx, child in enumerate(orig.children):
        if isinstance(child, Assignment):
            if not assign_region:
                assign_region=True
                kvec_loop = Loop()
                kvec_loop.hack_init(kvec, "1", "nkvec")
                new.addchild(kvec_loop)
            kvec_loop.addchild(child)
            child.parent = kvec_loop
        elif isinstance(child, Loop):
            if assign_region:
                assign_region = False
            new_loop = Loop()
            new_loop.hack_init(child._index, child._start, child._end, child._step)
            new.addchild(new_loop)
            new_loop.parent = new
            modify_tree(child, new_loop)

def optimise(kernel):

    kloop = kernel.children[-1]
    vec_str = "nkvec"

    new_kloop = Loop()
    new_kloop.hack_init(kloop._index, kloop._start, kloop._end, vec_str)
    
    modify_tree(kloop, new_kloop)

    kernel.children[-1] = new_kloop
    new_kloop.parent = kernel

    return kernel

optimised_pert_pressure_gradient_kernel = optimise(pert_pressure_gradient_kernel)

optimised_pert_pressure_gradient_kernel.view()

optimised_pert_pressure_gradient_kernel.view_variables()
