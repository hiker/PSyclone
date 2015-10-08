# -------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab
#        A. Porter STFC Daresbury Lab

''' This module provides the various transformations that can
    be applied to the schedule associated with an invoke(). There
    are both general and API-specific transformation classes in
    this module where the latter typically apply API-specific
    checks before calling the base class for the actual
    transformation. '''

from psyGen import Transformation

VALID_OMP_SCHEDULES = ["runtime", "static", "dynamic", "guided", "auto"]


class TransformationError(Exception):
    ''' Provides a PSyclone-specific error class for errors found during
        code transformation operations. '''

    def __init__(self, value):
        Exception.__init__(self, value)
        self.value = "Transformation Error: "+value

    def __str__(self):
        return repr(self.value)


class LoopFuseTrans(Transformation):
    ''' Provides a loop-fuse transformation.
        For example:

        >>> from parse import parse
        >>> from psyGen import PSyFactory
        >>> ast,invokeInfo=parse("dynamo.F90")
        >>> psy=PSyFactory("dynamo0.1").create(invokeInfo)
        >>> schedule=psy.invokes.get('invoke_v3_kernel_type').schedule
        >>> schedule.view()
        >>>
        >>> from transformations import LoopFuseTrans
        >>> trans=LoopFuseTrans()
        >>> new_schedule,memento=trans.apply(schedule.children[0],
                                             schedule.children[1])
        >>> new_schedule.view()
    '''

    def __str__(self):
        return "Fuse two adjacent loops together"

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "LoopFuse"

    def apply(self, node1, node2):
        ''' Fuse the loops represented by :py:obj:`node1` and
        :py:obj:`node2` '''
        # check nodes are loops
        from psyGen import Loop
        if not isinstance(node1, Loop) or not isinstance(node2, Loop):
            raise TransformationError("Error in LoopFuse transformation. "
                                      "At least one of the nodes is not "
                                      "a loop")
        # check loop1 and loop2 have the same parent
        if not node1.sameParent(node2):
            raise TransformationError("Error in LoopFuse transformation. "
                                      "loops do not have the same parent")
        # check node1 and node2 are next to each other
        if abs(node1.position-node2.position) != 1:
            raise TransformationError("Error in LoopFuse transformation. "
                                      "nodes are not siblings who are "
                                      "next to eachother")
        # Check iteration space is the same
        if not node1.iteration_space == node2.iteration_space:
            raise TransformationError("Error in LoopFuse transformation. "
                                      "Loops do not have the same "
                                      "iteration space")

        schedule = node1.root

        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep = Memento(schedule, self, [node1, node2])

        # add loop contents of node2 to node1
        node1.children.extend(node2.children)

        # change the parent of the loop contents of node2 to node1
        for child in node2.children:
            child.parent = node1

        # remove node2
        node2.parent.children.remove(node2)

        return schedule, keep


class GOceanLoopFuseTrans(LoopFuseTrans):
    ''' Performs error checking before calling the
        :py:meth:`LoopFuseTrans.apply` method of the
        :py:class:`base class <LoopFuseTrans>` in order to fuse two
        GOcean loops. '''

    def __str__(self):
        return ("Fuse two adjacent loops together with GOcean-specific "
                "validity checks")

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "GOceanLoopFuse"

    def apply(self, node1, node2):
        ''' Fuse the two GOcean loops represented by :py:obj:`node1` and
        :py:obj:`node2` '''
        try:
            if node1.field_space != node2.field_space:
                raise TransformationError(
                    "Error in GOceanLoopFuse transformation. Cannot "
                    "fuse loops that are over different grid-point types: "
                    "{0} {1}".format(node1.field_space,
                                     node2.field_space))
        except TransformationError as err:
            raise err
        except Exception as err:
            raise TransformationError("Unexpected exception: {0}".
                                      format(err))

        return LoopFuseTrans.apply(self, node1, node2)


