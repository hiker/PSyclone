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

class Variable(object):
    def __init__(self):
        self._name = "unknown"
    def hack_init(self, name):
        self._name = name
    @property
    def name(self):
        return self._name

class Kernel(Node):
    ''' xxx '''
    def __init__(self, name):
        self._name = name
        self._children = []
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
        self._type = get_loop_type(index,start,end,step)
    def view(self, indent=0):
        ''' xxx '''
        print self.indent(indent) + "Loop[type='{0}','{1}','{2}','{3}','{4}']".format(self._type, self._index, self._start, self._end, self._step)
        for child in self.children:
            child.view(indent + 1)

class Assignment(Node):
    ''' xxx '''
    def __init__(self):
        self._assignment_reference = None
        self._children = []
    def hack_init(self, write=None, read=None, functions=None):
        self._writer = write
        self._readers = read
        self._functions = functions
    def view(self, indent=0):
        readers_str = list_to_str(self._readers, "read")
        functions_str = list_to_str(self._functions, "functions")
        print self.indent(indent) + "Assign[write='{0}'{1}{2}]".format(self._writer.name, readers_str, functions_str)


def list_to_str(list_in, name):
        str_out = ""
        if not list_in:
            return str_out
        str_out = ", {0}=[".format(name)
        for idx, entry in enumerate(list_in):
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
    def view(self, indent=0):
        print self.indent(indent) + "Declare[{0}]".format(self._variable.name)



###############################################################################
# pert_pressure_gradient_kernel example

# create the Kernel
pert_pressure_gradient_kernel = Kernel("pert_pressure_gradient_kernel")

# create and declare the variables the Kernel uses
rho_e = Variable()
rho_e.hack_init("rho_e")
declare = Declaration()
declare.hack_init(rho_e)
pert_pressure_gradient_kernel.addchild(declare)

rho = Variable()
rho.hack_init("rho")
declare = Declaration()
declare.hack_init(rho)
pert_pressure_gradient_kernel.addchild(declare)

rho_ref_e = Variable()
rho_ref_e.hack_init("rho_ref_e")
declare = Declaration()
declare.hack_init(rho_ref_e)
pert_pressure_gradient_kernel.addchild(declare)

rho_ref = Variable()
rho_ref.hack_init("rho_ref")
declare = Declaration()
declare.hack_init(rho_ref)
pert_pressure_gradient_kernel.addchild(declare)

theta_e = Variable()
theta_e.hack_init("theta_e")
declare = Declaration()
declare.hack_init(theta_e)
pert_pressure_gradient_kernel.addchild(declare)

theta = Variable()
theta.hack_init("theta")
declare = Declaration()
declare.hack_init(theta)
pert_pressure_gradient_kernel.addchild(declare)

theta_ref_e = Variable()
theta_ref_e.hack_init("theta_ref_e")
declare = Declaration()
declare.hack_init(theta_ref_e)
pert_pressure_gradient_kernel.addchild(declare)

theta_ref = Variable()
theta_ref.hack_init("theta_ref")
declare = Declaration()
declare.hack_init(theta_ref)
pert_pressure_gradient_kernel.addchild(declare)

ru_e = Variable()
ru_e.hack_init("ru_e")
declare = Declaration()
declare.hack_init(ru_e)
pert_pressure_gradient_kernel.addchild(declare)

