# performs loop fusion on the first two loops of an invoke called
# 'invoke_0'. Does not perform any error checking.
def trans(psy):
    from transformations import LoopFuseTrans
    invoke = psy.invokes.get("invoke_0")
    schedule = invoke.schedule
    loop1 = schedule.children[0]
    loop2 = schedule.children[1]
    trans = LoopFuseTrans()
    schedule, _ = trans.apply(loop1, loop2)
    invoke.schedule = schedule
    return psy

