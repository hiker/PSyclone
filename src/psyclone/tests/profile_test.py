# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2018, Science and Technology Facilities Council
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# -----------------------------------------------------------------------------
# Author J. Henrichs, Bureau of Meteorology

''' Module containing tests for generating monitoring hooks'''

from __future__ import absolute_import

import os
import re
import pytest

from psyclone.generator import GenerationError
from psyclone.gocean1p0 import GOKern, GOSchedule
from psyclone.parse import parse
from psyclone.profiler import Profiler, ProfileNode
from psyclone.psyGen import Loop, PSyFactory
from psyclone.transformations import ProfileRegionTrans, TransformationError


# TODO: Once #170 is merged, use the new tests/utils.py module
def get_invoke(api, algfile, key):
    ''' Utility method to get the idx'th invoke from the algorithm
    specified in file '''

    if api == "gocean1.0":
        dir_name = "gocean1p0"
    elif api == "dynamo0.3":
        dir_name = "dynamo0p3"
    else:
        assert False
    _, info = parse(os.path.
                    join(os.path.dirname(os.path.abspath(__file__)),
                         "test_files", dir_name, algfile),
                    api=api)
    psy = PSyFactory(api).create(info)
    invokes = psy.invokes
    if isinstance(key, str):
        invoke = invokes.get(key)
    else:
        # invokes does not have a method by which to request the i'th
        # in the list so we do this rather clumsy lookup of the name
        # of the invoke that we want
        invoke = invokes.get(invokes.names[key])
    return psy, invoke


# -----------------------------------------------------------------------------
def test_profile_basic(capsys):
    '''Check basic functionality: node names, schedule view.
    '''
    Profiler.set_options([Profiler.INVOKES])
    _, invoke = get_invoke("gocean1.0", "test11_different_iterates_over_"
                           "one_invoke.f90", 0)

    assert str(invoke.schedule.children[0]) == "Profile"

    invoke.schedule.view()
    out, _ = capsys.readouterr()

    coloured_schedule = GOSchedule([]).coloured_text
    coloured_loop = Loop().coloured_text
    coloured_kern = GOKern().coloured_text
    coloured_profile = ProfileNode().coloured_text
    correct = (
        '''{0}[invoke='invoke_0',Constant loop bounds=True]
    {3}
        {1}[type='outer',field_space='cv',it_space='internal_pts']
            {1}[type='inner',field_space='cv',it_space='internal_pts']
                {2} compute_cv_code(cv_fld,p_fld,v_fld) '''
        '''[module_inline=False]
        {1}[type='outer',field_space='ct',it_space='all_pts']
            {1}[type='inner',field_space='ct',it_space='all_pts']
                {2} bc_ssh_code(ncycle,p_fld,tmask) '''
        '''[module_inline=False]'''.format(coloured_schedule, coloured_loop,
                                           coloured_kern, coloured_profile)
    )

    assert correct in out

    prt = ProfileRegionTrans()

    # Insert a profile call between outer and inner loop.
    # This forces the profile node to loop up in the tree
    # to find the subroutine node (i.e. we are testing
    # the while loop in the ProfileNode).
    new_sched, _ = prt.apply(invoke.schedule.children[0]
                             .children[0].children[0])

    new_sched.view()
    out, _ = capsys.readouterr()

    # Make sure to support colour codes
    correct = (
        '''{0}[invoke='invoke_0',Constant loop bounds=True]
    {3}
        {1}[type='outer',field_space='cv',it_space='internal_pts']
            {3}
                {1}[type='inner',field_space='cv',it_space='internal_pts']
                    {2} compute_cv_code(cv_fld,p_fld,v_fld) '''
        '''[module_inline=False]
        {1}[type='outer',field_space='ct',it_space='all_pts']
            {1}[type='inner',field_space='ct',it_space='all_pts']
                {2} bc_ssh_code(ncycle,p_fld,tmask) '''
        '''[module_inline=False]'''
    ).format(coloured_schedule, coloured_loop, coloured_kern, coloured_profile)
    assert correct in out

    Profiler.set_options(None)