class DynamoLoopFuseTrans(LoopFuseTrans):
    '''Performs error checking before calling the
        :py:meth:`~LoopFuseTrans.apply` method of the
        :py:class:`base class <LoopFuseTrans>` in order
        to fuse two Dynamo loops.

    '''

    def __str__(self):
        return ("Fuse two adjacent loops together with Dynamo-specific "
                "validity checks")

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "DynamoLoopFuse"

    def apply(self, node1, node2):
        ''' Fuse the two Dynamo loops represented by :py:obj:`node1`
        and :py:obj:`node2` '''
        try:
            if node1.field_space != node2.field_space:
                raise TransformationError(
                    "Error in DynamoLoopFuse transformation. "
                    "Cannot fuse loops that are over different spaces: "
                    "{0} {1}".format(node1.field_space,
                                     node2.field_space))
        except TransformationError as err:
            raise err
        except Exception as err:
            raise TransformationError("Unexpected exception: {0}".\
                                      format(err))
        return LoopFuseTrans.apply(self, node1, node2)


class OMPLoopTrans(Transformation):

    ''' Adds an orphaned OpenMP directive to a loop. i.e. the directive
        must be inside the scope of some other OMP Parallel REGION. This
        condition is tested at code-generation time.
        For example:

        >>> from parse import parse,ParseError
        >>> from psyGen import PSyFactory,GenerationError
        >>> api="gocean1.0"
        >>> filename="nemolite2d_alg.f90"
        >>> ast,invokeInfo=parse(filename,api=api,invoke_name="invoke")
        >>> psy=PSyFactory(api).create(invokeInfo)
        >>> print psy.invokes.names
        >>>
        >>> from psyGen import TransInfo
        >>> t=TransInfo()
        >>> ltrans = t.get_trans_name('OMPLoopTrans')
        >>> rtrans = t.get_trans_name('OMPParallelTrans')
        >>>
        >>> schedule=psy.invokes.get('invoke_0').schedule
        >>> schedule.view()
        >>> new_schedule=schedule
        >>>
        # Apply the OpenMP Loop transformation to *every* loop
        # in the schedule
        >>> for child in schedule.children:
        >>>     newschedule,memento=ltrans.apply(child)
        >>>     schedule = newschedule
        >>>
        # Enclose all of these loops within a single OpenMP
        # PARALLEL region
        >>> rtrans.omp_schedule("dynamic,1")
        >>> newschedule,memento = rtrans.apply(schedule.children)
        >>>
        >>>

    '''
    def __str__(self):
        return "Adds an 'OpenMP DO' directive to a loop"

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "OMPLoopTrans"

    @property
    def omp_schedule(self):
        ''' Returns the OpenMP schedule that will be specified by
            this transformation. The default schedule is 'static' '''
        return self._omp_schedule

    @omp_schedule.setter
    def omp_schedule(self, value):
        ''' Sets the OpenMP schedule that will be specified by
            this transformation. Checks that the string supplied in
            :py:obj:`value` is a recognised OpenMP schedule. '''

        # Some schedules have an optional chunk size following a ','
        value_parts = value.split(',')
        if value_parts[0].lower() not in VALID_OMP_SCHEDULES:
            raise TransformationError("Valid OpenMP schedules are {0} "
                                      "but got {1}".
                                      format(VALID_OMP_SCHEDULES,
                                             value_parts[0]))
        if len(value_parts) > 1:
            if value_parts[0] == "auto":
                raise TransformationError("Cannot specify a chunk size "
                                          "when using an OpenMP schedule"
                                          " of 'auto'")
            elif value_parts[1].strip() == "":
                raise TransformationError("Supplied OpenMP schedule '{0}'"
                                          " has missing chunk-size.".
                                          format(value))

        self._omp_schedule = value

    def __init__(self, omp_schedule="static"):
        self._omp_schedule = ""
        # Although we create the _omp_schedule attribute above (so that
        # pylint doesn't complain), we actually set its value using
        # the setter method in order to make use of the latter's error
        # checking.
        self.omp_schedule = omp_schedule
        Transformation.__init__(self)

    def apply(self, node):
        '''Apply the OMPLoopTrans transformation to the specified node in a
        Schedule. This node must be a Loop since this transformation
        corresponds to wrapping the generated code with directives like so:

        .. code-block:: fortran

          !$OMP DO
          do ...
             ...
          end do
          !$OMP END DO

        At code-generation time (when
        :py:meth:`OMPLoopTrans.gen_code` is called), this node must be
        within (i.e. a child of) an OpenMP PARALLEL region.

        '''
        # Check that the supplied node is a Loop
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Cannot apply an OpenMP Loop "
                                      "directive to something that is "
                                      "not a loop")
        # Check we are not a sequential loop
        if node.loop_type == 'colours':
            raise TransformationError("Error in "+self.name+" transformation. "
                                      "The target loop is over colours and "
                                      "must be computed serially.")

        schedule = node.root

        # create a memento of the schedule and the proposed
        # transformation
        from undoredo import Memento
        keep = Memento(schedule, self, [node])

        # keep a reference to the node's original parent and its index as these
        # are required and will change when we change the node's location
        node_parent = node.parent
        node_position = node.position

        # add our orphan OpenMP loop directive setting its parent to
        # the node's parent and its children to the node
        from psyGen import OMPDoDirective
        directive = OMPDoDirective(parent=node_parent,
                                   children=[node],
                                   omp_schedule=self.omp_schedule)

        # add the OpenMP loop directive as a child of the node's parent
        node_parent.addchild(directive, index=node_position)

        # change the node's parent to be the loop directive
        node.parent = directive

        # remove the original loop
        node_parent.children.remove(node)

        return schedule, keep


