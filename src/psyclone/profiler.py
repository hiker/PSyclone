# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2018-2019, Science and Technology Facilities Council.
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
# Modified by A. R. Porter, STFC Daresbury Lab
# Modified by R. W. Ford, STFC Daresbury Lab
# -----------------------------------------------------------------------------

''' This module provides support for adding profiling to code
    generated by PSyclone. '''

from __future__ import absolute_import, print_function
from psyclone.f2pygen import CallGen, TypeDeclGen, UseGen
from psyclone.psyGen import GenerationError, Kern, NameSpace, \
     NameSpaceFactory, Node, InternalError


class Profiler(object):
    ''' This class wraps all profiling related settings.'''

    # Command line option to use for the various profiling options
    # INVOKES: Automatically add a region for each invoke. i.e. at
    #          the start and end of each PSyclone created subroutine.
    # KERNELS: Automatically add a profile region around every
    #          kernel call including the loop structure created.
    INVOKES = "invokes"
    KERNELS = "kernels"
    SUPPORTED_OPTIONS = [INVOKES, KERNELS]
    _options = []
    # A namespace manager to make sure we get unique region names
    _namespace = NameSpace()

    # -------------------------------------------------------------------------
    @staticmethod
    def set_options(options):
        '''Sets the option the user required.
        :param options: List of options selected by the user, or None to
                        disable all automatic profiling.
        :type options: List of strings.
        :raises GenerationError: If any option is not KERNELS or INVOKES.
        '''
        # Test that all options are valid
        if options is None:
            options = []   # Makes it easier to test
        for index, option in enumerate(options):
            if option not in [Profiler.INVOKES, Profiler.KERNELS]:
                # Create a 'nice' representation of the allowed options.
                # [1:-1] cuts out the '[' and ']' that surrounding the
                # string of the list.
                allowed_options = str(Profiler.SUPPORTED_OPTIONS)[1:-1]
                raise GenerationError("Error in Profiler.setOptions: options "
                                      "must be one of {0} but found '{1}' "
                                      "at {2}"
                                      .format(allowed_options,
                                              str(option), index))

        # Store options so they can be queried later
        Profiler._options = options

    # -------------------------------------------------------------------------
    @staticmethod
    def profile_kernels():
        '''Returns true if kernel profiling is enabled.
        :return: True if kernels should be profiled.
        :rtype: bool'''
        return Profiler.KERNELS in Profiler._options

    # -------------------------------------------------------------------------
    @staticmethod
    def profile_invokes():
        '''Returns true if invoke profiling is enabled.
        :return: True if invokes should be profiled.
        :rtype: bool'''
        return Profiler.INVOKES in Profiler._options

    # -------------------------------------------------------------------------
    @staticmethod
    def add_profile_nodes(schedule, loop_class):
        '''This function inserts all required Profiling Nodes (for invokes
        and kernels, as specified on the command line) into a schedule.
        :param schedule: The schedule to instrument.
        :type schedule: :py::class::`psyclone.psyGen.InvokeSchedule` or \
                        derived class
        :param loop_class: The loop class (e.g. GOLoop, DynLoop) to instrument.
        :type loop_class: :py::class::`psyclone.psyGen.Loop` or derived class.
        '''

        from psyclone.psyir.transformations import ProfileTrans
        profile_trans = ProfileTrans()
        if Profiler.profile_kernels():
            for i in schedule.children:
                if isinstance(i, loop_class):
                    profile_trans.apply(i)
        if Profiler.profile_invokes():
            profile_trans.apply(schedule.children)

    # -------------------------------------------------------------------------
    @staticmethod
    def create_unique_region(name):
        '''This function makes sure that region names are unique even if
        the same kernel is called.
        :param str name: The name of a region (usually kernel name).
        :return str: A unique name based on the parameter name.
        '''
        return Profiler._namespace.create_name(name)


