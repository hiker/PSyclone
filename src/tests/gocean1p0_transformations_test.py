# -------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -------------------------------------------------------------------------
# Authors R. Ford and A. R. Porter, STFC Daresbury Lab

''' Module containing tests of Transformations when using the
    GOcean 1.0 API '''

from parse import parse
from psyGen import PSyFactory
from transformations import TransformationError,\
                            LoopFuseTrans, OMPParallelTrans,\
                            GOceanLoopFuseTrans,\
                            GOceanOMPParallelLoopTrans,\
                            GOceanOMPLoopTrans
from generator import GenerationError
import os
import pytest

API = "gocean1.0"


def get_invoke(algfile, idx):
    ''' Utility method to get the idx'th invoke from the algorithm
    specified in file '''
    _, info = parse(os.path.
                    join(os.path.dirname(os.path.abspath(__file__)),
                         "test_files", "gocean1p0",
                         algfile),
                    api=API)
    psy = PSyFactory(API).create(info)
    invokes = psy.invokes
    # invokes does not have a method by which to request the i'th
    # in the list so we do this rather clumsy lookup of the name
    # of the invoke that we want
    invoke = invokes.get(invokes.names[idx])
    return psy, invoke


def test_loop_fuse_different_iterates_over():
    ''' Test that an appropriate error is raised when we attempt to
    fuse two loops that have differing values of ITERATES_OVER '''
    _, invoke = get_invoke("test11_different_iterates_over_"
                           "one_invoke.f90", 0)
    schedule = invoke.schedule
    lftrans = LoopFuseTrans()

    # Attempt to fuse two loops that are iterating over different
    # things
    with pytest.raises(TransformationError):
        _, _ = lftrans.apply(schedule.children[0],
                             schedule.children[1])


def test_omp_region_with_wrong_arg_type():
    ''' Test that the OpenMP PARALLEL region transformation
        raises an appropriate error if passed something that is not
        a list of Nodes or a single Node. '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)

    ompr = OMPParallelTrans()

    with pytest.raises(TransformationError):
        _, _ = ompr.apply(invoke)


def test_omp_region_with_single_loop():
    ''' Test that we can pass the OpenMP PARALLEL region transformation
        a single node in a schedule '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompr = OMPParallelTrans()

    omp_schedule, _ = ompr.apply(schedule.children[1])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule
    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)
    gen = gen.lower()

    # Iterate over the lines of generated code
    within_omp_region = False
    call_count = 0
    for line in gen.split('\n'):
        if '!$omp parallel default' in line:
            within_omp_region = True
        if '!$omp end parallel' in line:
            within_omp_region = False
        if ' call ' in line and within_omp_region:
            call_count += 1

    assert call_count == 1


def test_omp_region_with_slice():
    ''' Test that we can pass the OpenMP PARALLEL region transformation
    a list of nodes specified as a slice '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompr = OMPParallelTrans()

    omp_schedule, _ = ompr.apply(schedule.children[1:])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule
    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)
    gen = gen.lower()

    # Iterate over the lines of generated code
    within_omp_region = False
    call_count = 0
    for line in gen.split('\n'):
        if '!$omp parallel default' in line:
            within_omp_region = True
        if '!$omp end parallel' in line:
            within_omp_region = False
        if ' call ' in line and within_omp_region:
            call_count += 1

    assert call_count == 2


def test_omp_region_no_slice():
    ''' Test that we can pass the OpenMP PARALLEL region transformation
    a list of nodes specified as node.children '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule
    ompr = OMPParallelTrans()
    omp_schedule, _ = ompr.apply(schedule.children)
    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule
    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)
    gen = gen.lower()
    # Iterate over the lines of generated code
    within_omp_region = False
    call_count = 0
    for line in gen.split('\n'):
        if '!$omp parallel default' in line:
            within_omp_region = True
        if '!$omp end parallel' in line:
            within_omp_region = False
        if ' call ' in line and within_omp_region:
            call_count += 1

    assert call_count == 3


