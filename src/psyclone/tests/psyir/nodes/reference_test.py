# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2019-2020, Science and Technology Facilities Council.
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
# Authors R. W. Ford, A. R. Porter and S. Siso, STFC Daresbury Lab
#         I. Kavcic, Met Office
#         J. Henrichs, Bureau of Meteorology
# -----------------------------------------------------------------------------

''' Performs py.test tests on the Reference PSyIR node. '''

from __future__ import absolute_import
import pytest
from psyclone.psyir.nodes import Reference, Array, Assignment, Container, \
    Literal
from psyclone.psyir.symbols import DataSymbol, DataType
from psyclone.psyGen import GenerationError, KernelSchedule, Kern
from psyclone.psyir.backend.fortran import FortranWriter
from psyclone.tests.utilities import get_invoke, check_links


def test_reference_node_str():
    ''' Check the node_str method of the Reference class.'''
    from psyclone.psyir.nodes.node import colored, SCHEDULE_COLOUR_MAP
    kschedule = KernelSchedule("kname")
    kschedule.symbol_table.add(DataSymbol("rname", DataType.INTEGER))
    assignment = Assignment(parent=kschedule)
    ref = Reference("rname", assignment)
    coloredtext = colored("Reference", SCHEDULE_COLOUR_MAP["Reference"])
    assert coloredtext+"[name:'rname']" in ref.node_str()


def test_reference_can_be_printed():
    '''Test that a Reference instance can always be printed (i.e. is
    initialised fully)'''
    kschedule = KernelSchedule("kname")
    kschedule.symbol_table.add(DataSymbol("rname", DataType.INTEGER))
    assignment = Assignment(parent=kschedule)
    ref = Reference("rname", assignment)
    assert "Reference[name:'rname']" in str(ref)


def test_reference_optional_parent():
    '''Test that the parent attribute is None if the optional parent
    argument is not supplied.

    '''
    ref = Reference("rname")
    assert ref.parent is None


def test_reference_symbol(monkeypatch):
    '''Test that the symbol method in a Reference Node instance returns
    the associated symbol if there is one and None if not. Also test
    for an incorrect scope argument.

    '''
    _, invoke = get_invoke("single_invoke_kern_with_global.f90",
                           api="gocean1.0", idx=0)
    sched = invoke.schedule
    kernels = sched.walk(Kern)
    kernel_schedule = kernels[0].get_kernel_schedule()
    references = kernel_schedule.walk(Reference)

    # Symbol in KernelSchedule SymbolTable
    field_old = references[0]
    assert field_old.name == "field_old"
    assert isinstance(field_old.symbol(), DataSymbol)
    assert field_old.symbol().name == field_old.name

    # Symbol in KernelSchedule SymbolTable with KernelSchedule scope
    assert isinstance(field_old.symbol(scope_limit=kernel_schedule),
                      DataSymbol)
    assert field_old.symbol().name == field_old.name

    # Symbol in KernelSchedule SymbolTable with parent scope
    assert field_old.symbol(scope_limit=field_old.parent) is None

    # Symbol in Container SymbolTable
    alpha = references[6]
    assert alpha.name == "alpha"
    assert isinstance(alpha.symbol(), DataSymbol)
    assert alpha.symbol().name == alpha.name

    # Symbol in Container SymbolTable with KernelSchedule scope
    assert alpha.symbol(scope_limit=kernel_schedule) is None

    # Symbol in Container SymbolTable with Container scope
    assert isinstance(kernel_schedule.root, Container)
    assert alpha.symbol(scope_limit=kernel_schedule.root).name == alpha.name

    # Symbol method with invalid scope type
    with pytest.raises(TypeError) as excinfo:
        _ = alpha.symbol(scope_limit="hello")
    assert ("The scope_limit argument 'hello' provided to the symbol method, "
            "is not of type `Node`." in str(excinfo.value))

    # Symbol method with invalid scope location
    with pytest.raises(ValueError) as excinfo:
        _ = alpha.symbol(scope_limit=alpha)
    assert ("The scope_limit node 'Reference[name:'alpha']' provided to the "
            "symbol method, is not an ancestor of this reference node "
            "'Reference[name:'alpha']'." in str(excinfo.value))

    # Symbol not in any container (rename alpha to something that is
    # not defined)
    monkeypatch.setattr(alpha, "_reference", "not_defined")
    assert not alpha.symbol()

# Test Array class


def test_array_node_str():
    ''' Check the node_str method of the Array class.'''
    from psyclone.psyir.nodes.node import colored, SCHEDULE_COLOUR_MAP
    kschedule = KernelSchedule("kname")
    kschedule.symbol_table.add(DataSymbol("aname", DataType.INTEGER,
                                          [DataSymbol.Extent.ATTRIBUTE]))
    assignment = Assignment(parent=kschedule)
    array = Array("aname", parent=assignment)
    coloredtext = colored("ArrayReference", SCHEDULE_COLOUR_MAP["Reference"])
    assert coloredtext+"[name:'aname']" in array.node_str()


def test_array_can_be_printed():
    '''Test that an Array instance can always be printed (i.e. is
    initialised fully)'''
    kschedule = KernelSchedule("kname")
    kschedule.symbol_table.add(DataSymbol("aname", DataType.INTEGER))
    assignment = Assignment(parent=kschedule)
    array = Array("aname", assignment)
    assert "ArrayReference[name:'aname']\n" in str(array)


def test_array_create():
    '''Test that the create method in the Array class correctly
    creates an Array instance.

    '''
    children = [Reference("i"), Reference("j"), Literal("1", DataType.REAL)]
    array = Array.create("temp", children)
    check_links(array, children)
    result = FortranWriter().array_node(array)
    assert result == "temp(i,j,1)"


def test_array_create_invalid():
    '''Test that the create method in an Array class raises the expected
    exception if the provided input is invalid.

    '''
    # name is not a string
    with pytest.raises(GenerationError) as excinfo:
        _ = Array.create([], [])
    assert ("name argument in create method of Array class should "
            "be a string but found 'list'."
            in str(excinfo.value))

    # name is an empty string
    with pytest.raises(GenerationError) as excinfo:
        _ = Array.create("", [])
    assert ("name argument in create method of Array class can't "
            "be an empty string.")

    # children not a list
    with pytest.raises(GenerationError) as excinfo:
        _ = Array.create("temp", "invalid")
    assert ("children argument in create method of Array class should "
            "be a list but found 'str'." in str(excinfo.value))

    # contents of children list are not Node
    with pytest.raises(GenerationError) as excinfo:
        _ = Array.create("temp",
                         [Reference("i"), "invalid"])
    assert (
        "child of children argument in create method of Array class "
        "should be a PSyIR Node but found 'str'." in str(excinfo.value))
