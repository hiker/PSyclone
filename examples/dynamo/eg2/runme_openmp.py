from parse import parse
from psyGen import PSyFactory
api="dynamo0.1"
ast,invokeInfo=parse("dynamo_algorithm_mod.F90",api=api)
psy=PSyFactory(api).create(invokeInfo)
print psy.gen

print psy.invokes.names

schedule=psy.invokes.get('invoke_0').schedule
schedule.view()

from psyGen import TransInfo
t=TransInfo()
print t.list

lf=t.get_trans_name('LoopFuse')
ol=t.get_trans_name('OpenMPLoop')

schedule.view()
fuse_schedule,memento=lf.apply(schedule.children[0],schedule.children[1])
fuse_schedule.view()
omp_schedule,memento=ol.apply(fuse_schedule.children[0])
omp_schedule.view()

psy.invokes.get('invoke_0')._schedule=omp_schedule

schedule=psy.invokes.get('invoke_v2_kernel_type').schedule
schedule.view()
omp_schedule,memento=ol.apply(schedule.children[0])
omp_schedule.view()

#schedule=psy.invokes.get('invoke_v1_kernel_type').schedule
#schedule.view()

print psy.gen