# -----------------------------------------------------------------------------
def test_profile_errors2():
    '''Test various error handling.'''

    with pytest.raises(GenerationError) as gen_error:
        Profiler.set_options(["invalid"])
    assert "Invalid option" in str(gen_error)


# -----------------------------------------------------------------------------
def test_profile_invokes_gocean1p0():
    '''Check that an invoke is instrumented correctly
    '''
    Profiler.set_options([Profiler.INVOKES])
    _, invoke = get_invoke("gocean1.0", "test11_different_iterates_over_"
                           "one_invoke.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    # First a simple test to that the nesting is correct - the
    # profile regions include both loops
    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  "call ProfileStart.*"
                  "do j.*"
                  "do i.*"
                  "call.*"
                  "end.*"
                  "end.*"
                  "call ProfileEnd")
    assert re.search(correct_re, code, re.I) is not None

    _, invoke = get_invoke("gocean1.0", "single_invoke_"
                           "two_kernels.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  "call ProfileStart.*"
                  "do j.*"
                  "do i.*"
                  "call.*"
                  "end.*"
                  "end.*"
                  "do j.*"
                  "do i.*"
                  "call.*"
                  "end.*"
                  "end.*"
                  "call ProfileEnd")
    assert re.search(correct_re, code, re.I) is not None
    Profiler.set_options(None)


# -----------------------------------------------------------------------------
def test_unique_region_names():
    '''Test that unique region names are created even when the kernel
    names are identical.'''

    Profiler.set_options([Profiler.KERNELS])
    _, invoke = get_invoke("gocean1.0",
                           "single_invoke_two_identical_kernels.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier

    code = str(invoke.gen()).replace("\n", "")

    # This regular expression puts the region names into groups.
    # Make sure even though the kernels have the same name, that
    # the created regions have different names. In order to be
    # flexible for future changes, we get the region names from
    # the ProfileStart calls using a regular expressions (\w*
    # being the group name enclosed in "") group. Python will store
    # those two groups and they can be accessed using the resulting
    # re object.group(n).
    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  r"call ProfileStart\(.*, \"(\w*)\",.*\).*"
                  "do j.*"
                  "do i.*"
                  "call compute_cu_code.*"
                  "end.*"
                  "end.*"
                  "call ProfileEnd.*"
                  r"call ProfileStart\(.*, \"(\w*)\",.*\).*"
                  "do j.*"
                  "do i.*"
                  "call compute_cu_code.*"
                  "end.*"
                  "end.*"
                  "call ProfileEnd")

    groups = re.search(correct_re, code, re.I)
    assert groups is not None

    # Check that the region names are indeed different: group(1)
    # is the first kernel region name crated by PSyclone, and
    # group(2) the name used in the second ProfileStart.
    # Those names must be different (otherwise the profiling tool
    # would likely combine the two different regions into one).
    assert groups.group(1) != groups.group(2)


# -----------------------------------------------------------------------------
def test_profile_kernels_gocean1p0():
    '''Check that all kernels are instrumented correctly
    '''
    Profiler.set_options([Profiler.KERNELS])
    _, invoke = get_invoke("gocean1.0", "single_invoke_"
                           "two_kernels.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    # Test that kernel profiling works in case of two kernel calls
    # in a single invoke subroutine - i.e. we need to have one profile
    # start call before two nested loops, and one profile end call
    # after that:
    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  r"call ProfileStart\(.*, (?P<profile1>\w*)\).*"
                  "do j.*"
                  "do i.*"
                  "call.*"
                  "end.*"
                  "end.*"
                  r"call ProfileEnd\((?P=profile1)\).*"
                  r"call ProfileStart\(.*, (?P<profile2>\w*)\).*"
                  "do j.*"
                  "do i.*"
                  "call.*"
                  "end.*"
                  "end.*"
                  r"call ProfileEnd\((?P=profile2)\)")
    groups = re.search(correct_re, code, re.I)
    assert groups is not None
    # Check that the variables are different
    assert groups.group(1) != groups.group(2)

    Profiler.set_options(None)