def test_omp_region_retains_kernel_order1():
    ''' Test that applying the OpenMP PARALLEL region transformation
    to a sub-set of nodes (last 2 of three) does not change their
    ordering '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompr = OMPParallelTrans()

    omp_schedule, _ = ompr.apply(schedule.children[1:])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule
    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)
    gen = gen.lower()

    # Iterate over the lines of generated code
    cu_idx = -1
    cv_idx = -1
    ts_idx = -1
    for idx, line in enumerate(gen.split('\n')):
        if 'call compute_cu' in line:
            cu_idx = idx
        if 'call compute_cv' in line:
            cv_idx = idx
        if 'call time_smooth' in line:
            ts_idx = idx

    # Kernels should be in order {compute_cu, compute_cv, time_smooth}
    assert cu_idx < cv_idx and cv_idx < ts_idx


def test_omp_region_retains_kernel_order2():
    ''' Test that applying the OpenMP PARALLEL region transformation
    to a sub-set of nodes (first 2 of 3) does not change their
    ordering '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompr = OMPParallelTrans()

    omp_schedule, _ = ompr.apply(schedule.children[0:2])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule
    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)
    gen = gen.lower()

    # Iterate over the lines of generated code
    cu_idx = -1
    cv_idx = -1
    ts_idx = -1
    for idx, line in enumerate(gen.split('\n')):
        if 'call compute_cu' in line:
            cu_idx = idx
        if 'call compute_cv' in line:
            cv_idx = idx
        if 'call time_smooth' in line:
            ts_idx = idx

    # Kernels should be in order {compute_cu, compute_cv, time_smooth}
    assert cu_idx < cv_idx and cv_idx < ts_idx


