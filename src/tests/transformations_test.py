from parse import parse
from psyGen import PSy
from transformations import SwapTrans, LoopFuseTrans
import os

class TestTransformations:

    def test_swap_trans(self):
        ''' test of a (test) swap transformation which swaps two entries in a schedule '''
        ast,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","gunghoproto","3_two_functions_shared_arguments.f90"), api = "gunghoproto" )
        psy=PSy(info)
        invokes=psy.invokes
        invoke=invokes.get("invoke_0")
        schedule=invoke.schedule
        loop1=schedule.children[0]
        loop2=schedule.children[1]
        trans=SwapTrans()
        schedule,memento=trans.apply(loop1,loop2)
        gen=str(psy.gen)
        # testkern1_code call should now be after testkern2_code call
        assert gen.rfind("testkern1_code")>gen.rfind("testkern2_code")

    def test_loop_fuse_trans(self):
        ''' test of the loop-fuse transformation '''
        ast,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","gunghoproto","3_two_functions_shared_arguments.f90"), api = "gunghoproto")
        psy=PSy(info)
        invokes=psy.invokes
        invoke=invokes.get("invoke_0")
        schedule=invoke.schedule
        loop1=schedule.children[0]
        loop2=schedule.children[1]
        trans=LoopFuseTrans()
        schedule,memento=trans.apply(loop1,loop2)
        gen=str(psy.gen)
        for idx,line in enumerate(gen.split('\n')):
            if line.find("DO column=1,topology")!=-1: do_idx=idx
            if line.find("CALL testkern1_code(")!=-1: call1_idx=idx
            if line.find("CALL testkern2_code(")!=-1: call2_idx=idx
            if line.find("END DO")!=-1: enddo_idx=idx
        # 4 lines should be in sequence as calls have been fused into one loop
        assert enddo_idx-call2_idx==1 and call2_idx-call1_idx==1 and call1_idx-do_idx==1
