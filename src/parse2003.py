''' Module containing classes related to parsing Fortran code using
    the f2003 parser '''
import ast
import operator as op

# supported operators
operators = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul,
             ast.Div: op.truediv, ast.Pow: op.pow, ast.BitXor: op.xor,
             ast.USub: op.neg}

def eval_expr(expr):
    """
    >>> eval_expr('2^6')
    4
    >>> eval_expr('2**6')
    64
    >>> eval_expr('1 + 2*3**(4^5) / (6 + -7)')
    -5.0
    """
    return eval_(ast.parse(expr, mode='eval').body)

def eval_(node):
    if isinstance(node, ast.Num): # <number>
        return node.n
    elif isinstance(node, ast.BinOp): # <left> <operator> <right>
        return operators[type(node.op)](eval_(node.left), eval_(node.right))
    elif isinstance(node, ast.UnaryOp): # <operator> <operand> e.g., -1
        return operators[type(node.op)](eval_(node.operand))
    else:
        raise TypeError(node)

def walk(children, my_type, indent=0, debug=False):
    '''' Walk down the tree produced by the f2003 parser where children
    are listed under 'content'.  Returns a list of all nodes with the
    specified type. '''
    local_list = []
    for child in children:
        if debug:
            print indent*"  " + "child type = ", type(child)
        if isinstance(child, my_type):
            local_list.append(child)
            
        # Depending on their level in the tree produced by fparser2003,
        # some nodes have children listed in .content and some have them
        # listed under .items...
        if hasattr(child, "content"):
            local_list += walk(child.content, my_type, indent+1, debug)
        elif hasattr(child, "items"):
            local_list += walk(child.items, my_type, indent+1, debug)
        else:
            pass

    return local_list


class Loop(object):
    ''' Representation of a Do loop '''

    def __init__(self):
        self._var_name = ""

    def load(self, parsed_loop):
        ''' Takes the supplied loop object produced by the f2003 parser
        and extracts relevant information from it to populate this object '''
        from fparser.Fortran2003 import Nonlabel_Do_Stmt, Loop_Control, Name
        #print type(parsed_loop)
        for node in parsed_loop.content:
            #print "  "+str(type(node))
            if isinstance(node, Nonlabel_Do_Stmt):
                var_name = walk(node.items, Name)
                self._var_name = str(var_name[0])
                #for item in node.items:
                #    print "    "+str(type(item))
                #    if isinstance(item, Loop_Control):
                #        for lcitem in item.items:
                #            print "      "+str(type(lcitem))
                #            print "      "+str(lcitem)

    @property
    def var_name(self):
        ''' Return a string containing the name of the loop variable '''
        return self._var_name


class Variable(object):
    ''' Representation of a Fortran variable. Can be a scalar or an
    array reference '''

    def __init__(self):
        # Name of this quantity in the DAG (may not be the same as
        # _orig_name because of assignment)
        self._name = None
        # Name of the variable as used in the raw Fortran code
        self._orig_name = None
        self._is_array_ref = False
        # List of the variables used to index into the array
        self._indices = []
        # Comma-delimited, string representation of the array-index
        # expression e.g. "ji, jj+1"
        self._index_expr = ""

    def __str__(self):
        name = self._name
        if self._is_array_ref:
            name += "("
            name += self.index_expr
            name += ")"
        return name

    @property
    def index_expr(self):
        ''' Return the full index expression of this variable if it is an
        array reference. '''
        if not self._is_array_ref:
            return ""

        import re
        tokens = re.split(',', self._index_expr)
        assert len(tokens) == len(self._indices)
        simplified_expr = ""
        for idx, tok in enumerate(tokens):
            if idx > 0:
                simplified_expr += ","

            # This is a very simplistic piece of code intended to
            # process array index expressions of the form 
            # ji+1-1+1. It ignores anything other than '+1' and '-1'.
            num_plus = tok.count("+1")
            num_minus = tok.count("-1")
            if num_plus > 0 or num_minus > 0:
                basic_expr = tok.replace("+1","")
                basic_expr = basic_expr.replace("-1","")
                simplified_expr += basic_expr
                net_incr = num_plus - num_minus
                if net_incr < 0:
                    simplified_expr += str(net_incr)
                elif net_incr > 0:
                    simplified_expr += "+" + str(net_incr)
                else:
                    # The +1's and -1's have cancelled each other out
                    pass
            else:
                # This part of the index expression contains no "+1"s and
                # no "-1"s so we leave it unchanged
                simplified_expr += tok
        self._index_expr = simplified_expr

        return self._index_expr

    def load(self, node, mapping=None, lhs=False):
        ''' Populate the state of this Variable object using the supplied
        output of the f2003 parser. If lhs is True then this variable
        appears on the LHS of an assignment and thus represents a new 
        entity in a DAG. '''
        from fparser.Fortran2003 import Name, Part_Ref, Real_Literal_Constant
        from parse import ParseError

        if isinstance(node, Name):
            name = str(node)
            self._orig_name = name[:]
            if mapping and name in mapping:
                self._name = mapping[name]
                if lhs:
                    # If this variable appears on the LHS of an assignment
                    # then it is effectively a new variable for the
                    # purposes of the graph.
                    self._name += "'"
            else:
                self._name = name
            self._is_array_ref = False

        elif isinstance(node, Part_Ref):
            self._name = str(node.items[0])
            self._orig_name = self._name
            self._is_array_ref = True
            # Get and store the original array-index expression (i.e. before
            # we start re-naming any of the variables involved). This gives
            # us the information on any expressions in the array indexing, e.g.
            # (ji+1,jj-1)
            self._index_expr = str(node.items[1]).replace(" ","")

            # This recurses down and finds the names of all of the variables
            # in the array-index expression (i.e. ignoring whether they
            # are "+1" etc.)
            array_indices = walk(node.items[1].items, Name)

            for idx, index in enumerate(array_indices):
                name = index.string
                if mapping and name in mapping:
                    self._indices.append(mapping[name])
                    # Replace the reference to this variable in the index
                    # expression with the new name
                    self._index_expr = self._index_expr.replace(name,
                                                                mapping[name])
                else:
                    self._indices.append(name)


        elif isinstance(node, Real_Literal_Constant):
            self._name = str(node)
            self._orig_name = self._name
            self._is_array_ref = False
        else:
            raise ParseError("Unrecognised type for variable: {0}".
                             format(type(node)))

    @property
    def orig_name(self):
        ''' Return the name of this variable as it appeared in the
        the parsed Fortran code '''
        return self._orig_name

    @property
    def name(self):
        ''' Return the name of this variable as a string '''
        return self._name

    @name.setter
    def name(self, new_name):
        ''' Set or change the name of this variable '''
        self._name = new_name

    def rename(self, old_name, new_name):
        ''' Re-name the root name of this variable and/or its array
        index variables (if any) '''
        if self._name == old_name:
            self._name = new_name
        for idx, index  in enumerate(self._indices):
            if str(index) == old_name:
                # Need to replace reference in array-index expression as
                # well as re-naming this variable
                self._index_expr = self._index_expr.replace(old_name,
                                                            new_name)
                self._indices[idx] = new_name
