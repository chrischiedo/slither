from typing import Dict, List, Optional

from slither.exceptions import SlitherException
from slither.solc_parsing.types.types import Block, ASTNode, Statement, VariableDeclarationStatement, \
    VariableDeclaration, Expression, Literal, IfStatement, BinaryOperation, Identifier, ExpressionStatement, Assignment, \
    TryCatchClause, TryStatement, ParameterList, FunctionCall, MemberAccess, WhileStatement, UnaryOperation, \
    ForStatement, ElementaryTypeName, TupleExpression, Return, Break, Continue, EmitStatement, Throw, SourceUnit, \
    ContractDefinition, FunctionDefinition, EventDefinition

"""
Every raw node should contain the following properties

id (int): internal node id
nodeType (string): type of node
src (string): src offset
"""


def _extract_base_props(raw: Dict) -> Dict:
    return {
        'src': raw['src'],
        'id': raw['id'],
    }


def _extract_expr_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        'type_str': raw['typeDescriptions']['typeString'],
        'constant': raw.get("isConstant", False),  # Identifier doesn't expose this
        'pure': raw.get('isPure', False),  # Identifier doesn't expose this
    }


def _extract_decl_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        'name': raw['name'],
        'visibility': raw.get('visibility', None),
    }


def _extract_call_props(raw: Dict) -> Dict:
    params = parse(raw['parameters'])

    if 'returnParameters' in raw:
        rets = parse(raw['returnParameters'])
    else:
        rets = None

    return {
        **_extract_decl_props(raw),
        'params': params,
        'rets': rets,
    }


def parse_block(raw: Dict) -> Block:
    """
    statements (Statement[]): list of statements
    """

    parsed_statements: List[Statement] = []
    for statement in raw['statements']:
        parsed_statement = parse(statement)
        assert isinstance(parsed_statement, Statement)
        parsed_statements.append(parsed_statement)

    return Block(parsed_statements, **_extract_base_props(raw))


def parse_variable_declaration_statement(raw: Dict) -> VariableDeclarationStatement:
    """
    assignments (int[]): ids of variables declared
    declarations (VariableDeclaration[]): variables declared
    initialValue (Expression?): initial value, if any
    """

    parsed_variables: List[Optional[VariableDeclaration]] = []
    for declaration in raw['declarations']:
        if declaration:
            parsed_variable = parse(declaration)
            assert isinstance(parsed_variable, VariableDeclaration)
            parsed_variables.append(parsed_variable)
        else:
            parsed_variables.append(None)

    if raw['initialValue']:
        initial_value = parse(raw['initialValue'])
        assert isinstance(initial_value, Expression)
    else:
        initial_value = None

    return VariableDeclarationStatement(parsed_variables, initial_value, **_extract_base_props(raw))


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

    type_parsed = parse(raw['typeName'])

    if raw['value']:
        value_parsed = parse(raw['value'])
    else:
        value_parsed = None

    return VariableDeclaration(type_parsed, value_parsed, raw['typeDescriptions']['typeString'], raw['constant'],
                               **_extract_decl_props(raw))


def parse_literal(raw: Dict) -> Literal:
    """
    kind (string)
    value (string)
    hexValue (string)
    subdenomination (string?)

    +ExpressionAnnotation
    """

    return Literal(raw['kind'], raw['value'], raw['hexValue'], raw['subdenomination'], **_extract_expr_props(raw))


def parse_if_statement(raw: Dict) -> IfStatement:
    """
    condition (Expression)
    trueBody (Statement)
    falseBody (Statement)
    """

    condition_parsed = parse(raw['condition'])
    true_body_parsed = parse(raw['trueBody'])

    if 'falseBody' in raw and raw['falseBody']:
        false_body_parsed = parse(raw['falseBody'])
        assert isinstance(false_body_parsed, Statement)
    else:
        false_body_parsed = None

    assert isinstance(condition_parsed, Expression)
    assert isinstance(true_body_parsed, Statement)

    return IfStatement(condition_parsed, true_body_parsed, false_body_parsed, **_extract_base_props(raw))


def parse_binary_operation(raw: Dict) -> BinaryOperation:
    """
    leftExpression (Expression)
    operator (string)
    rightExpression (Expression)
    """

    left_parsed = parse(raw['leftExpression'])
    operator = raw['operator']
    right_parsed = parse(raw['rightExpression'])

    assert isinstance(left_parsed, Expression)
    assert isinstance(operator, str)
    assert isinstance(right_parsed, Expression)

    return BinaryOperation(left_parsed, operator, right_parsed, **_extract_expr_props(raw))