# =============================================================================
class ProfileNode(Node):
    '''This class can be inserted into a schedule to create profiling code.

    :param children: a list of child nodes for this node. These will be made \
        children of the child Schedule of this Profile Node.
    :type children: list of :py::class::`psyclone.psyGen.Node` \
        or derived classes
    :param parent: the parent of this node in the PSyIR.
    :type parent: :py::class::`psyclone.psyGen.Node`
    :param str region_name: the name to call this profile region. This \
        name should be unique within this invoke unless aggregate \
        information is required.
    :param str location_name: a name describing the location of the \
        invoke. This name should be unique for each invoke in this \
        code unless aggregate information is required.

    '''
    # Profiling interface Fortran module
    fortran_module = "profile_mod"
    # The symbols we import from the profiling Fortran module
    profiling_symbols = ["ProfileData", "ProfileStart", "ProfileEnd"]
    # The use statement that we will insert. Any use of a module of the
    # same name that doesn't match this will result in a NotImplementedError
    # at code-generation time.
    use_stmt = "use profile_mod, only: " + ", ".join(profiling_symbols)
    # Root of the name to use for variables associated with profiling regions
    profiling_var = "psy_profile"

    def __init__(self, children=None, parent=None, name=None):
        # A ProfileNode always contains a Schedule
        sched = self._insert_schedule(children)
        Node.__init__(self, children=[sched], parent=parent)

        # Store the name of the profile variable that is used for this
        # profile name. This allows to show the variable name in __str__
        # (and also if we would call create_name in gen(), the name would
        # change every time gen() is called).
        self._var_name = NameSpaceFactory().create().create_name("profile")

        # Name of the region. In general at constructor time we might
        # not have a parent subroutine or a child for the kernel, so
        # the name is left empty, unless explicitly provided by the
        # user. If names are not provided here then the region and
        # module names are set the first time gen() is called (and
        # then remain unchanged).
        self._module_name = None
        self._region_name = None
        if name:
            # pylint: disable=too-many-boolean-expressions
            if not isinstance(name, tuple) or not len(name) == 2 or \
               not name[0] or not isinstance(name[0], str) or \
               not name[1] or not isinstance(name[1], str):
                raise InternalError(
                    "Error in ProfileNode. Profile name must be a "
                    "tuple containing two non-empty strings.")
            # pylint: enable=too-many-boolean-expressions
            # Valid profile names have been provided by the user.
            self._module_name = name[0]
            self._region_name = name[1]

        # Name and colour to use for this node
        self._text_name = "Profile"
        self._colour_key = "Profile"

    # -------------------------------------------------------------------------
    def __str__(self):
        ''' Returns a string representation of the subtree starting at
        this node. '''
        result = "ProfileStart[var={0}]\n".format(self._var_name)
        for child in self.profile_body.children:
            result += str(child)+"\n"
        return result+"ProfileEnd"

    @property
    def profile_body(self):
        '''
        :returns: the Schedule associated with this Profiling region.
        :rtype: :py:class:`psyclone.psyGen.Schedule`

        :raises InternalError: if this Profile node does not have a Schedule \
                               as its one and only child.
        '''
        from psyclone.psyGen import Schedule
        if len(self.children) != 1 or not \
           isinstance(self.children[0], Schedule):
            raise InternalError(
                "ProfileNode malformed or incomplete. It should have a single "
                "Schedule as a child but found: {0}".format(
                    [type(child).__name__ for child in self.children]))
        return self.children[0]

    def gen_code(self, parent):
        # pylint: disable=arguments-differ
        '''Creates the profile start and end calls, surrounding the children
        of this node.

        :param parent: the parent of this node.
        :type parent: :py:class:`psyclone.psyGen.Node`

        '''
        module_name = self._module_name
        if module_name is None:
            # The user has not supplied a module (location) name so
            # return the psy-layer module name as this will be unique
            # for each PSyclone algorithm file.
            module_name = self.root.invoke.invokes.psy.name

        region_name = self._region_name
        if region_name is None:
            # The user has not supplied a region name (to identify
            # this particular invoke region). Use the invoke name as a
            # starting point.
            region_name = self.root.invoke.name
            if len(self.walk(Kern)) == 1:
                # This profile only has one kernel within it, so append
                # the kernel name.
                my_kern = self.walk(Kern)[0]
                region_name += ":{0}".format(my_kern.name)
            # Add a region index to ensure uniqueness when there are
            # multiple regions in an invoke.
            profile_nodes = self.root.walk(ProfileNode)
            idx = 0
            for idx, profile_node in enumerate(profile_nodes):
                if profile_node is self:
                    break
            region_name += ":r{0}".format(idx)

        # Note that adding a use statement makes sure it is only
        # added once, so we don't need to test this here!
        use = UseGen(parent, self.fortran_module, only=True,
                     funcnames=["ProfileData, ProfileStart, ProfileEnd"])
        parent.add(use)
        prof_var_decl = TypeDeclGen(parent, datatype="ProfileData",
                                    entity_decls=[self._var_name],
                                    save=True)
        parent.add(prof_var_decl)

        prof_start = CallGen(parent, "ProfileStart",
                             ["\"{0}\"".format(module_name),
                              "\"{0}\"".format(region_name),
                              self._var_name])
        parent.add(prof_start)

        for child in self.profile_body:
            child.gen_code(parent)

        prof_end = CallGen(parent, "ProfileEnd",
                           [self._var_name])
        parent.add(prof_end)

    # -------------------------------------------------------------------------
    def gen_c_code(self, indent=0):
        '''
        Generates a string representation of this Node using C language
        (currently not supported).

        :param int indent: Depth of indent for the output string.
        :raises NotImplementedError: Not yet supported for profiling.
        '''
        raise NotImplementedError("Generation of C code is not supported "
                                  "for profiling")

    def update(self):
        # pylint: disable=too-many-locals, too-many-branches
        # pylint: disable=too-many-statements
        '''
        Update the underlying fparser2 parse tree to implement the profiling
        region represented by this Node. This involves adding the necessary
        module use statement as well as the calls to the profiling API.

        TODO #435 - remove this whole method once the NEMO API uses the
        Fortran backend of the PSyIR.

        :raises NotImplementedError: if the routine which is to have \
                             profiling added to it does not already have a \
                             Specification Part (i.e. some declarations).
        :raises NotImplementedError: if there would be a name clash with \
                             existing variable/module names in the code to \
                             be transformed.
        :raises InternalError: if we fail to find the node in the parse tree \
                             corresponding to the end of the profiling region.

        '''
        from fparser.common.sourceinfo import FortranFormat
        from fparser.common.readfortran import FortranStringReader
        from fparser.two.utils import walk_ast
        from fparser.two import Fortran2003
        from psyclone.psyGen import object_index

        # Ensure child nodes are up-to-date
        super(ProfileNode, self).update()

        # Get the parse tree of the routine containing this region
        # pylint: disable=protected-access
        ptree = self.root.invoke._ast
        # pylint: enable=protected-access
        # Rather than repeatedly walk the tree, we do it once for all of
        # the node types we will be interested in...
        node_list = walk_ast([ptree], [Fortran2003.Main_Program,
                                       Fortran2003.Subroutine_Stmt,
                                       Fortran2003.Function_Stmt,
                                       Fortran2003.Specification_Part,
                                       Fortran2003.Use_Stmt,
                                       Fortran2003.Name])
        if self._module_name:
            routine_name = self._module_name
        else:
            for node in node_list:
                if isinstance(node, (Fortran2003.Main_Program,
                                     Fortran2003.Subroutine_Stmt,
                                     Fortran2003.Function_Stmt)):
                    names = walk_ast([node], [Fortran2003.Name])
                    routine_name = str(names[0]).lower()
                    break

        for node in node_list:
            if isinstance(node, Fortran2003.Specification_Part):
                spec_part = node
                break
        else:
            # This limitation will be removed when we use the Fortran
            # backend of the PSyIR (#435)
            raise NotImplementedError(
                "Addition of profiling regions to routines without any "
                "existing declarations is not supported and '{0}' has no "
                "Specification-Part".format(routine_name))

        # Get the existing use statements
        found = False
        for node in node_list[:]:
            if isinstance(node, Fortran2003.Use_Stmt) and \
               self.fortran_module == str(node.items[2]).lower():
                # Check that the use statement matches the one we would
                # insert (i.e. the code doesn't already contain a module
                # with the same name as that used by the profiling API)
                if str(node).lower() != self.use_stmt.lower():
                    raise NotImplementedError(
                        "Cannot add profiling to '{0}' because it already "
                        "'uses' a module named '{1}'".format(
                            routine_name, self.fortran_module))
                found = True
                # To make our check on name clashes below easier, remove
                # the Name nodes associated with this use from our
                # list of nodes.
                names = walk_ast([node], [Fortran2003.Name])
                for name in names:
                    node_list.remove(name)

        if not found:
            # We don't already have a use for the profiling module so
            # add one.
            reader = FortranStringReader(
                "use profile_mod, only: ProfileData, ProfileStart, ProfileEnd")
            # Tell the reader that the source is free format
            reader.set_format(FortranFormat(True, False))
            use = Fortran2003.Use_Stmt(reader)
            spec_part.content.insert(0, use)

        # Check that we won't have any name-clashes when we insert the
        # symbols required for profiling. This check uses the list of symbols
        # that we created before adding the `use profile_mod...` statement.
        if not self.root.profiling_name_clashes_checked:
            for node in node_list:
                if isinstance(node, Fortran2003.Name):
                    text = str(node).lower()
                    # Check for the symbols we import from the profiling module
                    for symbol in self.profiling_symbols:
                        if text == symbol.lower():
                            raise NotImplementedError(
                                "Cannot add profiling to '{0}' because it "
                                "already contains a symbol that clashes with "
                                "one of those ('{1}') that must be imported "
                                "from the PSyclone profiling module.".
                                format(routine_name, symbol))
                    # Check for the name of the profiling module itself
                    if text == self.fortran_module:
                        raise NotImplementedError(
                            "Cannot add profiling to '{0}' because it already "
                            "contains a symbol that clashes with the name of "
                            "the PSyclone profiling module ('profile_mod')".
                            format(routine_name))
                    # Check for the names of profiling variables
                    if text.startswith(self.profiling_var):
                        raise NotImplementedError(
                            "Cannot add profiling to '{0}' because it already"
                            " contains symbols that potentially clash with "
                            "the variables we will insert for each profiling "
                            "region ('{1}*').".format(routine_name,
                                                      self.profiling_var))
        # Flag that we have now checked for name clashes so that if there's
        # more than one profiling node we don't fall over on the symbols
        # we've previous inserted.
        self.root.profiling_name_clashes_checked = True

        # Create a name for this region by finding where this profiling
        # node is in the list of profiling nodes in this Invoke.
        sched = self.root
        pnodes = sched.walk(ProfileNode)
        region_idx = pnodes.index(self)
        if self._region_name:
            region_name = self._region_name
        else:
            region_name = "r{0}".format(region_idx)
        var_name = "psy_profile{0}".format(region_idx)

        # Create a variable for this profiling region
        reader = FortranStringReader(
            "type(ProfileData), save :: {0}".format(var_name))
        # Tell the reader that the source is free format
        reader.set_format(FortranFormat(True, False))
        decln = Fortran2003.Type_Declaration_Stmt(reader)
        spec_part.content.append(decln)

        # Find the parent in the parse tree - first get a pointer to the
        # AST for the content of this region.
        content_ast = self.profile_body.children[0].ast
        # Now store the parent of this region
        # pylint: disable=protected-access
        fp_parent = content_ast._parent
        # pylint: enable=protected-access
        # Find the location of the AST of our first child node in the
        # list of child nodes of our parent in the fparser parse tree.
        ast_start_index = object_index(fp_parent.content,
                                       content_ast)
        # Finding the location of the end is harder as it might be the
        # end of a clause within an If or Select block. We therefore
        # work back up the fparser2 parse tree until we find a node that is
        # a direct child of the parent node.
        ast_end_index = None
        if self.profile_body[-1].ast_end:
            ast_end = self.profile_body[-1].ast_end
        else:
            ast_end = self.profile_body[-1].ast
        # Keep a copy of the pointer into the parse tree in case of errors
        ast_end_copy = ast_end

        while ast_end_index is None:
            try:
                ast_end_index = object_index(fp_parent.content,
                                             ast_end)
            except ValueError:
                # ast_end is not a child of fp_parent so go up to its parent
                # and try again
                # pylint: disable=protected-access
                if hasattr(ast_end, "_parent") and ast_end._parent:
                    ast_end = ast_end._parent
                    # pylint: enable=protected-access
                else:
                    raise InternalError(
                        "Failed to find the location of '{0}' in the fparser2 "
                        "Parse Tree:\n{1}\n".format(str(ast_end_copy),
                                                    str(fp_parent.content)))

        # Add the profiling-end call
        reader = FortranStringReader(
            "CALL ProfileEnd({0})".format(var_name))
        # Tell the reader that the source is free format
        reader.set_format(FortranFormat(True, False))
        pecall = Fortran2003.Call_Stmt(reader)
        fp_parent.content.insert(ast_end_index+1, pecall)

        # Add the profiling-start call
        reader = FortranStringReader(
            "CALL ProfileStart('{0}', '{1}', {2})".format(
                routine_name, region_name, var_name))
        reader.set_format(FortranFormat(True, False))
        pscall = Fortran2003.Call_Stmt(reader)
        fp_parent.content.insert(ast_start_index, pscall)