class OMPParallelLoopTrans(OMPLoopTrans):

    ''' Adds an OpenMP PARALLEL DO directive to a loop.

        For example:

        >>> from parse import parse
        >>> from psyGen import PSyFactory
        >>> ast,invokeInfo=parse("dynamo.F90")
        >>> psy=PSyFactory("dynamo0.1").create(invokeInfo)
        >>> schedule=psy.invokes.get('invoke_v3_kernel_type').schedule
        >>> schedule.view()
        >>>
        >>> from transformations import OMPParallelLoopTrans
        >>> trans=OMPParallelLoopTrans()
        >>> new_schedule,memento=trans.apply(schedule.children[0])
        >>> new_schedule.view()

    '''

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "OMPParallelLoopTrans"

    def __str__(self):
        return "Add an 'OpenMP PARALLEL DO' directive with no validity checks"

    def apply(self, node):
        ''' Apply an OMPParallelLoop Transformation to the supplied node
        (which must be a Loop). In the generated code this corresponds to
        wrapping the Loop with directives:

        .. code-block:: fortran

          !$OMP PARALLEL DO ...
          do ...
            ...
          end do
          !$OMP END PARALLEL DO

        '''
        # Check that the supplied Node is a Loop
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Error in {0} transformation. The "
                                      "node is not a loop.".format(self.name))

        # Check we are not a sequential loop
        if node.loop_type == 'colours':
            raise TransformationError("Error in "+self.name+" transformation. "
                                      "The requested loop is over colours and "
                                      "must be computed serially.")

        schedule = node.root
        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep = Memento(schedule, self, [node])

        # keep a reference to the node's original parent and its index as these
        # are required and will change when we change the node's location
        node_parent = node.parent
        node_position = node.position

        # add our OpenMP loop directive setting its parent to the node's
        # parent and its children to the node
        from psyGen import OMPParallelDoDirective
        directive = OMPParallelDoDirective(parent=node_parent,
                                           children=[node],
                                           omp_schedule=self.omp_schedule)

        # add the OpenMP loop directive as a child of the node's parent
        node_parent.addchild(directive, index=node_position)

        # change the node's parent to be the loop directive
        node.parent = directive

        # remove the original loop
        node_parent.children.remove(node)

        return schedule, keep


