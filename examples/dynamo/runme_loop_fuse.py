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
schedule=psy.invokes.get('invoke_0').schedule
print schedule
schedule.view()

from psyGen import transformations
t=transformations()
print t.list
lf=t.getTransNum(1) # or lf=t.getTransNum('LoopFuse')
newschedule,memento=lf.apply(schedule.children[0],schedule.children[1])
psy.invokes.get('invoke_0')._schedule=schedule
print psy.gen
