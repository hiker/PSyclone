# -----------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -----------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

''' Provides support for breaking long fortran lines into smaller ones
to allow the code to conform to the maximum line length limits (132
for f90 free format and onwards '''


class FortLineLength(object):

    ''' This class take a fortran code as a string and line wraps any
    lines that are larger than the specified line length'''

    def __init__(self, line_length=132):
        self._line_types = ["statement", "openmp_directive",
                            "openacc_directive", "unknown"]
        self._line_length = line_length

    def process(self, fortran_in):
        ''' takes fortran code as a string as input and output fortran
        code as a string with any long lines wrappe appropriately '''

        total_wrapped_lines = 0
        fortran_out = ""
        for line in fortran_in.split('\n'):
            if len(line) > self._line_length:

                line_type = self._get_line_type(line)
                if line_type in ["openmp_directive", "openacc_directive",
                                 "unknown"]:
                    raise Exception(
                            "fort_line_length: Unsupported line type [{0}]"
                            " found ...\n{1}".format(line_type, line))

                total_wrapped_lines += 1

                while len(line) > self._line_length:
                    # line_length-2 for continuation characters
                    break_point = self._find_break_point(line,
                                                         self._line_length-2)
                    fortran_out += line[:break_point] + " &\n"
                    line = line[break_point:]
                if line:
                    fortran_out += line + "\n"

            else:
                fortran_out += line + "\n"
        fortran_out += "! fort_line_length wrapped {0} lines\n".\
            format(str(total_wrapped_lines))
        return fortran_out

    def _get_line_type(self, line):
        ''' Classes lines into diffrent types. This is required as
        directives need different continuation characters to fortran
        statements. It also enables us to know a little about the
        structure of the line which could be useful at some point.'''

        import re
        stat = re.compile(r'^\s*(INTEGER|REAL|TYPE|CALL|SUBROUTINE|USE)',
                       flags=re.I)
        omp = re.compile(r'^"!$OMP"', flags=re.I)
        acc = re.compile(r'^"!$ACC"', flags=re.I)
        if stat.match(line):
            return "statement"
        if omp.match(line):
            return "openmp_directive"
        if acc.match(line):
            return "openacc_directive"
        return "unknown"

    def _find_break_point(self, line, max_index):
        ''' find the most appropriate break point for a fortran line '''

        # look for ", " as we know that fparser outputs lists this way and
        # our long lines are due to lists
        idx = line.rfind(", ", 0, max_index)
        if idx == -1:
            raise Exception(
                "Error in find_break_point. No suitable break point found")
        return idx+1
