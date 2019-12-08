import ast
import functools
import inspect
import pandas as pd
import networkx as nx


class Expression:
    def __init__(self):
        pass


class AssignExpression(Expression):
    def __init__(self, targets, segment, doc=None):
        super().__init__()
        self.__targets = targets
        self.__segment = segment
        self.__names = list()
        self.__calls = list()
        self.__constants = list()
        self.__doc = doc

    @property
    def targets(self):
        return self.__targets

    @property
    def segment(self):
        return self.__segment

    @property
    def names(self):
        return self.__names

    @names.setter
    def names(self, name):
        self.__names.append(name)

    @property
    def calls(self):
        return self.__calls

    @calls.setter
    def calls(self, name):
        self.__calls.append(name)

    @property
    def constants(self):
        return self.__constants

    @constants.setter
    def constants(self, name):
        self.__constants.append(name)

    @property
    def doc(self):
        return self.__doc

    @doc.setter
    def doc(self, doc):
        self.__doc = doc


class AssignmentGrapher(ast.NodeVisitor):
    def __init__(self, id, sourcecode):
        self.__id = id
        self.__sourcecode = sourcecode
        self.__expressions = list()
        self.__current = None
        self.__doc = None

    def visit_Assign(self, node):
        expression = AssignExpression([t.id for t in node.targets],
                                      ast.get_source_segment(self.__sourcecode, node, padded=True))
        self.__current = expression
        self.__expressions.append(self.__current)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        self.__doc = ast.get_docstring(node)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.__current.names = node.id
        self.generic_visit(node)

    def visit_Call(self, node):
        call = (hasattr(node.func, 'id') and node.func.id) or \
               (hasattr(node.func, 'attr') and node.func.attr)
        self.__current.calls = call
        self.generic_visit(node)

    def visit_Constant(self, node):
        self.__current.constants = node.value
        self.generic_visit(node)

    def visit_Return(self, node):
        expression = AssignExpression([ self.__id ],
                                      ast.get_source_segment(self.__sourcecode, node, padded=True),
                                      self.__doc)
        self.__current = expression
        self.__expressions.append(self.__current)
        self.generic_visit(node)

    def visit_Expr(self, node):
        if not hasattr(node, 'ctx') and hasattr(node, 'value') and hasattr(node.value, 'func'):
            expression = AssignExpression([ node.value.func.value.id ],
                                          ast.get_source_segment(self.__sourcecode, node, padded=True))
            self.__current = expression
            self.__expressions.append(self.__current)
            self.generic_visit(node)

    @property
    def expressions(self):
        return self.__expressions

    def lineage(self):
        return [ (t, n, e.segment, e.doc) for e in self.__expressions for t in e.targets for n in e.names ]

    def edges(self):
        # source, target, key, attributes
        return [ (n, t, n+"_"+t+"_"+e.segment, { "label": e.segment } ) for e in self.__expressions for t in e.targets for n in e.names ]

    def export(self, filename):
        G = nx.MultiDiGraph()
        G.add_edges_from(self.edges())
        # add doc to id node
        G.nodes[self.__id]['label'] = self.__doc
        nx.write_graphml(G, filename)

    def parse(self):
        tree = ast.parse(self.__sourcecode)
        self.visit(tree)
        return self

    @classmethod
    def parse_code(self, id, sourcecode):
        grapher = AssignmentGrapher(id, sourcecode)
        return grapher.parse()


def inspect_lineage(id):
    def decorator_lineage(func):
        @functools.wraps(func)
        def wrapper_lineage(*args, **kwargs):
            return func(*args, **kwargs)

        sourcelines = inspect.getsourcelines(func)
        # skip the first line which contains the decorator itself
        grapher = AssignmentGrapher.parse_code(id, ''.join(sourcelines[0][1:]))
        grapher.export(id + ".graphml")
        return wrapper_lineage

    return decorator_lineage