rho_at_quad = Variable()
rho_at_quad.hack_init("rho_at_quad")
declare = Declaration()
declare.hack_init(rho_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

rho_ref_at_quad = Variable()
rho_ref_at_quad.hack_init("rho_ref_at_quad")
declare = Declaration()
declare.hack_init(rho_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

w3_basis = Variable()
w3_basis.hack_init("w3_basis")
declare = Declaration()
declare.hack_init(w3_basis)
pert_pressure_gradient_kernel.addchild(declare)

theta_at_quad = Variable()
theta_at_quad.hack_init("theta_at_quad")
declare = Declaration()
declare.hack_init(theta_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

grad_theta_at_quad = Variable()
grad_theta_at_quad.hack_init("grad_theta_at_quad")
declare = Declaration()
declare.hack_init(grad_theta_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

theta_ref_at_quad = Variable()
theta_ref_at_quad.hack_init("theta_ref_at_quad")
declare = Declaration()
declare.hack_init(theta_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

grad_theta_ref_at_quad = Variable()
grad_theta_ref_at_quad.hack_init("grad_theta_ref_at_quad")
declare = Declaration()
declare.hack_init(grad_theta_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

w0_basis = Variable()
w0_basis.hack_init("w0_basis")
declare = Declaration()
declare.hack_init(w0_basis)
pert_pressure_gradient_kernel.addchild(declare)

w0_diff_basis = Variable()
w0_diff_basis.hack_init("w0_diff_basis")
declare = Declaration()
declare.hack_init(w0_diff_basis)
pert_pressure_gradient_kernel.addchild(declare)

exner_ref_at_quad = Variable()
exner_ref_at_quad.hack_init("exner_ref_at_quad")
declare = Declaration()
declare.hack_init(exner_ref_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

exner_at_quad = Variable()
exner_at_quad.hack_init("exner_at_quad")
declare = Declaration()
declare.hack_init(exner_at_quad)
pert_pressure_gradient_kernel.addchild(declare)

kappa = Variable()
kappa.hack_init("kappa")
declare = Declaration()
declare.hack_init(kappa)
pert_pressure_gradient_kernel.addchild(declare)

v = Variable()
v.hack_init("v")
declare = Declaration()
declare.hack_init(v)
pert_pressure_gradient_kernel.addchild(declare)

dv = Variable()
dv.hack_init("dv")
declare = Declaration()
declare.hack_init(dv)
pert_pressure_gradient_kernel.addchild(declare)

w2_basis = Variable()
w2_basis.hack_init("w2_basis")
declare = Declaration()
declare.hack_init(w2_basis)
pert_pressure_gradient_kernel.addchild(declare)

w2_diff_basis = Variable()
w2_diff_basis.hack_init("w2_diff_basis")
declare = Declaration()
declare.hack_init(w2_diff_basis)
pert_pressure_gradient_kernel.addchild(declare)

grad_term = Variable()
grad_term.hack_init("grad_term")
declare = Declaration()
declare.hack_init(grad_term)
pert_pressure_gradient_kernel.addchild(declare)

cp = Variable()
cp.hack_init("cp")
declare = Declaration()
declare.hack_init(cp)
pert_pressure_gradient_kernel.addchild(declare)

wqp_h = Variable()
wqp_h.hack_init("wqp_h")
declare = Declaration()
declare.hack_init(wqp_h)
pert_pressure_gradient_kernel.addchild(declare)

wqp_v = Variable()
wqp_v.hack_init("wqp_v")
declare = Declaration()
declare.hack_init(wqp_v)
pert_pressure_gradient_kernel.addchild(declare)

r_u = Variable()
r_u.hack_init("r_u")
declare = Declaration()
declare.hack_init(r_u)
pert_pressure_gradient_kernel.addchild(declare)

# create the loops and assignments

levels_loop = Loop()
levels_loop.hack_init("k", "0", "nlayers-1")
pert_pressure_gradient_kernel.addchild(levels_loop)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w3")
levels_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=rho_e, read=[rho])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=rho_ref_e, read=[rho_ref])
df_loop.addchild(assign)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w0")
levels_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=theta_e, read=[theta])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=theta_ref_e, read=[theta_ref])
df_loop.addchild(assign)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w2")
levels_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=ru_e, read=[])
df_loop.addchild(assign)

qp2_loop = Loop()
qp2_loop.hack_init("qp2", "1", "nqp_v")
levels_loop.addchild(qp2_loop)

qp1_loop = Loop()
qp1_loop.hack_init("qp1", "1", "nqp_h")
qp2_loop.addchild(qp1_loop)

assign = Assignment()
assign.hack_init(write=rho_at_quad, read=[])
qp1_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=rho_ref_at_quad, read=[])
qp1_loop.addchild(assign)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w3")
qp1_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=rho_at_quad, read=[rho_at_quad, rho_e, w3_basis])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=rho_ref_at_quad, read=[rho_ref_at_quad, rho_ref_e, w3_basis])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=theta_at_quad, read=[])
qp1_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=grad_theta_at_quad, read=[])
qp1_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=theta_ref_at_quad, read=[])
qp1_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=grad_theta_ref_at_quad, read=[])
qp1_loop.addchild(assign)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w0")
qp1_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=theta_at_quad, read=[theta_at_quad, theta_e, w0_basis])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=grad_theta_at_quad, read=[grad_theta_at_quad, theta_e, w0_diff_basis])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=theta_ref_at_quad, read=[theta_ref_at_quad, theta_ref_e, w0_basis])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=grad_theta_ref_at_quad, read=[grad_theta_ref_at_quad, theta_ref_e, w0_diff_basis])
df_loop.addchild(assign)

calc_exner_pointwise = Function("calc_exner_pointwise")

assign = Assignment()
assign.hack_init(write=exner_ref_at_quad, read=[], functions=[calc_exner_pointwise])
qp1_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=exner_at_quad, read=[kappa, exner_ref_at_quad, theta_at_quad, theta_ref_at_quad, rho_at_quad, rho_ref_at_quad])
qp1_loop.addchild(assign)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w2")
qp1_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=v, read=[w2_basis])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=dv, read=[w2_diff_basis])
df_loop.addchild(assign)

dot_product = Function("dot_product")

assign = Assignment()
assign.hack_init(write=grad_term, read=[cp, exner_ref_at_quad, theta_at_quad, dv], functions=[dot_product])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=grad_term, read=[grad_term, cp, exner_at_quad, theta_ref_at_quad, dv], functions=[dot_product])
df_loop.addchild(assign)

assign = Assignment()
assign.hack_init(write=ru_e, read=[ru_e, wqp_h, wqp_v, grad_term])
df_loop.addchild(assign)

df_loop = Loop()
df_loop.hack_init("df", "1", "ndf_w2")
levels_loop.addchild(df_loop)

assign = Assignment()
assign.hack_init(write=r_u, read=[r_u, ru_e])
df_loop.addchild(assign)

pert_pressure_gradient_kernel.view()
