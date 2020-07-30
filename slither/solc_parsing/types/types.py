from typing import List


class ASTNode:
    __slots__ = "src"

    def __init__(self, src: str):
        self.src = src


class Statement(ASTNode):
    pass


class Block(Statement):
    __slots__ = "statements"

    def __init__(self, src: str, statements: List[Statement]):
        super().__init__(src)
        self.statements = statements


class Expression(ASTNode):
    pass


class Declaration(ASTNode):
    pass


class VariableDeclaration(Declaration):
    __slots__ = "name", "type_name", "constant", "mutability", "state_variable", "storage_location", "overrides", "visibility", "value", "scope", "type_descriptions"

    def __init__(self, src: str):
        super().__init__(src)


class VariableDeclarationStatement(Statement):
    __slots__ = "variables", "initial_value"

    def __init__(self, src: str, variables: List[VariableDeclaration], initial_value: Expression):
        super().__init__(src)
        self.variables = variables
        self.initial_value = initial_value


class PrimaryExpression(Expression):
    pass


class Literal(PrimaryExpression):
    __slots__ = "kind", "value", "hex_value", "subdenomination"

    def __init__(self, src: str, kind: str, value: str, hex_value: str, subdenomination: str):
        super().__init__(src)
        self.kind = kind
        self.value = value
        self.hex_value = hex_value
        self.subdenomination = subdenomination
