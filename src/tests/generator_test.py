#-------------------------------------------------------------------------------
# (c) The copyright relating to this work is owned jointly by the Crown,
# Met Office and NERC 2014.
# However, it has been created with the help of the GungHo Consortium,
# whose members are identified at https://puma.nerc.ac.uk/trac/GungHo/wiki
#-------------------------------------------------------------------------------
# Author R. Ford STFC Daresbury Lab

from generator import generate, GenerationError
import pytest

class TestGenerate:
   ''' unit tests for the generate function '''

   def test_non_existant_filename(self):
       ''' checks that algGen raises appropriate error when a non-existant filename is supplied '''       
       import pytest
       with pytest.raises(IOError):
           generate("non_existant_file.f90")

   def test_invalid_api(self):
       ''' checks that algGen raises appropriate error when an invalid api is supplied '''       
       import os
       import pytest
       with pytest.raises(GenerationError):
           generate(os.path.join("test_files","dynamo0p1","algorithm","1_single_function.f90"), api="invalid")

   def test_invalid_kernel_path(self):
      ''' checks that algGen raises appropriate error when an invalid search path for kernel source files is supplied '''
      import os
      with pytest.raises(IOError):
         generate(os.path.join("test_files","dynamo0p1","algorithm","1_single_function.f90"), api="dynamo0.1", kernel_path="does_not_exist")

   def test_wrong_kernel_path(self):
      ''' checks that algGen raises appropriate error when the kernel code cannot be found in the specified search path '''
      import os
      with pytest.raises(IOError):
         generate(os.path.join("test_files","dynamo0p1","algorithm","1_single_function.f90"), api="dynamo0.1", kernel_path=os.path.join("test_files","gocean0p1"))

   def test_correct_kernel_path(self):
      ''' checks that algGen succeeds when the location of the kernel source code is *not* the same as that of the algorithm code '''
      import os
      alg,psy=generate(os.path.join("test_files","dynamo0p1","algorithm","1_single_function.f90"), 
                       api="dynamo0.1",
                       kernel_path=os.path.join("test_files","dynamo0p1","kernels"))

   def test_same_kernel_path(self):
      ''' checks that the generator succeeds when the search directory is the same as the algorithm code directory and a path is specified '''
      import os
      path=os.path.join("test_files","dynamo0p1","algorithm")
      alg,psy=generate(os.path.join(path,"1_single_function.f90"), 
                       api="dynamo0.1",
                       kernel_path=path)

   def test_similar_kernel_name(self):
      ''' checks that the generator does not match incorrect files '''
      import os
      alg,psy=generate(os.path.join("test_files","dynamo0p1","algorithm","1_single_function.f90"), 
                       api="dynamo0.1",
                       kernel_path=os.path.join("test_files","dynamo0p1","kernels2"))

   def test_recurse_correct_kernel_path(self):
      ''' checks that the generator succeeds when the location of the kernel source code is *not* the same as that of the algorithm code and recursion through subdirectories is required '''
      import os
      alg,psy=generate(os.path.join("test_files","dynamo0p1","algorithm","1_single_function.f90"), 
                       api="dynamo0.1",
                       kernel_path=os.path.join("test_files","dynamo0p1","kernels3"))