class DynamoOMPParallelLoopTrans(OMPParallelLoopTrans):

    ''' Dynamo-specific OpenMP loop transformation. Adds Dynamo specific
        validity checks. Actual transformation is done by the
        :py:class:`base class <OMPParallelLoopTrans>`.

    '''

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "DynamoOMPParallelLoopTrans"

    def __str__(self):
        return "Add an OpenMP Parallel Do directive to a Dynamo loop"

    def apply(self, node):

        ''' Perform Dynamo specific loop validity checks then call the
        :py:meth:`~OMPParallelLoopTrans.apply` method of the
        :py:class:`base class <OMPParallelLoopTrans>`. '''
        # Check that the supplied node is a loop - although this check
        # is not Dynamo specific it is necessary for the subsequent
        # checks to function correctly (only a loop object has an
        # iteration_space for instance).
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Error in {0} transformation. The "
                                      "node is not a loop.".format(self.name))
        # Check iteration space is supported - only cells at the moment
        if not node.iteration_space == "cells":
            raise TransformationError("Error in {0} transformation. The "
                                      "iteration space is not 'cells'.".\
                                      format(self.name))
        # If the loop is not already coloured then check whether or not
        # it should be. If the field space is W3 then we don't need
        # to worry about colouring.
        if node.field_space != "w3":
            if node.loop_type is not 'colour' and node.has_inc_arg():
                raise TransformationError(
                    "Error in {0} transformation. The kernel has an "
                    "argument with INC access. Colouring is required.".\
                    format(self.name))

        return OMPParallelLoopTrans.apply(self, node)


class GOceanOMPParallelLoopTrans(OMPParallelLoopTrans):

    '''GOcean specific OpenMP Do loop transformation. Adds GOcean
        specific validity checks. Actual transformation is done by
        :py:class:`base class <OMPParallelLoopTrans>`.

    '''

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "GOceanOMPParallelLoopTrans"

    def __str__(self):
        return "Add an OpenMP Parallel Do directive to a GOcean loop"

    def apply(self, node):

        ''' Perform GOcean-specific loop validity checks then call
        :py:meth:`OMPParallelLoopTrans.apply`.

        '''

        # check node is a loop - although this check
        # is not GOcean specific, it is necessary for the subsequent
        # checks to function correctly (only a loop object has a
        # loop_type for instance).
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Error in "+self.name+" transformation."
                                      " The node is not a loop.")
        # Check we are either an inner or outer loop
        if node.loop_type not in ["inner", "outer"]:
            raise TransformationError(
                "Error in "+self.name+" transformation.  The requested loop"
                " is not of type inner or outer.")

        return OMPParallelLoopTrans.apply(self,
                                          node)


class Dynamo0p3OMPLoopTrans(OMPLoopTrans):

    ''' Dynamo 0.3 specific orphan OpenMP loop transformation. Adds
    Dynamo-specific validity checks. Actual transformation is done by
    :py:class:`base class <OMPLoopTrans>`.

    '''

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "Dynamo0p3OMPLoopTrans"

    def __str__(self):
        return "Add an OpenMP DO directive to a Dynamo 0.3 loop"

    def apply(self, node):
        '''Perform Dynamo 0.3 specific loop validity checks then call
        :py:meth:`OMPLoopTrans.apply`.

        '''
        # check node is a loop
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Error in "+self.name+" transformation."
                                      " The node is not a loop.")
        # Check iteration space is supported - only cells at the moment
        if not node.iteration_space == "cells":
            raise TransformationError("Error in {0} transformation. The "
                                      "iteration space is not 'cells'.".\
                                      format(self.name))
        # If the loop is not already coloured then check whether or not
        # it should be
        if node.loop_type is not 'colour' and node.has_inc_arg():
            raise TransformationError(
                "Error in {0} transformation. The kernel has an argument"
                " with INC access. Colouring is required.".\
                format(self.name))
        return OMPLoopTrans.apply(self, node)


