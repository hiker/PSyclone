
''' This module tests the DAG generator using pytest '''

import os
import pytest
from parse import ParseError
import make_dag

# constants
BASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "test_files", "dag")

CODE = '''
module test_dag
contains
  subroutine testkern_qr_code(a,b,c,d)
    integer, intent(inout) :: a, b, c, d, e

    a = b + c
    d = a + e

  end subroutine testkern_qr_code
end module test_dag
'''

def test_basic():
    make_dag.main(os.path.join(BASE_PATH, "triple_product.f90"))
