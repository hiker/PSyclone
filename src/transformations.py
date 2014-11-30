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
        return "A test transformation that swaps two adjacent elements in a schedule"
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

        # find the position of nodes in the schedule
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
        # check loop1 and loop2 have the same parent
        if not node1.sameParent(node2):
            raise Exception("Error in LoopFuse transformation. loops do not have the same parent")
        # check node1 and node2 are next to each other
        if abs(node1.position-node2.position)!=1:
            raise Exception("Error in LoopFuse transformation. nodes are not siblings who are next to eachother")
        # Check iteration space is the same
        if not(node1.loop_space == node2.loop_space):
            raise Exception("Error in LoopFuse transformation. loops do not have the same iteration space")

        schedule=node1.root

        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule,self,[node1,node2])

        # add loop contents of node2 to node1
        node1.children.extend(node2.children)

        # change the parent of the loop contents of node2 to node1
        for child in node2.children:
            child.parent = node1

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
        return "Add an OpenMP directive with no validity checks"

    def apply(self,node):

        schedule=node.root
        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule,self,[node])

        # keep a reference to the node's original parent and its index as these
        # are required and will change when we change the node's location
        node_parent = node.parent
        node_position = node.position

        # add our OpenMP loop directive setting its parent to the node's
        # parent and its children to the node
        from psyGen import OMPLoopDirective
        directive = OMPLoopDirective(parent = node_parent, children = [node] )

        # add the OpenMP loop directive as a child of the node's parent
        node_parent.addchild(directive, index = node_position)

        # change the node's parent to be the loop directive
        node.parent = directive

        # remove the original loop
        node_parent.children.remove(node)

        return schedule,keep

class DynamoOpenMPLoop(OpenMPLoop):

    ''' Dynamo specific OpenMP loop transformation. Adds Dynamo specific
        validity checks. Actual transformation is done by parent class. '''

    @property
    def name(self):
        return "DynamoOpenMPLoop"

    def __str__(self):
        return "Add an OpenMP directive to a Dynamo loop"

    def apply(self,node):

        ''' Perform Dynamo specific loop validity checks then call the parent
            class. '''
        # check node is a loop
        from psyGen import Loop
        if not isinstance(node,Loop):
            raise Exception("Error in "+self.name+" transformation. The node is not a loop.")
        # Check iteration space is supported - only cells at the moment
        if not node.loop_space == "cells":
            raise Exception("Error in "+self.name+" transformation. The iteration space is not 'cells'.")
        # Check we do not need colouring
        if node.field_space != "v3" and node.loop_type is None:
            raise Exception("Error in "+self.name+" transformation. The field space written to by the kernel is not 'v3'. Colouring is required.")
        # Check we are not a sequential loop
        if node.loop_type == 'colours':
            raise Exception("Error in "+self.name+" transformation. The requested loop is over colours and must be computed serially.")
        return OpenMPLoop.apply(self,node)

class GOceanOpenMPLoop(OpenMPLoop):

    ''' GOcean specific OpenMP loop transformation. Adds GOcean specific
        validity checks. Actual transformation is done by parent class. '''

    @property
    def name(self):
        return "GOceanOpenMPLoop"

    def __str__(self):
        return "Add an OpenMP directive to a GOcean loop"

    def apply(self,node):

        ''' Perform GOcean specific loop validity checks then call the parent
            class. '''
        # check node is a loop
        from psyGen import Loop
        if not isinstance(node,Loop):
            raise Exception("Error in "+self.name+" transformation. The node is not a loop.")
        # Check we are either an inner or outer loop
        if node.loop_type not in ["inner","outer"]:
            raise Exception("Error in "+self.name+" transformation. The requested loop is not of type inner or outer.")

        return OpenMPLoop.apply(self,node)

class ColourTrans(Transformation):

    def __str__(self):
        return "Split a loop into colours"

    @property
    def name(self):
        return "LoopColour"

    def apply(self,node):

        # check node is a loop
        from psyGen import Loop
        if not isinstance(node,Loop):
            raise Exception("Error in LoopColour transformation. The node is not a loop")
        # Check iteration space is supported - only cells at the moment
        if not node.loop_space == "cells":
            raise Exception("Error in "+self.name+" transformation. The iteration space is not 'cells'.")
        # Check we need colouring
        if node.field_space == "v3":
            raise Exception("Error in "+self.name+" transformation. The field space written to by the kernel is 'v3'. Colouring is not required.")
        # Check this is a kernel loop
        if node.loop_type is not None:
            raise Exception("Error in "+self.name+" transformation. The loop is not the correct type for colouring.")

        schedule=node.root

        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule,self,[node])

        # TODO CAN WE CREATE A GENERIC LOOP OR DO WE NEED SPECIFIC GH or GO LOOPS?
        node_parent = node.parent
        node_position = node.position

        from dynamo0p1 import DynLoop

        # create a colours loop. This loops over colours and must be run
        # sequentially
        colours_loop = DynLoop(parent = node_parent)
        colours_loop.loop_type="colours"
        colours_loop.field_space=node.field_space
        colours_loop.loop_space=node.loop_space
        node_parent.addchild(colours_loop,
                             index = node_position)

        # create a colour loop. This loops over a particular colour and
        # can be run in parallel
        colour_loop = DynLoop(parent = colours_loop)
        colour_loop.loop_type="colour"
        colour_loop.field_space=node.field_space
        colour_loop.loop_space=node.loop_space
        colours_loop.addchild(colour_loop)

        # add contents of node to colour loop
        colour_loop.children.extend(node.children)

        # change the parent of the node's contents to the colour loop
        for child in node.children:
            child.parent = colour_loop

        # remove original loop
        node_parent.children.remove(node)

        return schedule,keep

class GOceanChangeLoopSpaceTrans(Transformation):

    def __str__(self):
        return "Change the space that a loop iterates over"

    @property
    def name(self):
        return "GOceanChangeLoopSpace"

    def apply(self, node, iteration_space):

        # check node is a loop
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise Exception("Error in GOceanChangeLoopSpace transformation. The node is not a loop")
        # check node is an outer loop (as we will propogate the change
        # to the innner loop)
        if not node.loop_type == "outer":
            raise Exception("Error in GOceanChangeLoopSpace transformation. The node is not an outer loop")
        if not len(node.children) == 1:
            raise Exception("Error in GOceanChangeLoopSpace transformation. The outer loop has more than one child node")
        elif not isinstance(node.children[0], Loop):
            raise Exception("Error in GOceanChangeLoopSpace transformation. The child of the outer loop is not a loop")
        elif not node.children[0].loop_type == "inner":
            raise Exception("Error in GOceanChangeLoopSpace transformation. The child of the outer loop is not an inner loop")

        schedule = node.root
        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep=Memento(schedule, self, [node, iteration_space])

        # change the outer loop space
        node.loop_space = iteration_space
        # change the inner loop space
        node.children[0].loop_space = iteration_space
        # return new schedule and a memento
        return schedule, keep
