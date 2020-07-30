from typing import Dict, List

from slither.exceptions import SlitherException
from slither.solc_parsing.types.types import Block, ASTNode, Statement, VariableDeclarationStatement, \
    VariableDeclaration, Literal

"""
Every raw node should contain the following properties

id (int): internal node id
name (string): type of node
src (string): src offset
"""


def parse_block(raw: Dict) -> Block:
    """
    children:
        Statement[]
    """

    parsed_statements: List[Statement] = []
    for statement in raw['children']:
        parsed_statement = parse(statement)
        assert isinstance(parsed_statement, Statement)
        parsed_statements.append(parsed_statement)

    return Block(raw['src'], parsed_statements)


def parse_variable_definition_statement(raw: Dict) -> VariableDeclarationStatement:
    """
    children:
        VariableDeclaration[]
        Expression?
    """

    parsed_children: List[ASTNode] = []
    for child in raw['children']:
        parsed_children.append(parse(child))

    initial_value = None
    if not isinstance(parsed_children[-1], VariableDeclaration):
        initial_value = parsed_children[-1]
        parsed_children = parsed_children[:-1]

    return VariableDeclarationStatement(raw['src'], parsed_children, initial_value)


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
    attrs = raw['attributes']
    return Literal(raw['src'], attrs['token'], attrs['value'], attrs['hexvalue'], attrs['subdenomination'])


def parse_unsupported(raw: Dict) -> ASTNode:
    raise SlitherException("unsupported compact json node", raw['nodeType'], raw)


def parse(raw: Dict) -> ASTNode:
    return PARSERS.get(raw['name'], parse_unsupported)(raw)


PARSERS = {
    'Block': parse_block,
    'VariableDefinitionStatement': parse_variable_definition_statement,
    'VariableDeclaration': parse_variable_declaration,
    'Literal': parse_literal,
}