# -----------------------------------------------------------------------------
def test_profile_invokes_dynamo0p3():
    '''Check that a Dynamo 0.3 invoke is instrumented correctly
    '''
    Profiler.set_options([Profiler.INVOKES])

    # First test for a single invoke with a single kernel work as expected:
    _, invoke = get_invoke("dynamo0.3", "1_single_invoke.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  "call ProfileStart.*"
                  "do cell.*"
                  "call.*"
                  "end.*"
                  "call ProfileEnd")
    assert re.search(correct_re, code, re.I) is not None

    # Next test two kernels in one invoke:
    _, invoke = get_invoke("dynamo0.3", "1.2_multi_invoke.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  "call ProfileStart.*"
                  "do cell.*"
                  "call.*"
                  "end.*"
                  "do cell.*"
                  "call.*"
                  "end.*"
                  "call ProfileEnd")
    assert re.search(correct_re, code, re.I) is not None
    Profiler.set_options(None)


# -----------------------------------------------------------------------------
def test_profile_kernels_dynamo0p3():
    '''Check that all kernels are instrumented correctly in a
    Dynamo 0.3 invoke.
    '''
    Profiler.set_options([Profiler.KERNELS])
    _, invoke = get_invoke("dynamo0.3", "1_single_invoke.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  "call ProfileStart.*"
                  "do cell.*"
                  "call.*"
                  "end.*"
                  "call ProfileEnd")
    assert re.search(correct_re, code, re.I) is not None

    _, invoke = get_invoke("dynamo0.3", "1.2_multi_invoke.f90", 0)

    # Convert the invoke to code, and remove all new lines, to make
    # regex matching easier
    code = str(invoke.gen()).replace("\n", "")

    correct_re = ("subroutine invoke.*"
                  "use profile_mod, only: ProfileData.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  r"TYPE\(ProfileData\), save :: profile.*"
                  r"call ProfileStart\(.*, (?P<profile1>\w*)\).*"
                  "do cell.*"
                  "call.*"
                  "end.*"
                  r"call ProfileEnd\((?P=profile1)\).*"
                  r"call ProfileStart\(.*, (?P<profile2>\w*)\).*"
                  "do cell.*"
                  "call.*"
                  "end.*"
                  r"call ProfileEnd\((?P=profile2)\).*")
    groups = re.search(correct_re, code, re.I)
    assert groups is not None
    # Check that the variables are different
    assert groups.group(1) != groups.group(2)
    Profiler.set_options(None)


