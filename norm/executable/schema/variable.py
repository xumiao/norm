from norm.models.norm import retrieve_type, Status, Lambda
from norm.executable.schema import NormSchema

from typing import Union
import logging
logger = logging.getLogger(__name__)


class VariableName(NormSchema):

    def __init__(self, scope, name):
        """
        The variable and its scope
        :param scope: the scope of the variable
        :type scope: Union[VariableName, EvaluationExpr]
        :param name: the name of the variable
        :type name: str
        """
        super().__init__()
        from norm.executable.expression.evaluation import EvaluationExpr
        self.scope: Union[VariableName, EvaluationExpr] = scope
        self.name: str = name

    def __str__(self):
        if self.scope is not None:
            return '{}{}{}'.format(self.scope, self.VARIABLE_SEPARATOR, self.name)
        else:
            return self.name

    def variable_type(self):
        return self.lam

    def compile(self, context):
        session = context.session

        if self.scope is None:
            name = self.name
            if context.scope and name in context.scope:
                return ColumnVariable(None, name).compile(context)
            else:
                lam = retrieve_type(context.context_namespace, name, session=session)
                if lam is None:
                    lam = retrieve_type(context.search_namespaces, name, status=Status.READY, session=session)
                self.lam = lam
                return self
        else:
            if isinstance(self.scope, ColumnVariable) and str(self) in self.scope.lam:
                # Already joined
                self.scope.name = str(self)
                return self.scope

            lam = self.scope.variable_type()
            if self.name in lam:
                if isinstance(self.scope, (ColumnVariable, JoinVariable)):
                    # Join lam to the scope for the column
                    return JoinVariable(self.scope, self.name, lam).compile(context)
                else:
                    # A column of the scope variable
                    return ColumnVariable(self.scope, self.name).compile(context)
            else:
                # An evaluation whose first argument is the scope
                lam = retrieve_type(context.context_namespace, self.name, session=session)
                if lam is None:
                    lam = retrieve_type(context.search_namespaces, self.name, status=Status.READY,
                                        session=session)
                assert(lam is not None)
                self.lam = lam
                from norm.executable.expression.argument import ArgumentExpr
                arg = ArgumentExpr(expr=self.scope)
                self.scope = None
                from norm.executable.expression.evaluation import EvaluationExpr
                return EvaluationExpr([arg], self)


class ColumnVariable(VariableName):

    def __init__(self, scope, name):
        super().__init__(scope, name)

    def variable_type(self):
        return self.lam.get_type(self.name)

    def compile(self, context):
        if self.scope is None:
            assert(context.scope is not None)
            self.lam = context.scope
        else:
            self.lam = self.scope.lam
        return self

    def execute(self, context):
        return self.lam.data[self.name]


class JoinVariable(VariableName):

    def __init__(self, scope, name, joiner):
        super().__init__(scope, name)
        self.lam = joiner

    def variable_type(self):
        return self.lam.get_type(self.name)

    def compile(self, context):
        return self

    def execute(self, context):
        lam = self.scope.lam
        joiner = self.lam
        if str(self) not in lam.data.columns:
            to_join = joiner.data[[self.name]].rename(columns={self.name: str(self)})
            lam.data = lam.data.join(to_join, on=str(self.scope))
        return lam.data

