from typing import Dict, List

from slither.exceptions import SlitherException
from slither.solc_parsing.types.types import Block, ASTNode, Statement, VariableDeclarationStatement, \
    VariableDeclaration, Expression, Literal

"""
Every raw node should contain the following properties

id (int): internal node id
nodeType (string): type of node
src (string): src offset
"""


def parse_block(raw: Dict) -> Block:
    """
    statements (Statement[]): list of statements
    """

    parsed_statements: List[Statement] = []
    for statement in raw['statements']:
        parsed_statement = parse(statement)
        assert isinstance(parsed_statement, Statement)
        parsed_statements.append(parsed_statement)

    return Block(raw['src'], parsed_statements)


def parse_variable_declaration_statement(raw: Dict) -> VariableDeclarationStatement:
    """
    assignments (int[]): ids of variables declared
    declarations (VariableDeclaration[]): variables declared
    initialValue (Expression?): initial value, if any
    """

    parsed_variables: List[VariableDeclaration] = []
    for declaration in raw['declarations']:
        parsed_variable = parse(declaration)
        assert isinstance(parsed_variable, VariableDeclaration)
        parsed_variables.append(parsed_variable)

    initial_value = parse(raw['initialValue'])
    assert isinstance(initial_value, Expression)

    return VariableDeclarationStatement(raw['src'], parsed_variables, initial_value)


def parse_variable_declaration(raw: Dict) -> VariableDeclaration:
    """
    name (string)
    typeName (ElementaryTypeName)
    constant (boolean)
    mutability (string)
    stateVariable (boolean)
    storageLocation (string)
    overrides (OverrideSpecifier[]?)
    visibility (string)
    value (Expression?)
    scope (int)
    typeDescriptions (TypeDescription)
    functionSelector (string): only if public state variable
    indexed (bool): only if event variable
    baseFunctions (int[]): only if overriding function
    """

    return VariableDeclaration(raw['src'])


def parse_literal(raw: Dict) -> Literal:
    """
    kind (string)
    value (string)
    hexValue (string)
    subdenomination (string?)

    +ExpressionAnnotation
    """

    return Literal(raw['src'], raw['kind'], raw['value'], raw['hexValue'], raw['subdenomination'])


def parse_unsupported(raw: Dict) -> ASTNode:
    raise SlitherException("unsupported compact json node", raw['nodeType'], raw)


def parse(raw: Dict) -> ASTNode:
    return PARSERS.get(raw['nodeType'], parse_unsupported)(raw)


PARSERS = {
    'Block': parse_block,
    'VariableDeclarationStatement': parse_variable_declaration_statement,
    'VariableDeclaration': parse_variable_declaration,
    'Literal': parse_literal,
}
