Getting Going
=============

Download
--------

PSyclone is available for download from the GungHo repository.

``svn co https://puma.nerc.ac.uk/svn/GungHo_svn/PSyclone/trunk PSyclone``

Hereon the location where you download PSyclone (including the
PSyclone directory itself) will be refered to as <PSYCLONEHOME>

Dependencies
------------

PSyclone is written in python so needs python to be installed on the
target machine. PSyclone has been tested under python 2.6.5 and 2.7.3.

PSyclone immediately relies on two external libraries, f2py and
pyparsing. To run the test suite you will require py.test.

f2py quick setup
^^^^^^^^^^^^^^^^

The source code of f2py (revision 88) is provided with PSyclone in the
sub-directory ``f2py_88``.

To use f2py provided with PSyclone you can simply set up your
PYTHONPATH variable to include this directory.
::
    > export PYTHONPATH=<PSYCLONEHOME>/f2py_88:${PYTHONPATH}

If for some reason you need to install f2py yourself then 
see :ref:`sec_f2py_install`.

pyparsing
^^^^^^^^^

PSyclone requires pyparsing, a library designed to allow parsers to be be
built in Python. PSyclone uses pyparsing to parse fortran regular
expressions as f2py does not fully parse these, (see
http://pyparsing.wikispaces.com for more information).

PSyclone has been tested with pyparsing version 1.5.2 which is a relatively
old version but is currently the version available in the Ubuntu
software center.

You can test if pyparsing is already installed on your machine by
typing ``import pyparsing`` from the python command line. If pyparsing
is installed, this command will complete succesfully. If pyparsing is
installed you can check its version by typing
``pyparsing.__version__`` after succesfully importing it. Versions
higher than 1.5.2 should work but have not been tested.

If pyparsing is not installed on your system you can install it from
within Ubuntu using the software center (search for the
"python-pyparsing" module in the software center and install). If you
do not run Ubuntu you could follow the instructions here
http://pyparsing.wikispaces.com/Download+and+Installation.

py.test
^^^^^^^

The PSyclone test suite uses py.test. You can test whether it is already
installed by simply typing ``py.test`` at a shell prompt. If it is 
present you will get output that begins with
::

======================== test session starts ==================

If you do not have it then py.test can be installed from here
http://pytest.org/latest/ (or specifically here
http://pytest.org/latest/getting-started.html).

Test
----

Once you have the necessary dependencies installed, you can test that
things are working by using the PSyclone test suite:
::
    > cd <PSYCLONEHOME>/src/tests
    > py.test

If everything is working as expected then you should see output similar to:
::

    ============================= test session starts =========================
    platform linux2 -- Python 2.7.5 -- py-1.4.26 -- pytest-2.6.4
    collected 35 items 

    alggen_test.py xxxxx.x.x
    f2pygen_test.py .x....
    generator_test.py ..
    parser_test.py .
    psyGen_test.py .............
    transformations_test.py xx.x

    ================== 24 passed, 11 xfailed in 1.21 seconds ==================

Run
---

Having checked things with the test suite you are ready to try running
PSyclone on the examples. The generator.py script can be used to
generate the required PSy code as well as the modified algorithm code.
::
    > cd <PSYCLONEHOME>/src
    > python ./generator.py 
    usage: generator.py [-h] [-oalg OALG] [-opsy OPSY]  [-api API] filename
    generator.py: error: too few arguments

Examples are provided in the examples directory. There are 3
subdirectories (dynamo, gocean and gunghoproto) corresponding to different
API's that are supported by PSyclone. In this case we are going to use
one of the dynamo examples
::
    > cd <PSYCLONEHOME>/examples/dynamo/eg1
    > python ../../../src/generator.py -oalg dynamo_alg.f90 -opsy dynamo_psy.f90 dynamo.F90

You should see two new files created called dynamo_alg.f90 (containing
the re-written algorithm layer) and dynamo_psy.f90 (containing the
generated PSy layer).

You can also run the runme.py example to see the interactive
API in action
::
    > cd <PSYCLONEHOME>/example/dynamo/eg1
    > python runme.py