def parse_identifier(raw: Dict) -> Identifier:
    """
    name (string)
    """

    name = raw['name']

    assert isinstance(name, str)

    return Identifier(name, **_extract_expr_props(raw))


def parse_expression_statement(raw: Dict) -> ExpressionStatement:
    """
    expression (Statement)
    """

    expression_parsed = parse(raw['expression'])

    assert isinstance(expression_parsed, Expression)

    return ExpressionStatement(expression_parsed, **_extract_base_props(raw))


def parse_assignment(raw: Dict) -> Assignment:
    """
    operator (string)
    leftHandSide (Expression)
    rightHandSide (Expression)

    +Attributes
    """

    operator = raw['operator']
    left_parsed = parse(raw['leftHandSide'])
    right_parsed = parse(raw['rightHandSide'])

    assert isinstance(operator, str)
    assert isinstance(left_parsed, Expression)
    assert isinstance(right_parsed, Expression)

    return Assignment(left_parsed, operator, right_parsed, **_extract_expr_props(raw))


def parse_parameter_list(raw: Dict) -> ParameterList:
    """
    parameters (VariableDeclaration[])
    """

    parameters_parsed = []
    for param in raw['parameters']:
        parameters_parsed.append(parse(param))

    return ParameterList(parameters_parsed, **_extract_base_props(raw))


def parse_try_catch_clause(raw: Dict) -> TryCatchClause:
    """
    errorName (string)
    parameters (ParameterList?)
    block (Block)
    """

    error_name = raw['errorName']
    if raw['parameters']:
        parameters_parsed = parse(raw['parameters'])
    else:
        parameters_parsed = None
    block_parsed = parse(raw['block'])

    return TryCatchClause(error_name, parameters_parsed, block_parsed, **_extract_base_props(raw))


def parse_try_statement(raw: Dict) -> TryStatement:
    """
    externalCall (Expression)
    clauses (TryCatchClause[])
    """

    external_call_parsed = parse(raw['externalCall'])
    clauses_parsed = []

    for clause in raw['clauses']:
        clauses_parsed.append(parse(clause))

    return TryStatement(external_call_parsed, clauses_parsed, **_extract_base_props(raw))


def parse_function_call(raw: Dict) -> FunctionCall:
    """
    expression (Expression)
    names (string[])
    arguments (Expression[])
    tryCall (bool)
    kind (string)

    +Annotation
    """

    expression_parsed = parse(raw['expression'])
    names = raw['names']
    arguments_parsed = []
    for arg in raw['arguments']:
        arguments_parsed.append(parse(arg))

    return FunctionCall(raw['kind'], expression_parsed, names, arguments_parsed, **_extract_expr_props(raw))


def parse_member_access(raw: Dict) -> MemberAccess:
    """
    memberName (string)
    expression (Expression)
    """

    member_name = raw['memberName']
    expression_parsed = parse(raw['expression'])

    return MemberAccess(expression_parsed, member_name, **_extract_expr_props(raw))


def parse_while_statement_internal(raw: Dict, is_do_while: bool) -> WhileStatement:
    """
    condition (Expression)
    body (Statement)
    """

    condition_parsed = parse(raw['condition'])
    body_parsed = parse(raw['body'])

    return WhileStatement(condition_parsed, body_parsed, is_do_while, **_extract_base_props(raw))


def parse_while_statement(raw: Dict) -> WhileStatement:
    return parse_while_statement_internal(raw, False)


def parse_do_while_statement(raw: Dict) -> WhileStatement:
    return parse_while_statement_internal(raw, True)


def parse_unary_operation(raw: Dict) -> UnaryOperation:
    """
    prefix (bool)
    operator (string)
    subExpression (Expression)
    """

    expression_parsed = parse(raw['subExpression'])

    return UnaryOperation(raw['operator'], expression_parsed, raw['prefix'], **_extract_expr_props(raw))


def parse_for_statement(raw: Dict) -> ForStatement:
    """
    initializationExpression (Statement)
    condition (Expression)
    loopExpression (ExpressionStatement)
    body (Statement)
    """

    init_parsed = parse(raw['initializationExpression'])
    cond_parsed = parse(raw['condition'])
    loop_parsed = parse(raw['loopExpression'])
    body_parsed = parse(raw['body'])

    return ForStatement(init_parsed, cond_parsed, loop_parsed, body_parsed, **_extract_base_props(raw))


