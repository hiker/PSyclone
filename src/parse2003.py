''' Module containing classes related to parsing Fortran code using
    the f2003 parser '''


def walk(children, my_type, indent=0, debug=False):
    '''' Walk down the tree produced by the f2003 parser where children
    are listed under 'content'.  Returns a list of all nodes with the
    specified type. '''
    from fparser.Fortran2003 import Section_Subscript_List, Name
    local_list = []
    for idx, child in enumerate(children):
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
        print type(parsed_loop)
        for node in parsed_loop.content:
            print "  "+str(type(node))
            if isinstance(node, Nonlabel_Do_Stmt):
                var_name = walk(node.items, Name)
                self._var_name = str(var_name[0])
                for item in node.items:
                    print "    "+str(type(item))
                    if isinstance(item, Loop_Control):
                        for lcitem in item.items:
                            print "      "+str(type(lcitem))
                            print "      "+str(lcitem)

    @property
    def var_name(self):
        ''' Return a string containing the name of the loop variable '''
        return self._var_name


class Variable(object):
    ''' Representation of a Fortran variable. Can be a scalar or an
    array reference '''

    def __init__(self):
        self._name = None
        self._is_array_ref = False
        self._indices = []

    def __str__(self):
        name = self._name
        if self._is_array_ref:
            name += "("
            for idx, index in enumerate(self._indices):
                if idx > 0:
                    name += ", "
                name += index
            name += ")"
        return name

    def load(self, node, mapping=None):
        ''' Populate the state of this Variable object using the supplied
        output of the f2003 parser '''
        from fparser.Fortran2003 import Name, Part_Ref
        from parse import ParseError
        if isinstance(node, Name):
            name = str(node)
            if mapping and name in mapping:
                self._name = mapping[name]
            else:
                self._name = name
            self._is_array_ref = False
        elif isinstance(node, Part_Ref):
            self._name = str(node.items[0])
            self._is_array_ref = True
            array_indices = walk(node.items[1].items, Name)
            for index in array_indices:
                name = str(index)
                if mapping and name in mapping:                    
                    self._indices.append(mapping[name])
                else:
                    self._indices.append(name)
        else:
            raise ParseError("Unrecognised type for variable: {0}".
                             format(type(node)))