def test_omp_region_retains_kernel_order3():
    ''' Test that applying the OpenMP PARALLEL region transformation
    to a sub-set of nodes (middle 1 of 3) does not change their
    ordering '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompr = OMPParallelTrans()
    ompl = GOceanOMPLoopTrans()

    # Put an OMP Do around the 2nd loop of the schedule
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Put an OMP Parallel around that single OMP Do
    schedule, _ = ompr.apply([omp_schedule.children[1]])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule
    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)
    gen = gen.lower()

    # Iterate over the lines of generated code
    cu_idx = -1
    cv_idx = -1
    ts_idx = -1
    for idx, line in enumerate(gen.split('\n')):
        if 'call compute_cu' in line:
            cu_idx = idx
        if 'call compute_cv' in line:
            cv_idx = idx
        if 'call time_smooth' in line:
            ts_idx = idx

    # Kernels should be in order {compute_cu, compute_cv, time_smooth}
    assert cu_idx < cv_idx and cv_idx < ts_idx


def test_omp_region_before_loops_trans():
    ''' Test of the OpenMP PARALLEL region transformation where
    we do the region transformation before the loop
    transformations. '''
    psy, invoke = get_invoke("single_invoke_two_kernels.f90", 0)
    schedule = invoke.schedule

    # Put all of the loops in the schedule within a single
    # OpenMP region
    ompr = OMPParallelTrans()
    omp_schedule, _ = ompr.apply(schedule.children)

    # Put an OpenMP do directive around each loop contained
    # in the region
    ompl = GOceanOMPLoopTrans()
    for child in omp_schedule.children[0].children:
        schedule, _ = ompl.apply(child)
        omp_schedule = schedule

    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule

    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)

    # Iterate over the lines of generated code
    omp_region_idx = -1
    omp_do_idx = -1
    for idx, line in enumerate(gen.split('\n')):
        if '!$omp parallel default' in line:
            omp_region_idx = idx
        if '!$omp do' in line:
            omp_do_idx = idx
        if 'DO j=' in line:
            break

    assert omp_region_idx != -1
    assert omp_do_idx != -1
    assert omp_do_idx - omp_region_idx == 1


def test_omp_region_after_loops_trans():
    ''' Test of the OpenMP PARALLEL region transformation where we
    do the loop transformations before the region transformation '''
    psy, invoke = get_invoke("single_invoke_two_kernels.f90", 0)
    schedule = invoke.schedule

    # Put an OpenMP do directive around each loop contained
    # in the schedule
    ompl = GOceanOMPLoopTrans()
    for child in schedule.children:
        omp_schedule, _ = ompl.apply(child)

    # Now put an OpenMP parallel region around that set of
    # loops
    ompr = OMPParallelTrans()
    schedule, _ = ompr.apply(omp_schedule.children)

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Store the results of applying this code transformation as
    # a string
    gen = str(psy.gen)

    # Iterate over the lines of generated code
    omp_region_idx = -1
    omp_do_idx = -1
    for idx, line in enumerate(gen.split('\n')):
        if '!$omp parallel default' in line:
            omp_region_idx = idx
        if '!$omp do' in line:
            omp_do_idx = idx
        if 'DO j=' in line:
            break

    assert omp_region_idx != -1
    assert omp_do_idx != -1
    assert omp_do_idx - omp_region_idx == 1


def test_omp_region_commutes_with_loop_trans():
    ''' Test that the OpenMP PARALLEL region and (orphan) loop
    transformations commute - i.e. we get the same result
    independent of the order in which they are applied. '''
    psy, invoke = get_invoke("single_invoke_two_kernels.f90", 0)
    schedule = invoke.schedule

    # Put an OpenMP do directive around each loop contained
    # in the schedule
    ompl = GOceanOMPLoopTrans()
    for child in schedule.children:
        omp_schedule, _ = ompl.apply(child)

    # Now put an OpenMP parallel region around that set of
    # loops
    ompr = OMPParallelTrans()
    schedule, _ = ompr.apply(omp_schedule.children)

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Store the results of applying this code transformation as
    # a string
    loop_before_region_gen = str(psy.gen)

    # Now we do it again but in the opposite order...

    # Put all of the loops in the schedule within a single
    # OpenMP region
    psy, invoke = get_invoke("single_invoke_two_kernels.f90", 0)
    schedule = invoke.schedule

    ompr = OMPParallelTrans()
    omp_schedule, _ = ompr.apply(schedule.children)

    # Put an OpenMP do directive around each loop contained
    # in the region
    ompl = GOceanOMPLoopTrans()
    for child in omp_schedule.children[0].children:
        schedule, _ = ompl.apply(child)
        omp_schedule = schedule

    # Replace the original loop schedule with the transformed one
    invoke.schedule = omp_schedule

    # Store the results of applying this code transformation as
    # a string
    region_before_loop_gen = str(psy.gen)

    assert region_before_loop_gen == loop_before_region_gen


def test_omp_region_nodes_not_children_of_same_parent():
    ''' Test that we raise appropriate error if user attempts
    to put a region around nodes that are not children of
    the same parent '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPParallelLoopTrans()
    ompr = OMPParallelTrans()

    # Put an OpenMP parallel do around the first loop in the schedule
    _, _ = ompl.apply(schedule.children[0])

    # Attempt to put an OpenMP parallel region around that same loop
    # (which is now a child of an OpenMP loop directive) and the
    # second loop in the schedule
    with pytest.raises(TransformationError):
        _, _ = ompr.apply([schedule.children[0].children[0],
                           schedule.children[1]])


def test_omp_region_nodes_not_children_of_same_schedule():
    ''' Test that we raise appropriate error if user attempts
    to put a region around nodes that are not children of
    the same schedule '''
    _, invoke1 = get_invoke("test12_two_invokes_two_kernels.f90", 0)
    schedule1 = invoke1.schedule
    _, invoke2 = get_invoke("test12_two_invokes_two_kernels.f90", 1)
    schedule2 = invoke2.schedule

    ompr = OMPParallelTrans()

    # Attempt to put an OpenMP parallel region the loops from the
    # two different schedules
    with pytest.raises(TransformationError):
        _, _ = ompr.apply([schedule1.children[0],
                           schedule2.children[0]])