class GOceanOMPLoopTrans(OMPLoopTrans):

    ''' GOcean-specific orphan OpenMP loop transformation. Adds GOcean
        specific validity checks. Actual transformation is done by
        :py:class:`base class <OMPLoopTrans>`.

    '''

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "GOceanOMPLoopTrans"

    def __str__(self):
        return "Add an OpenMP DO directive to a GOcean loop"

    def apply(self, node):

        '''Perform GOcean specific loop validity checks then call
            `:py:meth:`OMPLoopTrans.apply`.

        '''
        # check node is a loop. Although this is not GOcean specific
        # it is required for the subsequent checks to function
        # correctly.
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Error in "+self.name+" transformation."
                                      " The node is not a loop.")
        # Check we are either an inner or outer loop
        if node.loop_type not in ["inner", "outer"]:
            raise TransformationError("Error in "+self.name+" transformation."
                                      " The requested loop is not of type "
                                      "inner or outer.")

        return OMPLoopTrans.apply(self, node)

class ColourTrans(Transformation):

    '''Apply a colouring transformation to a loop.

    Transform a loop over cells (columns) into a doubly-nested loop
    where the outer loop is over colours and the inner is over points
    of that colour. This then permits a subsequent OpenMP
    parallelisation of the inner loop. For example:

    >>> invoke = ...
    >>> schedule = invoke.schedule
    >>>
    >>> ctrans = ColourTrans()
    >>>
    >>> # Colour all of the loops
    >>> for child in schedule.children:
    >>>     cschedule, _ = ctrans.apply(child)
    >>>
    >>> csched.view()

    '''

    def __str__(self):
        return "Split a loop into colours"

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "LoopColourTrans"

    def apply(self, node):
        '''Converts the Loop represented by :py:obj:`node` into a
        nested loop where the outer loop is over colours and the inner
        loop is over points of that colour.
        '''
        schedule = node.root

        # create a memento of the schedule and the proposed transformation
        from undoredo import Memento
        keep = Memento(schedule, self, [node])

        node_parent = node.parent
        node_position = node.position

        # create a colours loop. This loops over colours and must be run
        # sequentially
        colours_loop = node.__class__(parent=node_parent, loop_type="colours")
        colours_loop.field_space = node.field_space
        colours_loop.iteration_space = node.iteration_space
        # Add this loop as a child of the original node's parent
        node_parent.addchild(colours_loop, index=node_position)

        # create a colour loop. This loops over a particular colour and
        # can be run in parallel
        colour_loop = node.__class__(parent=colours_loop, loop_type="colour")
        colour_loop.field_space = node.field_space
        colour_loop.iteration_space = node.iteration_space
        # Add this loop as a child of our loop over colours
        colours_loop.addchild(colour_loop)

        # add contents of node to colour loop
        colour_loop.children.extend(node.children)

        # change the parent of the node's contents to the colour loop
        for child in node.children:
            child.parent = colour_loop

        # remove original loop
        node_parent.children.remove(node)

        return schedule, keep


class Dynamo0p1ColourTrans(Transformation):

    ''' Apply a colouring transformation to a loop (in order to permit a
        subsequent OpenMP parallelisation over colours).
    '''

    def __str__(self):
        return "Split a Dynamo 0.1 loop into colours"

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "Dynamo0p1LoopColourTrans"

    def apply(self, node):
        '''Performs Dynamo0.1-specific error checking and then uses the parent
        class to convert the Loop represented by :py:obj:`node` into a
        nested loop where the outer loop is over colours and the inner
        loop is over points of that colour.

        '''

        # check node is a loop
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise Exception("Error in "+self.name+" transformation. The "
                            "node is not a loop")
        # Check iteration space is supported - only cells at the moment
        if not node.iteration_space == "cells":
            raise Exception("Error in "+self.name+" transformation. The "
                            "iteration space is not 'cells'.")
        # Check we need colouring
        if node.field_space == "w3":
            raise Exception("Error in "+self.name+" transformation. The "
                            "field space written to by the kernel is 'w3'. "
                            "Colouring is not required.")
        # Check this is a kernel loop
        if node.loop_type not in [None, ""]:
            raise Exception("Error in {0} transformation. The "
                            "loop is not the correct type for colouring."
                            " Expecting 'None' but found '{1}'".
                            format(self.name, node.loop_type))

        schedule, keep = ColourTrans.apply(self, node)

        return schedule, keep


