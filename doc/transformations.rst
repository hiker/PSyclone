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

Applying Transformations
------------------------

Optimisations can be applied either interactively or through a script.

Interactive
+++++++++++

Script
++++++

The generator.py script has an optional -s option which can specify a script file to apply to the PSy layer code.

Available Transformations
-------------------------
