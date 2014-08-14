# Copyright 2013 STFC, all rights reserved
import fparser

class Alg(object):
  '''
  Generate a modified algorithm code for a single algorithm specification. Takes the ast of the algorithm specification output from the function :func:`parse.parse` and an instance of the :class:`psyGen.PSy` class as input.

  :param ast ast: An object containing an ast of the algorithm specification which was produced by the function :func:`parse.parse`.
  :param PSy psy: An object (:class:`psyGen.PSy`) containing information about the PSy layer.

  For example:

  >>> from parse import parse
  >>> ast,info=parse("argspec.F90")
  >>> from psyGen import PSy
  >>> psy=PSy(info)
  >>> from algGen import Alg
  >>> alg=Alg(ast,psy)
  >>> print(alg.gen)

  '''
  def __init__(self,ast,psy):
    self._ast=ast
    self._psy=psy

  @property
  def gen(self):
    '''
    Generate modified algorithm code

    :rtype: ast

    '''
    from fparser import api
    from f2pygen import adduse
    psyName=self._psy.name
    # run through all statements looking for procedure calls
    idx=0
    for stmt, depth in api.walk(self._ast, -1):

      if isinstance(stmt,fparser.statements.Call):
        if stmt.designator=="invoke":
          from psyGen import Invoke
          invokeInfo=self._psy.invokes.invoke_list[idx]
          stmt.designator=invokeInfo.name
          stmt.items=invokeInfo.orig_unique_args
          adduse(psyName,stmt.parent,only=True,funcnames=[invokeInfo.name])
          idx+=1
    return self._ast

class TestAlgGenClass:
  ''' AlgGen class unit tests. We use the generate function as parse and PSyFactory need to be called
  before AlgGen so it is simpler to use the generate function '''

  def test_single_invoke_gunghoproto(self):
    ''' test for correct code transformation for a single function specified in an invoke call for the
        gunghoproto api '''
    import os
    from generator import generate
    alg,psy=generate(os.path.join("test_files","gunghoproto","1_single_function.f90"),api="gunghoproto")
    assert (str(alg).find("USE psy_single_function, ONLY: invoke_testkern_type")!=-1 and \
            str(alg).find("CALL invoke_testkern_type(f1, f2, m1)")!=-1)

  def test_single_invoke_dynamo0p1(self):
    ''' test for correct code transformation for a single function specified in an invoke call for the
        gunghoproto api '''
    import os
    from generator import generate
    alg,psy=generate(os.path.join("test_files","dynamo0p1","1_single_function.f90"),api="dynamo0.1")
    assert (str(alg).find("USE psy_single_function, ONLY: invoke_testkern_type")!=-1 and \
            str(alg).find("CALL invoke_testkern_type(f1, f2, m1)")!=-1)


