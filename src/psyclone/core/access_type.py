# -----------------------------------------------------------------------------
# BSD 3-Clause License
#
# Copyright (c) 2017-2019, Science and Technology Facilities Council.
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
# -----------------------------------------------------------------------------


from __future__ import print_function, absolute_import
from enum import Enum
from psyclone.configuration import Config


class AccessType(Enum):
    '''A simple enum-class for the various valid access types.
    '''

    INC = 1
    WRITE = 2
    READ = 3
    READWRITE = 4
    SUM = 5

    @staticmethod
    def get_size():
        ''':returns: The number of elements in this emnumerator.
        :rtype int'''
        return len(AccessType)

    def __str__(self):
        '''Convert to a string representation. The test
        test_arg_descriptor_repr needs this function to return
        the api_name() (and not e.g. just name of the enum,
        like READ)..
        :return: API name for this string.
        :rtype: str
        '''
        return self.api_name()

    def api_name(self):
        '''This convenient function returns the name of the type in the
        current API. E.g. in a dynamo0.3 API, WRITE --> "gh_write"
        :returns: The API specific name.
        :rtype: str
        '''
        api_config = Config.get().api_conf()
        rev_access_mapping = api_config.get_reverse_access_mapping()
        return rev_access_mapping[self]

    @staticmethod
    def from_string(access_string):
        '''Convert a string (e.g. "read") into the corresponding
        AccessType enum value (AccessType.READ).
        :param str access_string: Access type as string.
        :returns" Corresponding AccessType enum.
        :Raises: KeyError if access_string is not a valid access type.
        '''
        for access in AccessType:
            if access.name == access_string.upper():
                return access
        raise KeyError("Unknown access type '{0}'.".format(access_string))