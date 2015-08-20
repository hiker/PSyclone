Transformations
===============

As discussed in the previous section, transformations can be applied
to a schedule to modify it. Typically transformations will be used to
optimise the PSy layer for a particular architecture, however
transformations could be added for other reasons, such as to aid
debugging or for performance monitoring.

Finding Transformations
-----------------------

Transformations can be imported directly, but the user needs to know
what transformations are available. A helper class **TransInfo** is
provided to show the available transformations

.. autoclass:: psyGen.TransInfo
    :members:

Available Transformations
-------------------------

Most transformations are generic as the schedule structure is
independent of the API, however it often makes sense to specialise
these for a particular API by adding API-specific errors checks. Some
transformations are API-specific (or specific to a set of API's
e.g. dynamo). Currently these different types of transformation are
indicated by their names.

The transformations currently available are given below:

.. automodule:: transformations
    :members:

Applying Transformations
------------------------

Transformations can be applied either interactively or through a
script.


Interactive
+++++++++++

To apply a transformation interactively we first parse and analyse the
code and then extract the particular schedule we are interested
in. For example ...
::

    from parse import parse
    from psyGen import PSyFactory

    # This example uses version 0.1 of the Dynamo API
    api = "dynamo0.1"

    # Parse the file containing the algorithm specification and
    # return the Abstract Syntax Tree and invokeInfo objects
    ast, invokeInfo = parse("dynamo.F90", api=api)

    # Create the PSy-layer object using the invokeInfo
    psy = PSyFactory(api).create(invokeInfo)

    # Optionally generate the vanilla PSy layer fortran
    print psy.gen

    # List the various invokes that the PSy layer contains
    print psy.invokes.names

    # Get the required invoke
    invoke = psy.invokes.get('invoke_0_v3_kernel_type')

    # Get the schedule associated with the required invoke
    schedule = invoke.schedule
    schedule.view()

Now we have the schedule we can create and apply a transformation to
it to create a new schedule and then replace the original schedule
with the new one. For example ...
::

    # Get the list of possible loop transformations
    from psyGen import TransInfo
    t = TransInfo()
    print t.list

    # Create an OpenMPLoop-transformation
    ol = t.get_trans_name('OMPParallelLoopTrans')

    # Apply it to the loop schedule of the selected invoke
    new_schedule,memento = ol.apply(schedule.children[0])
    new_schedule.view()

    # Replace the original loop schedule of the selected invoke
    # with the new, transformed schedule 
    invoke.schedule=new_schedule

    # Generate the Fortran code for the new PSy layer
    print psy.gen

More examples of use of the interactive application of transformations
can be found in the runme*.py files within the examples/dynamo/eg1 and
examples/dynamo/eg2 directories. Some simple examples of the use of
transformations are also given in the previous section.

Script
++++++

The generator.py script has an optional -s option which can specify a script file to apply to the PSy layer code.

