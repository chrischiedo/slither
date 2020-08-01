from typing import Callable

from slither.solc_parsing.exceptions import ParsingError
from slither.solc_parsing.types.types import *

"""
The compact AST format was introduced in Solidity 0.4.12. In general, each node contains the following properties:

id (int): internal node id
nodeType (string): type of node
src (string): src offset

A node may also contain common properties depending on its type. All expressions, declarations, and calls share
similar properties, which are extracted below
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
        'canonical_name': raw.get('canonicalName', ''),
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


def parse_source_unit(raw: Dict) -> SourceUnit:
    nodes_parsed: List[ASTNode] = []

    for node in raw['nodes']:
        nodes_parsed.append(parse(node))

    return SourceUnit(nodes_parsed, **_extract_base_props(raw))


def parse_pragma_directive(raw: Dict) -> PragmaDirective:
    return PragmaDirective(raw['literals'], **_extract_base_props(raw))


def parse_import_directive(raw: Dict) -> ImportDirective:
    return ImportDirective(raw['absolutePath'], **_extract_base_props(raw))


def parse_contract_definition(raw: Dict) -> ContractDefinition:
    nodes_parsed: List[ASTNode] = []
    for child in raw['nodes']:
        nodes_parsed.append(parse(child))

    return ContractDefinition(raw['contractKind'], raw['linearizedBaseContracts'], nodes_parsed,
                              **_extract_decl_props(raw))


def parse_inheritance_specifier(raw: Dict) -> InheritanceSpecifier:
    basename_parsed = parse(raw['baseName'])
    assert isinstance(basename_parsed, UserDefinedTypeName)

    if raw['arguments']:
        args_parsed = []
        for child in raw['arguments']:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)
            args_parsed.append(child_parsed)
    else:
        args_parsed = None

    return InheritanceSpecifier(basename_parsed, args_parsed, **_extract_base_props(raw))


def parse_using_for_directive(raw: Dict) -> UsingForDirective:
    library_name_parsed = parse(raw['libraryName'])
    assert isinstance(library_name_parsed, UserDefinedTypeName)

    typename_parsed = parse(raw['typeName'])
    assert isinstance(typename_parsed, TypeName)

    return UsingForDirective(library_name_parsed, typename_parsed, **_extract_base_props(raw))


def parse_struct_definition(raw: Dict) -> StructDefinition:
    members_parsed: List[VariableDeclaration] = []
    for child in raw['members']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)

    return StructDefinition(members_parsed, **_extract_decl_props(raw))


def parse_enum_definition(raw: Dict) -> EnumDefinition:
    members_parsed: List[EnumValue] = []
    for child in raw['members']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, EnumValue)

    return EnumDefinition(members_parsed, **_extract_decl_props(raw))


def parse_enum_value(raw: Dict) -> EnumValue:
    return EnumValue(**_extract_decl_props(raw))


def parse_parameter_list(raw: Dict) -> ParameterList:
    """
    parameters (VariableDeclaration[])
    """

    parameters_parsed = []
    for child in raw['parameters']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        parameters_parsed.append(child_parsed)

    return ParameterList(parameters_parsed, **_extract_base_props(raw))


def parse_function_definition(raw: Dict) -> FunctionDefinition:
    body_parsed = parse(raw['body'])
    assert isinstance(body_parsed, Block)

    modifiers_parsed = []
    for child in raw['modifiers']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, ModifierInvocation)
        modifiers_parsed.append(child_parsed)

    return FunctionDefinition(raw['stateMutability'], raw['kind'], modifiers_parsed, body_parsed,
                              **_extract_call_props(raw))


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
    assert isinstance(type_parsed, TypeName)

    if raw['value']:
        value_parsed = parse(raw['value'])
        assert isinstance(value_parsed, Expression)
    else:
        value_parsed = None

    return VariableDeclaration(type_parsed, value_parsed, raw['typeDescriptions']['typeString'], raw['constant'],
                               **_extract_decl_props(raw))


def parse_modifier_definition(raw: Dict) -> ModifierDefinition:
    body_parsed = parse(raw['body'])
    assert isinstance(body_parsed, Block)

    return ModifierDefinition(body_parsed, **_extract_call_props(raw))


def parse_modifier_invocation(raw: Dict) -> ModifierInvocation:
    if raw['arguments']:
        arguments_parsed: Optional[List[Expression]] = []
        for child in raw['arguments']:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)
            arguments_parsed.append(child_parsed)
    else:
        arguments_parsed = None

    name_parsed = parse(raw['modifierName'])
    assert isinstance(name_parsed, Identifier)

    return ModifierInvocation(name_parsed, arguments_parsed, **_extract_base_props(raw))


def parse_event_definition(raw: Dict) -> EventDefinition:
    return EventDefinition(raw['anonymous'], **_extract_call_props(raw))


def parse_elementary_type_name(raw: Dict) -> ElementaryTypeName:
    """
    name (string)
    """

    name = raw['name']

    mutability = None
    if 'stateMutability' in raw:
        mutability = raw['stateMutability']

    return ElementaryTypeName(name, mutability, **_extract_base_props(raw))


def parse_user_defined_type_name(raw: Dict) -> UserDefinedTypeName:
    return UserDefinedTypeName(raw['name'], **_extract_base_props(raw))


def parse_function_type_name(raw: Dict) -> FunctionTypeName:
    params = parse(raw['parameterTypes'])
    assert isinstance(params, ParameterList)

    rets = parse(raw['returnParameterTypes'])
    assert isinstance(rets, ParameterList)

    return FunctionTypeName(params, rets, raw['stateMutability'], raw['visibility'], **_extract_base_props(raw))


def parse_mapping(raw: Dict) -> Mapping:
    key_parsed = parse(raw['keyType'])
    assert isinstance(key_parsed, TypeName)

    val_parsed = parse(raw['valueType'])
    assert isinstance(val_parsed, TypeName)

    return Mapping(key_parsed, val_parsed, **_extract_base_props(raw))


def parse_array_type_name(raw: Dict) -> ArrayTypeName:
    base_parsed = parse(raw['baseType'])
    assert isinstance(base_parsed, TypeName)

    if raw['length']:
        len_parsed = parse(raw['length'])
        assert isinstance(len_parsed, Expression)
    else:
        len_parsed = None

    return ArrayTypeName(base_parsed, len_parsed, **_extract_base_props(raw))


def parse_inline_assembly(raw: Dict) -> InlineAssembly:
    return InlineAssembly(raw['AST'], **_extract_base_props(raw))


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


def parse_placeholder_statement(raw: Dict) -> PlaceholderStatement:
    return PlaceholderStatement(**_extract_base_props(raw))


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


def parse_try_catch_clause(raw: Dict) -> TryCatchClause:
    """
    errorName (string)
    parameters (ParameterList?)
    block (Block)
    """

    error_name = raw['errorName']
    if raw['parameters']:
        parameters_parsed = parse(raw['parameters'])
        assert isinstance(parameters_parsed, ParameterList)
    else:
        parameters_parsed = None
    block_parsed = parse(raw['block'])
    assert isinstance(block_parsed, Block)

    return TryCatchClause(error_name, parameters_parsed, block_parsed, **_extract_base_props(raw))


def parse_try_statement(raw: Dict) -> TryStatement:
    """
    externalCall (Expression)
    clauses (TryCatchClause[])
    """

    external_call_parsed = parse(raw['externalCall'])
    assert isinstance(external_call_parsed, Expression)

    clauses_parsed = []
    for child in raw['clauses']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, TryCatchClause)
        clauses_parsed.append(child_parsed)

    return TryStatement(external_call_parsed, clauses_parsed, **_extract_base_props(raw))


def parse_while_statement_internal(raw: Dict, is_do_while: bool) -> WhileStatement:
    """
    condition (Expression)
    body (Statement)
    """

    condition_parsed = parse(raw['condition'])
    assert isinstance(condition_parsed, Expression)

    body_parsed = parse(raw['body'])
    assert isinstance(body_parsed, Statement)

    return WhileStatement(condition_parsed, body_parsed, is_do_while, **_extract_base_props(raw))


def parse_while_statement(raw: Dict) -> WhileStatement:
    return parse_while_statement_internal(raw, False)


def parse_do_while_statement(raw: Dict) -> WhileStatement:
    return parse_while_statement_internal(raw, True)


def parse_for_statement(raw: Dict) -> ForStatement:
    """
    initializationExpression (Statement)
    condition (Expression)
    loopExpression (ExpressionStatement)
    body (Statement)
    """

    init_parsed = parse(raw['initializationExpression'])
    assert isinstance(init_parsed, Statement)

    cond_parsed = parse(raw['condition'])
    assert isinstance(cond_parsed, Expression)

    loop_parsed = parse(raw['loopExpression'])
    assert isinstance(loop_parsed, ExpressionStatement)

    body_parsed = parse(raw['body'])
    assert isinstance(body_parsed, Statement)

    return ForStatement(init_parsed, cond_parsed, loop_parsed, body_parsed, **_extract_base_props(raw))


def parse_continue(raw: Dict) -> Continue:
    return Continue(**_extract_base_props(raw))


def parse_break(raw: Dict) -> Break:
    return Break(**_extract_base_props(raw))


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


def parse_throw(raw: Dict) -> Throw:
    return Throw(**_extract_base_props(raw))


def parse_emit_statement(raw: Dict) -> EmitStatement:
    """
    eventCall (FunctionCall)
    """
    call_parsed = parse(raw['eventCall'])
    assert isinstance(call_parsed, FunctionCall)

    return EmitStatement(call_parsed, **_extract_base_props(raw))


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


def parse_expression_statement(raw: Dict) -> ExpressionStatement:
    """
    expression (Statement)
    """

    expression_parsed = parse(raw['expression'])

    assert isinstance(expression_parsed, Expression)

    return ExpressionStatement(expression_parsed, **_extract_base_props(raw))


def parse_conditional(raw: Dict) -> Conditional:
    true_expr_parsed = parse(raw['trueExpression'])
    assert isinstance(true_expr_parsed, Expression)

    false_expr_parsed = parse(raw['falseExpression'])
    assert isinstance(false_expr_parsed, Expression)

    cond_parsed = parse(raw['condition'])
    assert isinstance(cond_parsed, Expression)

    return Conditional(cond_parsed, true_expr_parsed, false_expr_parsed, **_extract_expr_props(raw))


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


def parse_unary_operation(raw: Dict) -> UnaryOperation:
    """
    prefix (bool)
    operator (string)
    subExpression (Expression)
    """

    expression_parsed = parse(raw['subExpression'])
    assert isinstance(expression_parsed, Expression)

    return UnaryOperation(raw['operator'], expression_parsed, raw['prefix'], **_extract_expr_props(raw))


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
    assert isinstance(expression_parsed, Expression)

    names = raw['names']
    arguments_parsed = []
    for child in raw['arguments']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        arguments_parsed.append(child_parsed)

    return FunctionCall(raw['kind'], expression_parsed, names, arguments_parsed, **_extract_expr_props(raw))


def parse_function_call_options(raw: Dict) -> FunctionCallOptions:
    expression_parsed = parse(raw['expression'])
    assert isinstance(expression_parsed, Expression)

    names = raw['names']
    assert isinstance(names, list)
    for name in names:
        assert isinstance(name, str)

    options_parsed: List[Expression] = []
    for child in raw['options']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        options_parsed.append(child_parsed)

    return FunctionCallOptions(expression_parsed, names, options_parsed, **_extract_expr_props(raw))


def parse_new_expression(raw: Dict) -> NewExpression:
    typename_parsed = parse(raw['typeName'])
    assert isinstance(typename_parsed, TypeName)

    return NewExpression(typename_parsed, **_extract_expr_props(raw))


def parse_member_access(raw: Dict) -> MemberAccess:
    """
    memberName (string)
    expression (Expression)
    """

    expression_parsed = parse(raw['expression'])
    assert isinstance(expression_parsed, Expression)

    member_name = raw['memberName']

    return MemberAccess(expression_parsed, member_name, **_extract_expr_props(raw))


def parse_index_access(raw: Dict) -> IndexAccess:
    base_parsed = parse(raw['baseExpression'])
    assert isinstance(base_parsed, Expression)

    if raw['indexExpression']:
        index_parsed = parse(raw['indexExpression'])
        assert isinstance(index_parsed, Expression)
    else:
        index_parsed = None

    return IndexAccess(base_parsed, index_parsed, **_extract_expr_props(raw))


def parse_index_range_access(raw: Dict) -> IndexRangeAccess:
    base_parsed = parse(raw['baseExpression'])
    assert isinstance(base_parsed, Expression)

    start_parsed = parse(raw['startExpression'])
    assert isinstance(start_parsed, Expression)

    if raw['endExpression']:
        end_parsed = parse(raw['endExpression'])
        assert isinstance(end_parsed, Expression)
    else:
        end_parsed = None

    return IndexRangeAccess(base_parsed, start_parsed, end_parsed, **_extract_expr_props(raw))


def parse_identifier(raw: Dict) -> Identifier:
    """
    name (string)
    """

    name = raw['name']

    assert isinstance(name, str)

    return Identifier(name, **_extract_expr_props(raw))


def parse_elementary_type_name_expression(raw: Dict) -> ElementaryTypeNameExpression:
    typename_parsed = parse(raw['typeName'])
    assert isinstance(typename_parsed, ElementaryTypeName)

    return ElementaryTypeNameExpression(typename_parsed, **_extract_expr_props(raw))


def parse_literal(raw: Dict) -> Literal:
    """
    kind (string)
    value (string)
    hexValue (string)
    subdenomination (string?)

    +ExpressionAnnotation
    """

    return Literal(raw['kind'], raw['value'], raw['hexValue'], raw['subdenomination'], **_extract_expr_props(raw))


def parse_unsupported(raw: Dict) -> ASTNode:
    raise ParsingError("unsupported compact json node", raw['nodeType'], raw.keys(), raw)


def parse(raw: Dict) -> ASTNode:
    try:
        return PARSERS.get(raw['nodeType'], parse_unsupported)(raw)
    except ParsingError as e:
        raise e
    except Exception as e:
        raise ParsingError("failed to parse compact json node", raw['nodeType'], e, raw.keys(), raw)


PARSERS: Dict[str, Callable[[Dict], ASTNode]] = {
    'SourceUnit': parse_source_unit,
    'PragmaDirective': parse_pragma_directive,
    'ImportDirective': parse_import_directive,
    'ContractDefinition': parse_contract_definition,
    'InheritanceSpecifier': parse_inheritance_specifier,
    'UsingForDirective': parse_using_for_directive,
    'StructDefinition': parse_struct_definition,
    'EnumDefinition': parse_enum_definition,
    'EnumValue': parse_enum_value,
    'ParameterList': parse_parameter_list,
    'FunctionDefinition': parse_function_definition,
    'VariableDeclaration': parse_variable_declaration,
    'ModifierDefinition': parse_modifier_definition,
    'ModifierInvocation': parse_modifier_invocation,
    'EventDefinition': parse_event_definition,
    'ElementaryTypeName': parse_elementary_type_name,
    'UserDefinedTypeName': parse_user_defined_type_name,
    'FunctionTypeName': parse_function_type_name,
    'Mapping': parse_mapping,
    'ArrayTypeName': parse_array_type_name,
    'InlineAssembly': parse_inline_assembly,
    'Block': parse_block,
    'PlaceholderStatement': parse_placeholder_statement,
    'IfStatement': parse_if_statement,
    'TryCatchClause': parse_try_catch_clause,
    'TryStatement': parse_try_statement,
    'WhileStatement': parse_while_statement,
    'DoWhileStatement': parse_do_while_statement,
    'ForStatement': parse_for_statement,
    'Continue': parse_continue,
    'Break': parse_break,
    'Return': parse_return,
    'Throw': parse_throw,
    'EmitStatement': parse_emit_statement,
    'VariableDeclarationStatement': parse_variable_declaration_statement,
    'ExpressionStatement': parse_expression_statement,
    'Conditional': parse_conditional,
    'Assignment': parse_assignment,
    'TupleExpression': parse_tuple_expression,
    'UnaryOperation': parse_unary_operation,
    'BinaryOperation': parse_binary_operation,
    'FunctionCall': parse_function_call,
    'FunctionCallOptions': parse_function_call_options,
    'NewExpression': parse_new_expression,
    'MemberAccess': parse_member_access,
    'IndexAccess': parse_index_access,
    'IndexRangeAccess': parse_index_range_access,
    'Identifier': parse_identifier,
    'ElementaryTypeNameExpression': parse_elementary_type_name_expression,
    'Literal': parse_literal,
}