class Dynamo0p3ColourTrans(ColourTrans):

    ''' Split a Dynamo 0.3 loop into colours so that it can be
    parallelised. For example:

    >>> from parse import parse
    >>> from psyGen import PSyFactory
    >>> import transformations
    >>> import os
    >>> import pytest
    >>>
    >>> TEST_API = "dynamo0.3"
    >>> _,info=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),
    >>>              "tests", "test_files", "dynamo0p3",
    >>>              "4.6_multikernel_invokes.f90"),
    >>>              api=TEST_API)
    >>> psy = PSyFactory(TEST_API).create(info)
    >>> invoke = psy.invokes.get('invoke_0')
    >>> schedule = invoke.schedule
    >>>
    >>> ctrans = Dynamo0p3ColourTrans()
    >>> otrans = DynamoOMPParallelLoopTrans()
    >>>
    >>> # Colour all of the loops
    >>> for child in schedule.children:
    >>>     cschedule, _ = ctrans.apply(child)
    >>>
    >>> # Then apply OpenMP to each of the colour loops
    >>> schedule = cschedule
    >>> for child in schedule.children:
    >>>     newsched, _ = otrans.apply(child.children[0])
    >>>
    >>> newsched.view()

    Colouring in the Dynamo 0.3 API is subject to the following rules:

    * Any kernel which has a field with 'INC' access must be coloured UNLESS
      that field is on w3
    * A kernel may have at most one field with 'INC' access
    * Attempting to colour a kernel that updates a field on w3 (with INC
      access) should result in PSyclone issuing an error since colouring is
      not required (and is not supported by the Dynamo infrastructure).
    * Attempting to colour any kernel that doesn't have a field with INC
      access should also result in PSyclone issuing a warning.
    * A separate colour map will be required for each field that is coloured
      (if an invoke contains >1 kernel call)

    '''

    def __str__(self):
        return "Split a Dynamo 0.3 loop into colours"

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "Dynamo0p3LoopColourTrans"

    def apply(self, node):
        '''Performs Dynamo0.3-specific error checking and then uses the parent
        class to convert the Loop represented by :py:obj:`node` into a
        nested loop where the outer loop is over colours and the inner
        loop is over points of that colour.

        '''
        # check node is a loop
        from psyGen import Loop
        if not isinstance(node, Loop):
            raise TransformationError("Error in Dynamo0p3ColourTrans. "
                                      "The supplied node is not a loop")
        # Check we need colouring
        if node.field_space == "w3":
            raise TransformationError(
                "Colouring a loop on W3 is unecessary and is not supported.")

        # Check whether we have a field that has INC access
        if not node.has_inc_arg():
            #TODO generate a warning here as we don't need to colour
            # a loop that does not update a field with INC access
            pass

        # Check that we're not attempting to colour a loop that is
        # already within an OpenMP region (because the loop over
        # colours *must* be sequential)
        from psyGen import OMPDirective
        if node.ancestor(OMPDirective):
            raise TransformationError("Cannot have a loop over colours "
                                      "within an OpenMP parallel region.")

        schedule, keep = ColourTrans.apply(self, node)

        return schedule, keep


