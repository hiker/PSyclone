from parse import parse
from psyGen import PSyFactory
from transformations import SwapTrans, LoopFuseTrans, GOceanOpenMPLoop, \
                            GOceanChangeLoopSpaceTrans
import os
import pytest

class TestTransformationsGHProto:

    @pytest.mark.xfail(reason="bug 3")
    def test_swap_trans(self):
        ''' test of a (test) swap transformation which swaps two entries in a schedule '''
        ast,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","gunghoproto","3_two_functions_shared_arguments.f90"), api = "gunghoproto" )
        psy=PSyFactory("gunghoproto").create(info)
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

    @pytest.mark.xfail(reason="bug 3")
    def test_loop_fuse_trans(self):
        ''' test of the loop-fuse transformation '''
        ast,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","gunghoproto","3_two_functions_shared_arguments.f90"), api = "gunghoproto")
        psy=PSyFactory("gunghoproto").create(info)
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

class TestTransformationsGOcean:

    def test_loop_space_trans(self):
        ''' test that the loop space transformation works '''
        ast, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files", "gocean0p1", "openmp_fuse_test.f90"), api="gocean" )
        psy = PSyFactory("gocean").create(info)
        invokes = psy.invokes
        invoke_1 = invokes.get("invoke_1")
        schedule_1 = invoke_1.schedule
        u_loop_outer = schedule_1.children[0]
        v_loop_outer = schedule_1.children[1]

        lstrans = GOceanChangeLoopSpaceTrans()
        lftrans = LoopFuseTrans()

        # error if unknown iteration space
        with pytest.raises(AssertionError):
            schedule, memento = lstrans.apply(u_loop_outer, "UNDEF")
        # change spaces directly. Not recommended as we can end up with
        # inner and outer iterations not matching if both are not changed.
        u_loop_outer.loop_space = "ct"
        u_loop_outer.children[0].loop_space = "ct"
        # change space via transformation (recommended)
        schedule, memento = lstrans.apply(v_loop_outer, "ct")
        # can we successfully fuse?
        schedule, memento = lftrans.apply(u_loop_outer, v_loop_outer)
        u_loop_inner = schedule.children[0].children[0]
        v_loop_inner = schedule.children[0].children[1]
        schedule, memento = lftrans.apply(u_loop_inner, v_loop_inner)
        # check correct code is generated with appropriate offsets
        gen=str(psy.gen)
        assert gen.rfind("CALL compute_u(i+1, j, u)") != -1 and \
               gen.rfind("CALL compute_v(i, j+1, v)") != -1
 
    def test_loop_fuse_trans(self):
        ''' test the loop transformation '''
        ast, info = parse(os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_files", "gocean0p1", "openmp_fuse_test.f90"), api="gocean" )
        psy = PSyFactory("gocean").create(info)
        invokes = psy.invokes
        invoke_0 = invokes.get("invoke_0")
        schedule_0 = invoke_0.schedule
        lftrans = LoopFuseTrans()
        parent_loop = schedule_0.children[0]
        child_loop = parent_loop.children[0]
        kern_call = child_loop.children[0]
        # error if nodes are not loops
        with pytest.raises(Exception):
            schedule, memento = lftrans.apply(parent_loop, kern_call)
        # error if not same parents
        with pytest.raises(Exception):
            schedule, memento = lftrans.apply(parent_loop, child_loop)

        invoke_1 = invokes.get("invoke_1")
        schedule_1 = invoke_1.schedule
        u_loop = schedule_1.children[0]
        v_loop = schedule_1.children[1]
        # error if iteration space is different
        with pytest.raises(Exception):
            schedule, memento = lftrans.apply(u_loop, v_loop)

    def test_openmp_loop_fuse_trans(self):
        ''' test of the OpenMP transformation of a fused loop '''
        ast,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","gocean0p1","openmp_fuse_test.f90"), api = "gocean")
        psy=PSyFactory("gocean").create(info)
        invokes=psy.invokes
        invoke=invokes.get('invoke_0')
        schedule=invoke.schedule
        lftrans=LoopFuseTrans()
        ompf=GOceanOpenMPLoop()

        # fuse all outer loops
        lf1_schedule,memento = lftrans.apply(schedule.children[0],
                                             schedule.children[1])
        lf2_schedule,memento = lftrans.apply(lf1_schedule.children[0],
                                             lf1_schedule.children[1])
        # fuse all inner loops
        lf3_schedule,memento = lftrans.apply(lf2_schedule.children[0].children[0],
                                             lf2_schedule.children[0].children[1])
        lf4_schedule,memento = lftrans.apply(lf3_schedule.children[0].children[0],
                                             lf3_schedule.children[0].children[1])

        # Add an OpenMP directive around the fused loop
        omp1_schedule,memento = ompf.apply(lf4_schedule.children[0])

        # Replace the original loop schedule with the transformed one
        psy.invokes.get('invoke_0')._schedule=omp1_schedule

        # Store the results of applying this code transformation as
        # a string
        gen=str(psy.gen)

        omp_do_idx = -1
        outer_do_idx = -1
        inner_do_idx = -1
        # Iterate over the lines of generated code taking the index of the first match
        for idx,line in enumerate(gen.split('\n')):
            if '!$omp parallel do' in line and omp_do_idx == -1: omp_do_idx = idx
            if 'DO j=' in line and  outer_do_idx == -1: outer_do_idx = idx
            if 'DO i=' in line and inner_do_idx == -1: inner_do_idx = idx

        # The OpenMP 'parallel do' directive must occur immediately before
        # the DO loop itself
        assert outer_do_idx-omp_do_idx==1 and outer_do_idx-inner_do_idx==-1

    def test_openmp_loop_trans(self):
        ''' test of the OpenMP transformation of an all-points loop '''
        ast,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","gocean0p1","openmp_fuse_test.f90"), api = "gocean")
        psy=PSyFactory("gocean").create(info)
        invokes=psy.invokes
        invoke=invokes.get('invoke_0')
        schedule=invoke.schedule
        ompf=GOceanOpenMPLoop()

        omp1_schedule,memento = ompf.apply(schedule.children[0])

        # Replace the original loop schedule with the transformed one
        psy.invokes.get('invoke_0')._schedule=omp1_schedule

        # Store the results of applying this code transformation as
        # a string
        gen=str(psy.gen)

        omp_do_idx = -1
        outer_do_idx = -1
        inner_do_idx = -1
        # Iterate over the lines of generated code
        for idx,line in enumerate(gen.split('\n')):
            if '!$omp parallel do' in line and omp_do_idx == -1: omp_do_idx = idx
            if 'DO j=' in line and outer_do_idx == -1: outer_do_idx = idx
            if 'DO i=' in line and inner_do_idx == -1: inner_do_idx = idx

        # The OpenMP 'parallel do' directive must occur immediately before
        # the DO loop itself
        assert outer_do_idx - omp_do_idx == 1 and inner_do_idx - outer_do_idx == 1