def parse_elementary_type_name(raw: Dict) -> ElementaryTypeName:
    """
    name (string)
    """

    name = raw['name']

    if 'stateMutability' in raw:
        mutability = raw['stateMutability']
    else:
        mutability = ''

    return ElementaryTypeName(name, mutability, **_extract_base_props(raw))


def parse_tuple_expression(raw: Dict) -> TupleExpression:
    """
    isInlineArray (bool)
    components (Expression[])
    """

    is_array = raw['isInlineArray']
    components_parsed = []
    for component in raw['components']:
        if component:
            components_parsed.append(parse(component))
        else:
            components_parsed.append(None)

    return TupleExpression(components_parsed, is_array, **_extract_expr_props(raw))


def parse_return(raw: Dict) -> Return:
    """
    expression (Expression?)
    functionReturnParameters (int)
    """
    if raw['expression']:
        expr_parsed = parse(raw['expression'])
    else:
        expr_parsed = None

    return Return(expr_parsed, **_extract_base_props(raw))


def parse_continue(raw: Dict) -> Continue:
    return Continue(**_extract_base_props(raw))


def parse_break(raw: Dict) -> Break:
    return Break(**_extract_base_props(raw))


def parse_throw(raw: Dict) -> Throw:
    return Throw(**_extract_base_props(raw))


def parse_emit_statement(raw: Dict) -> EmitStatement:
    """
    eventCall (FunctionCall)
    """

    return EmitStatement(parse(raw['eventCall']), **_extract_base_props(raw))


def parse_source_unit(raw: Dict) -> SourceUnit:
    nodes_parsed: List[ASTNode] = []

    for node in raw['nodes']:
        nodes_parsed.append(parse(node))

    return SourceUnit(nodes_parsed, **_extract_base_props(raw))


def parse_contract_definition(raw: Dict) -> ContractDefinition:
    nodes_parsed: List[ASTNode] = []
    for child in raw['nodes']:
        nodes_parsed.append(parse(child))

    return ContractDefinition(raw['contractKind'], raw['linearizedBaseContracts'], nodes_parsed,
                              **_extract_decl_props(raw))


def parse_function_definition(raw: Dict) -> FunctionDefinition:
    body_parsed = parse(raw['body'])
    modifiers_parsed = []

    for child in raw['modifiers']:
        modifiers_parsed.append(parse(child))

    return FunctionDefinition(raw['stateMutability'], raw['kind'], modifiers_parsed, body_parsed,
                              **_extract_call_props(raw))

def parse_event_definition(raw: Dict) -> EventDefinition:
    return EventDefinition(raw['anonymous'], **_extract_call_props(raw))

def parse_unsupported(raw: Dict) -> ASTNode:
    raise SlitherException("unsupported compact json node", raw['nodeType'], raw.keys(), raw)


def parse(raw: Dict) -> ASTNode:
    try:
        return PARSERS.get(raw['nodeType'], parse_unsupported)(raw)
    except SlitherException as e:
        raise e
    except Exception as e:
        raise SlitherException("failed to parse compact json node", raw['nodeType'], e, raw.keys(), raw)


PARSERS = {
    'Block': parse_block,
    'VariableDeclarationStatement': parse_variable_declaration_statement,
    'VariableDeclaration': parse_variable_declaration,
    'Literal': parse_literal,
    'IfStatement': parse_if_statement,
    'BinaryOperation': parse_binary_operation,
    'Identifier': parse_identifier,
    'ExpressionStatement': parse_expression_statement,
    'Assignment': parse_assignment,
    'ParameterList': parse_parameter_list,
    'TryStatement': parse_try_statement,
    'TryCatchClause': parse_try_catch_clause,
    'FunctionCall': parse_function_call,
    'MemberAccess': parse_member_access,
    'WhileStatement': parse_while_statement,
    'DoWhileStatement': parse_do_while_statement,
    'UnaryOperation': parse_unary_operation,
    'ForStatement': parse_for_statement,
    'ElementaryTypeName': parse_elementary_type_name,
    'TupleExpression': parse_tuple_expression,
    'Return': parse_return,
    'Continue': parse_continue,
    'Break': parse_break,
    'EmitStatement': parse_emit_statement,
    'Throw': parse_throw,
    'SourceUnit': parse_source_unit,
    'ContractDefinition': parse_contract_definition,
    'FunctionDefinition': parse_function_definition,
    'EventDefinition': parse_event_definition,
}
