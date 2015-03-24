#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2015.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

from parse import parse
from psyGen import PSyFactory
import os

class TestPSyDynamo0p3API:
    ''' Tests for PSy layer code generation that are specific to the dynamo0.3 api. '''

    def test_vector_field(self):
        ''' tests that a vector field is declared correctly in the PSy layer '''
        ast,invokeInfo=parse(os.path.join(os.path.dirname(os.path.abspath(__file__)),"test_files","dynamo0p3","8_vector_field.f90"),api="dynamo0.3")
        psy=PSyFactory("dynamo0.3").create(invokeInfo)
        generated_code = psy.gen
        assert(str(generated_code).find("SUBROUTINE invoke_testkern_chi_type(f1, chi)")!=-1 and \
                  str(generated_code).find("TYPE(field_type), intent(inout) :: f1, chi(3)")!=-1)
