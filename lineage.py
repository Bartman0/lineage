import ast
import functools
import inspect
import pandas as pd


class Expression:
    def __init__(self):
        pass


class AssignExpression(Expression):
    def __init__(self, targets, segment):
        super().__init__()
        self.__targets = targets
        self.__segment = segment
        self.__names = list()
        self.__calls = list()
        self.__constants = list()

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


class AssignmentGrapher(ast.NodeVisitor):
    def __init__(self, sourcecode):
        self.__sourcecode = sourcecode
        self.__expressions = list()
        self.__current = None

    def visit_Assign(self, node):
        expression = AssignExpression([t.id for t in node.targets],
                                      ast.get_source_segment(self.__sourcecode, node, padded=True))
        self.__current = expression
        self.__expressions.append(expression)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.__current.names = node.id
        self.generic_visit(node)

    def visit_Call(self, node):
        self.__current.calls = node.func.attr
        self.generic_visit(node)

    def visit_Constant(self, node):
        self.__current.constants = node.value
        self.generic_visit(node)

    @property
    def expressions(self):
        return self.__expressions

    def lineage(self):
        # InspectLineage is seen as a source itself, remove it from the lineage
        return [ (t, n, e.segment) for e in self.__expressions for t in e.targets for n in e.names if n != 'InspectLineage' ]

    def export(self, filename):
        df = pd.DataFrame(self.lineage(), columns = [ 'target', 'source', 'segment' ])
        df.to_csv(filename + ".csv", sep=';', index=False)

    def parse(self):
        tree = ast.parse(self.__sourcecode)
        self.visit(tree)
        return self

    @classmethod
    def parse_code(self, sourcecode):
        grapher = AssignmentGrapher(sourcecode)
        return grapher.parse()


class InspectLineage:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.__func = func
        self.__num_calls = 0
        self.__sourcelines = inspect.getsourcelines(func)
        self.__grapher = AssignmentGrapher.parse_code(''.join(self.__sourcelines[0]))
        self.__lineage = self.__grapher.lineage()
        self.__grapher.export(str(self.__func.__name__) + ".lineage")

    def __call__(self, *args, **kwargs):
        self.__num_calls += 1
        # print(f"call of {self.func.__name__!r}")
        return self.__func(*args, **kwargs)