# -----------------------------------------------------------------------------
def test_transform(capsys):
    '''Tests normal behaviour of profile region transformation.'''

    _, invoke = get_invoke("gocean1.0", "test27_loop_swap.f90", "invoke_loop1")
    schedule = invoke.schedule

    prt = ProfileRegionTrans()
    assert str(prt) == "Insert a profile start and end call."
    assert prt.name == "ProfileRegionTrans"

    # Try applying it to a list
    sched1, _ = prt.apply(schedule.children)
    sched1.view()
    out, _ = capsys.readouterr()
    # out is unicode, and has no replace function, so convert to string first
    out = str(out).replace("\n", "")

    # The .* before and after a keyword are necessary to escape colouring
    # codes that might be used!
    correct_re = (".*GOSchedule.*"
                  r"    .*Profile.*"
                  r"        .*Loop.*\[type='outer'.*"
                  r"        .*Loop.*\[type='outer'.*"
                  r"        .*Loop.*\[type='outer'.*")
    assert re.search(correct_re, out)

    # Now only wrap a single node - the middle loop:
    sched2, _ = prt.apply(schedule.children[0].children[1])
    sched2.view()
    out, _ = capsys.readouterr()  # .replace("\n", "")
    # out is unicode, and has no replace function, so convert to string first
    out = str(out).replace("\n", "")
    correct_re = (".*GOSchedule.*"
                  r"    .*Profile.*"
                  r"        .*Loop.*\[type='outer'.*"
                  r"        .*Profile.*"
                  r"            .*Loop.*\[type='outer'.*"
                  r"        .*Loop.*\[type='outer'.*")
    assert re.search(correct_re, out)

    # Check that an sublist created from individual elements
    # can be wrapped
    sched3, _ = prt.apply([sched2.children[0].children[0],
                           sched2.children[0].children[1]])
    sched3.view()
    out, _ = capsys.readouterr()  # .replace("\n", "")
    # out is unicode, and has no replace function, so convert to string first
    out = str(out).replace("\n", "")
    correct_re = (".*GOSchedule.*"
                  r"    .*Profile.*"
                  r"        .*Profile.*"
                  r"            .*Loop.*\[type='outer'.*"
                  r"            .*Profile.*"
                  r"                .*Loop.*\[type='outer'.*"
                  r"        .*Loop.*\[type='outer'.*")
    assert re.search(correct_re, out)


# -----------------------------------------------------------------------------
def test_transform_errors(capsys):
    '''Tests error handling of the profile region transformation.'''

    # This has been imported and tested before, so we can assume
    # here that this all works as expected/
    _, invoke = get_invoke("gocean1.0", "test27_loop_swap.f90", "invoke_loop1")

    schedule = invoke.schedule
    prt = ProfileRegionTrans()

    with pytest.raises(TransformationError) as excinfo:
        prt.apply([schedule.children[0].children[0], schedule.children[1]])
    assert "supplied nodes are not children of the same Schedule/parent." \
           in str(excinfo)

    # Supply not a node object:
    with pytest.raises(TransformationError) as excinfo:
        prt.apply(5)
    assert "Argument must be a single Node in a schedule or a list of Nodes " \
           "in a schedule but have been passed an object of type: " \
           "<type 'int'>" in str(excinfo)

    # Test that it will only allow correctly ordered nodes:
    with pytest.raises(TransformationError) as excinfo:
        sched1, _ = prt.apply([schedule.children[1], schedule.children[0]])
    assert "Children are not consecutive children of one parent:" \
           in str(excinfo)

    with pytest.raises(TransformationError) as excinfo:
        sched1, _ = prt.apply([schedule.children[0], schedule.children[2]])
    assert "Children are not consecutive children of one parent:" \
           in str(excinfo)

    # Test 3 element lists: first various incorrect ordering:
    with pytest.raises(TransformationError) as excinfo:
        sched1, _ = prt.apply([schedule.children[0],
                               schedule.children[2],
                               schedule.children[1]])
    assert "Children are not consecutive children of one parent:" \
           in str(excinfo)

    with pytest.raises(TransformationError) as excinfo:
        sched1, _ = prt.apply([schedule.children[1],
                               schedule.children[0],
                               schedule.children[2]])
    assert "Children are not consecutive children of one parent:" \
           in str(excinfo)

    # Just to be sure: also check that the right order does indeed work!
    sched1, _ = prt.apply([schedule.children[0],
                           schedule.children[1],
                           schedule.children[2]])
    sched1.view()
    out, _ = capsys.readouterr()
    # out is unicode, and has no replace function, so convert to string first
    out = str(out).replace("\n", "")

    correct_re = (".*GOSchedule.*"
                  r"    .*Profile.*"
                  r"        .*Loop.*\[type='outer'.*"
                  r"        .*Loop.*\[type='outer'.*"
                  r"        .*Loop.*\[type='outer'.*")
    assert re.search(correct_re, out)
