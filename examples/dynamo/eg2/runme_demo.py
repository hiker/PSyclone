#export PYTHONPATH=/home/rupert/proj/GungHoSVN/PSyclone_r1895_module_inline/f2py_88:/home/rupert/proj/GungHoSVN/PSyclone_r1895_module_inline/src:${PYTHONPATH}

from parse import parse
from psyGen import PSyFactory
api="dynamo0.1"
ast,invokeInfo=parse("dynamo_algorithm_mod.F90",api=api)
psy=PSyFactory(api).create(invokeInfo)

from algGen import Alg
alg = Alg(ast,psy)
print alg.gen

print psy.gen

print psy.invokes.names

schedule=psy.invokes.get('invoke_0').schedule
schedule.view()

from psyGen import TransInfo
t=TransInfo()
print t.list

lf=t.get_trans_name('LoopFuse')
ol=t.get_trans_name('OpenMPLoop')
lc=t.get_trans_name('LoopColour')
ki=t.get_trans_name('KernelModuleInline')

schedule.view()
fuse_schedule,memento=lf.apply(schedule.children[0],schedule.children[1])
fuse_schedule.view()

psy.invokes.get('invoke_0')._schedule=fuse_schedule
print psy.gen

fuse_schedule.view()
omp_schedule,memento=ol.apply(fuse_schedule.children[0])
omp_schedule.view()

psy.invokes.get('invoke_0')._schedule=omp_schedule
print psy.gen

omp_schedule.view()
ki_schedule,memento=ki.apply(omp_schedule.children[0].children[0].children[0])
ki_schedule.view()

psy.invokes.get('invoke_0')._schedule=ki_schedule
print psy.gen

# v2 invoke

schedule=psy.invokes.get('invoke_v2_kernel_type').schedule
schedule.view()
lc_schedule,memento=lc.apply(schedule.children[0])
lc_schedule.view()

psy.invokes.get('invoke_v2_kernel_type')._schedule=lc_schedule
print psy.gen

lc_schedule.view()
lc_omp_schedule,memento=ol.apply(lc_schedule.children[0].children[0])
lc_omp_schedule.view()

psy.invokes.get('invoke_v2_kernel_type')._schedule=lc_omp_schedule
print psy.gen

# v1 invoke

schedule=psy.invokes.get('invoke_v1_kernel_type').schedule
schedule.view()
lc_schedule,memento=lc.apply(schedule.children[0])
lc_schedule.view()

lc_omp_schedule,memento=ol.apply(lc_schedule.children[0].children[0])
lc_omp_schedule.view()

psy.invokes.get('invoke_v1_kernel_type')._schedule=lc_omp_schedule
print psy.gen