class OMPParallelTrans(Transformation):

    ''' Create an OpenMP PARALLEL region by inserting directives. For
    example:

    >>> from parse import parse, ParseError
    >>> from psyGen import PSyFactory, GenerationError
    >>> api="gocean1.0"
    >>> filename="nemolite2d_alg.f90"
    >>> ast,invokeInfo=parse(filename,api=api,invoke_name="invoke")
    >>> psy=PSyFactory(api).create(invokeInfo)
    >>>
    >>> from psyGen import TransInfo
    >>> t=TransInfo()
    >>> ltrans = t.get_trans_name('GOceanOMPLoopTrans')
    >>> rtrans = t.get_trans_name('OMPParallelTrans')
    >>>
    >>> schedule=psy.invokes.get('invoke_0').schedule
    >>> schedule.view()
    >>> new_schedule=schedule
    >>>
    >>> # Apply the OpenMP Loop transformation to *every* loop
    >>> # in the schedule
    >>> for child in schedule.children:
    >>>     newschedule,memento=ltrans.apply(child)
    >>>     schedule = newschedule
    >>>
    >>> # Enclose all of these loops within a single OpenMP
    >>> # PARALLEL region
    >>> newschedule, _ = rtrans.apply(schedule.children)
    >>> newschedule.view()

    '''

    def __str__(self):
        return "Insert an OpenMP Parallel region"

    @property
    def name(self):
        ''' Returns the name of this transformation as a string '''
        return "OMPParallelTrans"

    def apply(self, nodes):
        '''Apply this transformation to a subset of the nodes within a
            schedule - i.e. enclose the specified Loops in the
            schedule within a single OpenMP region. :py:obj:`nodes`
            can be a single Node or a list of Nodes.

        '''
        from psyGen import OMPDirective, OMPParallelDirective

        # Check whether we've been passed a list of nodes or just a
        # single node. If the latter then we create ourselves a
        # list containing just that node.
        from psyGen import Node
        if isinstance(nodes, list) and isinstance(nodes[0], Node):
            node_list = nodes
        elif isinstance(nodes, Node):
            node_list = [nodes]
        else:
            arg_type = str(type(nodes))
            raise TransformationError("Error in OMPParallel transformation. "
                                      "Argument must be a single Node in a "
                                      "schedule or a list of Nodes in a "
                                      "schedule but have been passed an "
                                      "object of type: {0}".
                                      format(arg_type))

        # Keep a reference to the parent of the nodes that are to be
        # enclosed within a parallel region. Also keep the index of
        # the first child to be enclosed as that will become the
        # position of the new !$omp parallel directive.
        node_parent = node_list[0].parent
        node_position = node_list[0].position

        if node_list[0].ancestor(OMPDirective):
            raise TransformationError("Error in OMPParallel transformation:"+\
                                      " cannot create an OpenMP PARALLEL "+\
                                      "region within another OpenMP region.")
        for child in node_list:
            if child.parent is not node_parent:
                raise TransformationError(
                    "Error in OMPParallel transformation: supplied nodes "
                    "are not children of the same Schedule/parent.")

        # create a memento of the schedule and the proposed
        # transformation
        schedule = node_list[0].root

        from undoredo import Memento
        keep = Memento(schedule, self)

        # Create the OpenMP parallel directive as a child of the
        # parent of the nodes being enclosed and with those nodes
        # as its children.
        # We slice the nodes list in order to get a new list object
        # (although the actual items in the list are still those in the
        # original). If we don't do this then we get an infinite
        # recursion in the new schedule.
        directive = OMPParallelDirective(parent=node_parent,
                                         children=node_list[:])

        # Change all of the affected children so that they have
        # the OpenMP directive as their parent. Use a slice
        # of the list of nodes so that we're looping over a local
        # copy of the list. Otherwise things get confused when
        # we remove children from the list.
        for child in node_list[:]:
            # Remove child from the parent's list of children
            node_parent.children.remove(child)
            child.parent = directive

        # Add the OpenMP region directive as a child of the parent
        # of the nodes being enclosed and at the original location
        # of the first of these nodes
        node_parent.addchild(directive,
                             index=node_position)

        return schedule, keep
