from parse import parse,ParseError
from psyGen import PSyFactory,GenerationError
#from algGen import Alg
api="dynamo0.1"
filename="dynamo.F90"
ast,invokeInfo=parse(filename,api=api,invoke_name="invoke")
psy=PSyFactory(api).create(invokeInfo)
print psy.gen
#alg=Alg(ast,psy)

print psy.invokes.names
schedule=psy.invokes.get('invoke_v3_kernel_type').schedule
print schedule
schedule.view()

from psyGen import TransInfo
t=TransInfo()
print t.list
ol=t.get_trans_name('OpenMPLoop')
new_schedule,memento=ol.apply(schedule.children[0])
new_schedule.view()
psy.invokes.get('invoke_v3_kernel_type')._schedule=schedule
print psy.gen
