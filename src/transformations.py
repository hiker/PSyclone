from psyGen import Transformation

class SwapTrans(Transformation):
    ''' A test transformation. This swaps two entries in a schedule. These entries must be siblings and next to eachother in the schedule.

        For example:

        >>> schedule=[please see schedule class for information]
        >>> print schedule
        >>> loop1=schedule.children[0]
        >>> loop2=schedule.children[1]
        >>> trans=SwapTrans()
        >>> newSchedule,memento=SwapTrans.apply(loop1,loop2)
        >>> print newSchedule

    '''
    def __init__(self):
        pass
    def __str__(self):
        return "A test transformation that swaps to adjacent elements in a schedule"
    @property
    def name(self):
        return "SwapTrans"

    def apply(self,node1,node2):

        # First perform any validity checks

        # TBD check node1 and node2 are in the same schedule
        if not node1.sameRoot(node2):
            raise Exception("Error in transformation. nodes are not in the same schedule")
        # TBD check node1 and node2 have the same parent
        if not node1.sameParent(node2):
            raise Exception("Error in transformation. nodes do not have the same parent")
        # TBD check node1 and node2 are next to each other
        if abs(node1.position-node2.position)!=1:
            raise Exception("Error in transformation. nodes are not siblings who are next to eachother")

        schedule=node1.root

        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule,self,[node1,node2])

        # find the nodes in the schedule
        index1=node1.parent.children.index(node1)
        index2=node2.parent.children.index(node2)

        # swap nodes
        node1.parent.children[index1]=node2
        node2.parent.children[index2]=node1

        return schedule,keep

class LoopFuseTrans(Transformation):

    def __str__(self):
        return "Fuse two adjacent loops together"

    @property
    def name(self):
        return "LoopFuse"

    def apply(self,node1,node2):

        # check nodes are loops
        from psyGen import Loop
        if not isinstance(node1,Loop) or not isinstance(node2,Loop):
            raise Exception("Error in LoopFuse transformation. at least one of the nodes is not a loop")
        # check node1 and node2 have the same parent
        if not node1.sameParent(node2):
            raise Exception("Error in LoopFuse transformation. nodes do not have the same parent")
        # check node1 and node2 are next to each other
        if abs(node1.position-node2.position)!=1:
            raise Exception("Error in LoopFuse transformation. nodes are not siblings who are next to eachother")
        # TBD Check iteration space is the same

        schedule=node1.root

        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule,self,[node1,node2])

        # add loop contents of node2 to node1
        node1.children.extend(node2.children)

        # remove node2
        node2.parent.children.remove(node2)

        return schedule,keep

class OpenMPLoop(Transformation):

    ''' Adds an OMP directive to a loop. 

        For example:

        >>> from parse import parse
        >>> from psyGen import PSyFactory
        >>> ast,invokeInfo=parse("dynamo.F90")
        >>> psy=PSyFactory("dynamo0.1").create(invokeInfo)
        >>> schedule=psy.invokes.get('invoke_v3_kernel_type').schedule
        >>> schedule.view()
        >>>
        >>> from transformations import OpenMPLoop
        >>> trans=OpenMPLoop()
        >>> new_schedule,memento=trans.apply(schedule.children[0])
        >>> new_schedule.view()

    '''

    @property
    def name(self):
        return "OpenMPLoop"

    def __str__(self):
        return "Add an OpenMP directive to a loop"

    def apply(self,node):

        # check node is a loop
        from psyGen import Loop
        if not isinstance(node,Loop):
            raise Exception("Error in "+self.name+" transformation. The node is not a loop.")

        schedule=node.root
        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule,self,[node])

        # colour logic here??
        

        # add our OpenMP loop directive and the loop as its child just before
        # the current loop location
        from psyGen import OMPLoopDirective
        node.parent.addchild(OMPLoopDirective(parent = node.parent,
                                              children = [node] ),
                             index = node.position)

        # remove the original loop
        node.parent.children.remove(node)

        return schedule,keep
