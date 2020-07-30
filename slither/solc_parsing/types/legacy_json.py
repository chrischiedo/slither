from typing import Dict, List, Optional

from slither.exceptions import SlitherException
from slither.solc_parsing.types.types import Block, ASTNode, Statement, VariableDeclarationStatement, \
    VariableDeclaration, Literal, ParameterList, Return, Expression, TupleExpression, ExpressionStatement, Assignment, \
    Identifier, FunctionCall, Throw

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

    return VariableDeclaration(raw['src'], raw['attributes']['name'], None, None, raw['attributes']['type'], False, '')


def parse_literal(raw: Dict) -> Literal:
    attrs = raw['attributes']
    return Literal(raw['src'], attrs['token'], attrs['value'], attrs['hexvalue'], attrs['subdenomination'], '')


def parse_parameter_list(raw: Dict) -> ParameterList:
    """
    children:
        (VariableDeclaration?)[]
    """

    parameters_parsed: List[Optional[VariableDeclaration]] = []

    for child in raw['children']:
        if child:
            child_parsed = parse(child)
            assert isinstance(child_parsed, VariableDeclaration)

            parameters_parsed.append(child_parsed)
        else:
            parameters_parsed.append(None)

    return ParameterList(raw['src'], parameters_parsed)


def parse_return(raw: Dict) -> Return:
    """
    children:
        Expression?
    """

    if len(raw['children']) > 0:
        expr_parsed = parse(raw['children'][0])

        assert isinstance(expr_parsed, Expression)
    else:
        expr_parsed = None

    return Return(raw['src'], expr_parsed)


def parse_tuple_expression(raw: Dict) -> TupleExpression:
    """
    children:
        (Expression?)[]
    """

    children_parsed: List[Optional[Expression]] = []

    for child in raw['children']:
        if child:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)

            children_parsed.append(child_parsed)
        else:
            children_parsed.append(None)

    return TupleExpression(raw['src'], children_parsed, False, 'tuple()')


def parse_expression_statement(raw: Dict) -> ExpressionStatement:
    """
    children:
        Expression
    """

    expression_parsed = parse(raw['children'][0])
    assert isinstance(expression_parsed, Expression)

    return ExpressionStatement(raw['src'], expression_parsed)


def parse_assignment(raw: Dict) -> Assignment:
    """
    children:
        left (Expression)
        right (Expression)

    attributes:
        operator (string)
        type (string)
    """

    left = parse(raw['children'][0])
    assert isinstance(left, Expression)

    right = parse(raw['children'][1])
    assert isinstance(right, Expression)

    return Assignment(raw['src'], left, raw['attributes']['operator'], right, raw['attributes']['type'])


def parse_identifier(raw: Dict) -> Identifier:
    """
    attributes:
        type (string)
        value (string)
    """

    return Identifier(raw['src'], raw['attributes']['value'], raw['attributes']['type'])


def parse_function_call(raw: Dict) -> FunctionCall:
    """
    children:
        call (Expression)
        args (Expression[])

    attributes:
        type (string)
        type_conversion (bool)
    """

    call_parsed = parse(raw['children'][0])
    assert isinstance(call_parsed, Expression)

    args_parsed: List[Expression] = []
    if len(raw['children']) > 1:
        for child in raw['children'][1:]:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)

            args_parsed.append(child_parsed)

    return FunctionCall(raw['src'], 'functionCall', call_parsed, [], args_parsed, raw['attributes']['type'])


def parse_throw(raw: Dict) -> Throw:
    return Throw(raw['src'])


def parse_unsupported(raw: Dict) -> ASTNode:
    raise SlitherException("unsupported legacy json node", raw['name'], raw)


def parse(raw: Dict) -> ASTNode:
    try:
        return PARSERS.get(raw['name'], parse_unsupported)(raw)
    except SlitherException as e:
        raise e
    except Exception as e:
        raise SlitherException("failed to parse legacy json node", e, raw)


PARSERS = {
    'Block': parse_block,
    'VariableDefinitionStatement': parse_variable_definition_statement,
    'VariableDeclaration': parse_variable_declaration,
    'Literal': parse_literal,
    'ParameterList': parse_parameter_list,
    'Return': parse_return,
    'TupleExpression': parse_tuple_expression,
    'ExpressionStatement': parse_expression_statement,
    'Assignment': parse_assignment,
    'Identifier': parse_identifier,
    'FunctionCall': parse_function_call,
    'Throw': parse_throw,
}
