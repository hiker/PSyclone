# -----------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
# -----------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

''' Provides support for breaking long fortran lines into smaller ones
to allow the code to conform to the maximum line length limits (132
for f90 free format is the default)'''


class FortLineLength(object):

    ''' This class take a free format fortran code as a string and
    line wraps any lines that are larger than the specified line
    length'''

    def __init__(self, line_length=132):
        self._line_length = line_length
        self._line_types = ["statement", "openmp_directive",
                            "openacc_directive", "comment",
                            "unknown"]
        self._cont_start = {"statement":"",
                            "openmp_directive":"!$omp& ",
                            "openacc_directive":"!$acc& ",
                            "comment":"!& "}
        self._cont_end = {"statement":" &",
                          "openmp_directive":" &",
                          "openacc_directive":" &",
                          "comment":""}
        self._key_lists = {"statement":[", ", ",", " "],
                           "openmp_directive":[" ", ",",")"],
                           "openacc_directive":[" ", ",",")"],
                           "comment":[" ",".",","]}

    def process(self, fortran_in):
        ''' takes fortran code as a string as input and output fortran
        code as a string with any long lines wrappe appropriately '''

        fortran_out = ""
        for line in fortran_in.split('\n'):
            if len(line) > self._line_length:
                line_type = self._get_line_type(line)
                if line_type == "unknown":
                    raise Exception(
                            "fort_line_length: Unsupported line type [{0}]"
                            " found ...\n{1}".format(line_type, line))

                while len(line) > self._line_length:
                    break_point = self._find_break_point(
                        line, self._line_length-len(self._cont_end[line_type]),
                        self._key_lists[line_type])
                    fortran_out += line[:break_point] + self._cont_end[line_type] + "\n"
                    line = line[break_point:]
                if line:
                    fortran_out += self._cont_start[line_type] + line + "\n"
            else:
                fortran_out += line + "\n"

        # We add an extra newline so remove it when we return
        return fortran_out[:-1]

    def _get_line_type(self, line):
        ''' Classes lines into diffrent types. This is required as
        directives need different continuation characters to fortran
        statements. It also enables us to know a little about the
        structure of the line which could be useful at some point.'''

        import re
        stat = re.compile(r'^\s*(INTEGER|REAL|TYPE|CALL|SUBROUTINE|USE)',
                          flags=re.I)
        omp = re.compile(r'^\s*!\$OMP', flags=re.I)
        acc = re.compile(r'^\s*!\$ACC', flags=re.I)
        comment = re.compile(r'^\s*!')
        if stat.match(line):
            return "statement"
        if omp.match(line):
            return "openmp_directive"
        if acc.match(line):
            return "openacc_directive"
        if comment.match(line):
            return "comment"
        return "unknown"

    def _find_break_point(self, line, max_index, key_list):
        ''' find the most appropriate break point for a fortran line '''

        for key in key_list:
            idx = line.rfind(key, 0, max_index)
            if idx != -1:
                return idx+len(key)-1
        raise Exception(
            "Error in find_break_point. No suitable break point found")