def test_omp_loop_outside_region():
    ''' Test that a generation error is raised if we try and
    have an orphaned OpenMP loop that is not enclosed
    within a parallel region '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    # Put an OpenMP do directive around each loop contained
    # in the schedule
    ompl = GOceanOMPLoopTrans()
    ompr = OMPParallelTrans()

    for child in schedule.children:
        omp_schedule, _ = ompl.apply(child)

    # Now enclose all but the last loop in a parallel region
    ompr_schedule, _ = ompr.apply(omp_schedule.children[0:-2])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = ompr_schedule

    # Attempt to generate the transformed code
    with pytest.raises(GenerationError):
        _ = psy.gen


def test_omp_loop_applied_to_non_loop():
    ''' Test that we raise a TransformationError if we attempt
    to apply an OMP DO transformation to something that
    is not a loop '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    from transformations import OMPLoopTrans
    ompl = OMPLoopTrans()
    omp_schedule, _ = ompl.apply(schedule.children[0])

    # Attempt to (erroneously) apply the OMP Loop transformation
    # to the first node in the schedule (which is now itself an
    # OMP Loop transformation)
    with pytest.raises(TransformationError):
        _, _ = ompl.apply(omp_schedule.children[0])


def test_go_omp_loop_applied_to_non_loop():
    ''' Test that we raise a TransformationError if we attempt
    to apply a GOcean OMP DO transformation to something that
    is not a loop '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans()
    omp_schedule, _ = ompl.apply(schedule.children[0])

    # Attempt to (erroneously) apply the GO OMP Loop transformation
    # to the first node in the schedule (which is now itself an
    # OMP Loop transformation)
    with pytest.raises(TransformationError):
        _, _ = ompl.apply(omp_schedule.children[0])


def test_go_omp_loop_applied_to_wrong_loop_type():
    ''' Test that we raise a TransformationError if we attempt to
    apply a GOcean OMP  DO transformation to a loop of
    the wrong type '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    # Manually break the loop-type of the first loop in order to
    # test that this error is handled. We have to work-around
    # the setter method to do this since it has error checking
    # too!
    schedule.children[0]._loop_type = "wrong"

    ompl = GOceanOMPLoopTrans()
    # Attempt to apply the transformation to the loop that has been
    # given an incorrect type
    with pytest.raises(TransformationError):
        _, _ = ompl.apply(schedule.children[0])


def test_go_omp_parallel_loop_applied_to_non_loop():
    ''' Test that we raise a TransformationError if we attempt to
    apply a GOcean OMP Parallel DO transformation to something that
    is not a loop '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPParallelLoopTrans()
    omp_schedule, _ = ompl.apply(schedule.children[0])

    # Attempt to (erroneously) apply the OMP Loop transformation
    # to the first node in the schedule (which is now itself an
    # OMP Loop transformation)
    with pytest.raises(TransformationError):
        _, _ = ompl.apply(omp_schedule.children[0])


def test_go_omp_parallel_loop_applied_to_wrong_loop_type():
    ''' Test that we raise a TransformationError if we attempt to
    apply a GOcean OMP Parallel DO transformation to a loop of
    the wrong type '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    # Manually break the loop-type of the first loop in order to
    # test that this error is handled. We have to work-around
    # the setter method to do this since it has error checking
    # too!
    schedule.children[0]._loop_type = "wrong"

    ompl = GOceanOMPParallelLoopTrans()
    # Attempt to apply the transformation to the loop that has been
    # given an incorrect type
    with pytest.raises(TransformationError):
        _, _ = ompl.apply(schedule.children[0])


def test_omp_parallel_do_inside_parallel_region():
    ''' Test that a generation error is raised if we attempt
    to have an OpenMP parallel do within an OpenMP
    parallel region '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPParallelLoopTrans()
    ompr = OMPParallelTrans()

    # Put an OpenMP parallel do directive around all of the loops
    for child in schedule.children:
        omp_schedule, _ = ompl.apply(child)

    # Now enclose all of the children within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children)

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    with pytest.raises(GenerationError):
        _ = psy.gen


def test_omp_parallel_region_inside_parallel_do():
    ''' Test that a generation error is raised if we attempt
    to have an OpenMP parallel region within an OpenMP
    parallel do (with the latter applied first) '''
    _, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPParallelLoopTrans()
    ompr = OMPParallelTrans()

    # Put an OpenMP parallel do directive around one of the loops
    _, _ = ompl.apply(schedule.children[1])

    # Now attempt to put a parallel region inside that parallel do
    with pytest.raises(TransformationError):
        _, _ = ompr.apply([schedule.children[1].children[0]])


def test_omp_parallel_do_around_parallel_region():
    ''' Test that a generation error is raised if we attempt
    to have an OpenMP parallel region around an OpenMP
    parallel do (with the latter applied second) '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPParallelLoopTrans()
    ompr = OMPParallelTrans()

    # Put a parallel region around two of the loops
    omp_schedule, _ = ompr.apply(schedule.children[0:2])

    # Put an OpenMP parallel do directive around one of those loops
    # (which is now a child of the region directive)
    schedule, _ = ompl.apply(omp_schedule.children[0].children[0])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    with pytest.raises(GenerationError):
        _ = psy.gen


