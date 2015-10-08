'''A module inline example script which demonstrates how to perform
inlining '''

def run():
    '''The function doing all the work. Performs loop fusing, colouring
     and adding OpenMP directives as well as inlining'''

    from parse import parse
    from psyGen import PSyFactory
    from algGen import Alg
    from psyGen import TransInfo

    api = "dynamo0.1"
    ast, invoke_info = parse("dynamo_algorithm_mod.F90", api=api)
    psy = PSyFactory(api).create(invoke_info)

    alg = Alg(ast, psy)
    print alg.gen

    print psy.gen

    print psy.invokes.names

    schedule = psy.invokes.get('invoke_0').schedule
    schedule.view()

    trans = TransInfo()
    print trans.list

    loop_fuse = trans.get_trans_name('LoopFuse')
    omp_loop = trans.get_trans_name('OpenMPLoop')
    loop_colour = trans.get_trans_name('LoopColour')
    mod_inline = trans.get_trans_name('KernelModuleInline')

    schedule.view()
    fuse_schedule, _ = loop_fuse.apply(schedule.children[0],
                                       schedule.children[1])
    fuse_schedule.view()

    psy.invokes.get('invoke_0').schedule = fuse_schedule
    print psy.gen

    fuse_schedule.view()
    omp_schedule, _ = omp_loop.apply(fuse_schedule.children[0])
    omp_schedule.view()

    psy.invokes.get('invoke_0').schedule = omp_schedule
    print psy.gen

    omp_schedule.view()
    ki_schedule, _ = mod_inline.apply(
        omp_schedule.children[0].children[0].children[0])
    ki_schedule.view()

    psy.invokes.get('invoke_0').schedule = ki_schedule
    print psy.gen

    # v2 invoke

    schedule = psy.invokes.get('invoke_v2_kernel_type').schedule
    schedule.view()
    lc_schedule, _ = loop_colour.apply(schedule.children[0])
    lc_schedule.view()

    psy.invokes.get('invoke_v2_kernel_type').schedule = lc_schedule
    print psy.gen

    lc_schedule.view()
    lc_omp_schedule, _ = omp_loop.apply(lc_schedule.children[0].children[0])
    lc_omp_schedule.view()

    psy.invokes.get('invoke_v2_kernel_type').schedule = lc_omp_schedule
    print psy.gen

    # v1 invoke

    schedule = psy.invokes.get('invoke_v1_kernel_type').schedule
    schedule.view()
    lc_schedule, _ = loop_colour.apply(schedule.children[0])
    lc_schedule.view()

    lc_omp_schedule, _ = omp_loop.apply(lc_schedule.children[0].children[0])
    lc_omp_schedule.view()

    psy.invokes.get('invoke_v1_kernel_type').schedule = lc_omp_schedule
    print psy.gen

# export PYTHONPATH=/home/rupert/proj/GungHoSVN/PSyclone_r1895_module_inline/
# f2py_88:/home/rupert/proj/GungHoSVN/PSyclone_r1895_module_inline/src:
# ${PYTHONPATH}

if __name__ == "__main__":
    run()