@pytest.mark.xfail(reason="OMP Region with children of different types "
                   "not yet implemented")
def test_omp_region_with_children_of_different_types():
    ''' Test that we can generate code if we have an
    OpenMP parallel region enclosing children of different types. '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans()
    ompr = OMPParallelTrans()

    # Put an OpenMP do directive around one loop
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Now enclose all of the children within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children)

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    _ = psy.gen


def test_omp_schedule_default_static():
    ''' Test that if no OMP schedule is specified then we default
    to "static" '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans()
    ompr = OMPParallelTrans()

    # Put an OpenMP do directive around one loop without specifying
    # the OMP schedule to use
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Now enclose it within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children[1])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    gen = str(psy.gen)

    assert '!$omp do schedule(static)' in gen


def test_omp_do_schedule_runtime():
    ''' Test that we can specify the schedule of an OMP do as
    "runtime" '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans(omp_schedule="runtime")
    ompr = OMPParallelTrans()

    # Put an OpenMP do directive around one loop
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Now enclose it within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children[1])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    gen = str(psy.gen)

    assert '!$omp do schedule(runtime)' in gen


def test_omp_do_schedule_dynamic():
    ''' Test that we can specify the schedule of an OMP do as
    "dynamic" '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans(omp_schedule="dynamic")
    ompr = OMPParallelTrans()

    # Put an OpenMP do directive around one loop
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Now enclose it within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children[1])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    gen = str(psy.gen)

    assert '!$omp do schedule(dynamic)' in gen


def test_omp_do_schedule_guided():
    ''' Test that we can specify the schedule of an OMP do as
    "guided" '''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans(omp_schedule="guided")
    ompr = OMPParallelTrans()

    # Put an OpenMP do directive around one loop
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Now enclose it within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children[1])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    gen = str(psy.gen)

    assert '!$omp do schedule(guided)' in gen


def test_omp_schedule_guided_with_empty_chunk():
    ''' Test that we raise an appropriate error if we miss off
    the chunksize '''
    with pytest.raises(TransformationError):
        _ = GOceanOMPLoopTrans(omp_schedule="guided, ")


def test_omp_schedule_guided_with_chunk():
    ''' Test that we can specify the schedule of an OMP do as
    "guided,n" where n is some chunk size'''
    psy, invoke = get_invoke("single_invoke_three_kernels.f90", 0)
    schedule = invoke.schedule

    ompl = GOceanOMPLoopTrans(omp_schedule="guided,10")
    ompr = OMPParallelTrans()

    # Put an OpenMP do directive around one loop
    omp_schedule, _ = ompl.apply(schedule.children[1])

    # Now enclose it within a parallel region
    schedule, _ = ompr.apply(omp_schedule.children[1])

    # Replace the original loop schedule with the transformed one
    invoke.schedule = schedule

    # Attempt to generate the transformed code
    gen = str(psy.gen)

    assert '!$omp do schedule(guided,10)' in gen


def test_omp_invalid_schedule():
    ''' Test that we raise an appropriate error if we specify
    an invalid omp schedule '''
    with pytest.raises(TransformationError):
        _ = GOceanOMPLoopTrans(omp_schedule="rubbish")


def test_omp_schedule_auto_with_chunk():
    ''' Test that we raise an appropriate error if we specify
    the omp schedule as "auto" but try to provide a chunk size '''
    with pytest.raises(TransformationError):
        _ = GOceanOMPLoopTrans(omp_schedule="auto,4")
