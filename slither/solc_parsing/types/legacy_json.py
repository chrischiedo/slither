from typing import Callable

from slither.solc_parsing.exceptions import ParsingError
from slither.solc_parsing.types.types import *

"""
The legacy AST format is used by all versions of Solidity that Slither currently supports (i.e. >=0.4.0), but it must
be manually enabled for versions >=0.4.12. In general, all nodes contain the following properties:

id (int): internal node id, randomly generated
name (string): type of node
src (string): src offset

A node may also contain an array of children. This array is simply the concatenation of every child node and does
not contain nulls if a child node is unset. As a result, this results in ambiguities when parsing constructs like
a for loop.

A node may, for Solidity >=0.4.12, contain an optional attributes dictionary, which contains additonal
properties about the node
"""


def _extract_base_props(raw: Dict) -> Dict:
    if raw['name'] == 'SourceUnit':
        return {
            'src': '',
            'id': -1,
        }

    return {
        'src': raw['src'],
        'id': raw['id'],
    }


def _extract_decl_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        'name': raw['attributes']['name'],
        'canonical_name': raw.get('canonicalName', ''),
        'visibility': raw['attributes'].get('visibility', 'public'),
    }


def _extract_expr_props(raw: Dict) -> Dict:
    return {
        **_extract_base_props(raw),
        'type_str': raw['attributes']['type'],
        'constant': raw.get("isConstant", False),  # Identifier doesn't expose this
        'pure': raw.get('isPure', False),  # Identifier doesn't expose this
    }


def parse_variable_definition_statement(raw: Dict) -> VariableDeclarationStatement:
    """
    children:
        VariableDeclaration[]
        Expression?
    """

    parsed_children: List[VariableDeclaration] = []
    for child in raw['children'][:-1]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        parsed_children.append(child_parsed)

    initial_value = None
    last_child = parse(raw['children'][-1])
    if isinstance(last_child, VariableDeclaration):
        parsed_children.append(last_child)
    else:
        initial_value = last_child

    return VariableDeclarationStatement(parsed_children, initial_value, **_extract_base_props(raw))


def parse_expression_statement(raw: Dict) -> ExpressionStatement:
    """
    children:
        Expression
    """

    expression_parsed = parse(raw['children'][0])
    assert isinstance(expression_parsed, Expression)

    return ExpressionStatement(expression_parsed, **_extract_base_props(raw))


def parse_conditional(raw: Dict) -> Conditional:
    true_expr_parsed = parse(raw['children'][0])
    assert isinstance(true_expr_parsed, Expression)

    false_expr_parsed = parse(raw['children'][1])
    assert isinstance(false_expr_parsed, Expression)

    cond_parsed = parse(raw['children'][2])
    assert isinstance(cond_parsed, Expression)

    return Conditional(cond_parsed, true_expr_parsed, false_expr_parsed, **_extract_expr_props(raw))


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

    return Assignment(left, raw['attributes']['operator'], right, **_extract_expr_props(raw))


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

    return TupleExpression(children_parsed, False, **_extract_expr_props(raw))


def parse_binary_operation(raw: Dict) -> BinaryOperation:
    left_parsed = parse(raw['children'][0])
    right_parsed = parse(raw['children'][1])

    assert isinstance(left_parsed, Expression)
    assert isinstance(right_parsed, Expression)

    return BinaryOperation(left_parsed, raw['attributes']['operator'], right_parsed, **_extract_expr_props(raw))


def parse_function_call(raw: Dict) -> FunctionCall:
    attrs = raw['attributes']

    if 'isStructConstructorCall' in attrs:
        # >= 0.4.12
        if attrs['isStructConstructorCall']:
            kind = 'structConstructorCall'
        else:
            kind = 'typeConversion' if attrs['type_conversion'] else 'functionCall'
    else:
        # >= 0.4.0
        if attrs['type_conversion']:
            kind = 'typeConversion'
        elif attrs['type'].startswith("struct "):
            kind = 'structConstructorCall'
        else:
            kind = 'functionCall'

    if 'names' in attrs:
        names = attrs['names']
    else:
        names = []

    call_parsed = parse(raw['children'][0])
    assert isinstance(call_parsed, Expression)

    args_parsed: List[Expression] = []
    for child in raw['children'][1:]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        args_parsed.append(child_parsed)

    return FunctionCall(kind, call_parsed, names, args_parsed, **_extract_expr_props(raw))


def parse_function_call_options(raw: Dict) -> FunctionCallOptions:
    expression_parsed = parse(raw['children'][0])
    assert isinstance(expression_parsed, Expression)

    names = raw['attributes']['names']
    assert isinstance(names, list)
    for name in names:
        assert isinstance(name, str)

    options_parsed: List[Expression] = []
    for child in raw['children'][1:]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        options_parsed.append(child_parsed)

    return FunctionCallOptions(expression_parsed, names, options_parsed, **_extract_expr_props(raw))


def parse_new_expression(raw: Dict) -> NewExpression:
    typename_parsed = parse(raw['children'][0])
    assert isinstance(typename_parsed, TypeName)

    return NewExpression(typename_parsed, **_extract_expr_props(raw))


def parse_member_access(raw: Dict) -> MemberAccess:
    expr_parsed = parse(raw['children'][0])
    assert isinstance(expr_parsed, Expression)

    return MemberAccess(expr_parsed, raw['attributes']['member_name'], **_extract_expr_props(raw))


def parse_throw(raw: Dict) -> Throw:
    return Throw(raw['src'])


def parse_source_unit(raw: Dict) -> SourceUnit:
    children_parsed: List[ASTNode] = []
    for child in raw['children']:
        children_parsed.append(parse(child))
    return SourceUnit(children_parsed, **_extract_base_props(raw))


def parse_pragma_directive(raw: Dict) -> PragmaDirective:
    return PragmaDirective(raw['attributes']['literals'], **_extract_base_props(raw))


def parse_contract_definition(raw: Dict) -> ContractDefinition:
    attrs = raw['attributes']

    if 'contractKind' in attrs:
        # >=0.4.12
        kind = attrs['contractKind']
    else:
        # <0.4.12
        if attrs['isLibrary']:
            kind = "library"
        elif attrs['fullyImplemented']:
            kind = "contract"
        else:
            kind = "interface"

    linearized = attrs['linearizedBaseContracts']
    nodes = []
    if 'children' in raw:
        nodes = [parse(child) for child in raw['children']]

    return ContractDefinition(kind, linearized, nodes, **_extract_decl_props(raw))


def parse_inheritance_specifier(raw: Dict) -> InheritanceSpecifier:
    basename_parsed = parse(raw['children'][0])
    assert isinstance(basename_parsed, UserDefinedTypeName)

    if len(raw['children']) > 1:
        args_parsed = []
        for child in raw['children'][1:]:
            child_parsed = parse(child)
            assert isinstance(child_parsed, Expression)
            args_parsed.append(child_parsed)
    else:
        args_parsed = None

    return InheritanceSpecifier(basename_parsed, args_parsed, **_extract_base_props(raw))


def parse_using_for_directive(raw: Dict) -> UsingForDirective:
    library = parse(raw['children'][0])
    assert isinstance(library, UserDefinedTypeName)

    typename = None
    if len(raw['children']) > 1:
        typename = parse(raw['children'][1])
        assert isinstance(typename, TypeName)

    return UsingForDirective(library, typename, **_extract_base_props(raw))


def parse_struct_definition(raw: Dict) -> StructDefinition:
    attrs = raw['attributes']

    if 'canonicalName' in attrs:
        # >=0.4.12
        canonical_name = attrs['canonicalName']
    else:
        canonical_name = None

    members_parsed: List[VariableDeclaration] = []
    for child in raw['children']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, VariableDeclaration)
        members_parsed.append(child_parsed)

    return StructDefinition(members_parsed, name=attrs['name'], canonical_name=canonical_name, visibility=None,
                            **_extract_base_props(raw))


def parse_enum_definition(raw: Dict) -> EnumDefinition:
    attrs = raw['attributes']

    if 'canonicalName' in attrs:
        # >=0.4.12
        canonical_name = attrs['canonicalName']
    else:
        canonical_name = None

    members_parsed: List[EnumValue] = []
    for child in raw['children']:
        child_parsed = parse(child)
        assert isinstance(child_parsed, EnumValue)
        members_parsed.append(child_parsed)

    return EnumDefinition(members_parsed, name=attrs['name'], canonical_name=canonical_name, visibility=None,
                          **_extract_base_props(raw))


def parse_enum_value(raw: Dict) -> EnumValue:
    return EnumValue(
        name=raw['attributes']['name'],
        canonical_name=None,
        visibility=None,
        **_extract_base_props(raw)
    )


def parse_function_definition(raw: Dict) -> FunctionDefinition:
    attrs = raw['attributes']
    if 'stateMutability' in attrs:
        # >=0.4.16
        mutability = attrs['stateMutability']
    elif 'payable' in attrs:
        # >=0.4.5
        mutability = "payable" if attrs['payable'] else "nonpayable"
    else:
        # >=0.4.0
        """
        as it turns out, constant functions can do non-constant things, so mark it as payable so err on the side
        of more detectors triggering
        """
        mutability = "payable"

    if 'kind' in attrs:
        # >= 0.5.0
        kind = attrs['kind']
    elif 'isConstructor' in attrs and attrs['isConstructor']:
        # >= 0.4.12
        kind = "constructor"
    else:
        # >= 0.4.0
        kind = 'fallback' if attrs['name'] == '' else 'function'

    assert len(raw['children']) >= 3

    params = parse(raw['children'][0])
    assert isinstance(params, ParameterList)

    rets = parse(raw['children'][1])
    assert isinstance(rets, ParameterList)

    modifiers_parsed: List[ModifierInvocation] = []
    for child in raw['children'][2:-1]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, ModifierInvocation)
        modifiers_parsed.append(child_parsed)

    body = parse(raw['children'][-1])
    assert isinstance(body, Block)

    return FunctionDefinition(mutability, kind, modifiers_parsed, body, params=params, rets=rets,
                              **_extract_decl_props(raw))


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

    return ParameterList(parameters_parsed, **_extract_base_props(raw))


def parse_elementary_type_name(raw: Dict) -> ElementaryTypeName:
    attrs = raw['attributes']
    if 'stateMutability' in attrs:
        # >=0.5.0
        mutability = attrs['stateMutability']
    else:
        # >=0.4.0
        mutability = "payable" if attrs['name'] == 'address' else None

    return ElementaryTypeName(attrs['name'], mutability, **_extract_base_props(raw))


def parse_user_defined_type_name(raw: Dict) -> UserDefinedTypeName:
    return UserDefinedTypeName(raw['attributes']['name'], **_extract_base_props(raw))


def parse_array_type_name(raw: Dict) -> ArrayTypeName:
    base_parsed = parse(raw['children'][0])
    assert isinstance(base_parsed, TypeName)

    len_parsed = None
    if len(raw['children']) > 1:
        len_parsed = parse(raw['children'][1])
        assert isinstance(len_parsed, Expression)

    return ArrayTypeName(base_parsed, len_parsed, **_extract_base_props(raw))


def parse_inline_assembly(raw: Dict) -> InlineAssembly:
    return InlineAssembly(raw['attributes']['operations'], **_extract_base_props(raw))


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

    return Block(parsed_statements, **_extract_base_props(raw))


def parse_placeholder_statement(raw: Dict) -> PlaceholderStatement:
    return PlaceholderStatement(**_extract_base_props(raw))


def parse_return(raw: Dict) -> Return:
    """
    children:
        Expression?
    """

    expr_parsed = None
    if len(raw['children']) > 0:
        expr_parsed = parse(raw['children'][0])
        assert isinstance(expr_parsed, Expression)

    return Return(expr_parsed, **_extract_base_props(raw))


def parse_variable_declaration(raw: Dict) -> VariableDeclaration:
    attrs = raw['attributes']
    if 'constant' in attrs:
        # >=0.4.11
        constant = attrs['constant']
    else:
        # >=0.4.0
        constant = False

    typename = parse(raw['children'][0])
    assert isinstance(typename, TypeName)

    value = None
    if len(raw['children']) > 1:
        value = parse(raw['children'][1])
        assert isinstance(value, Expression)

    return VariableDeclaration(
        typename, value, raw['attributes']['type'], constant, **_extract_decl_props(raw)
    )


def parse_modifier_definition(raw: Dict) -> ModifierDefinition:
    params = parse(raw['children'][0])
    assert isinstance(params, ParameterList)

    body = parse(raw['children'][1])
    assert isinstance(body, Block)

    return ModifierDefinition(
        body=body,
        params=params,
        rets=None,
        name=raw['attributes']['name'],
        canonical_name=None,
        visibility=None,
        **_extract_base_props(raw)
    )


def parse_modifier_invocation(raw: Dict) -> ModifierInvocation:
    name = parse(raw['children'][0])
    assert isinstance(name, Identifier)

    args_parsed: List[Expression] = []
    for child in raw['children'][1:]:
        child_parsed = parse(child)
        assert isinstance(child_parsed, Expression)
        args_parsed.append(child_parsed)

    return ModifierInvocation(
        modifier=name,
        args=args_parsed,
        **_extract_base_props(raw)
    )


def parse_index_access(raw: Dict) -> IndexAccess:
    base_parsed = parse(raw['children'][0])
    assert isinstance(base_parsed, Expression)

    index_parsed = None
    if len(raw['children']) > 1:
        index_parsed = parse(raw['children'][1])
        assert isinstance(index_parsed, Expression)

    return IndexAccess(base_parsed, index_parsed, **_extract_expr_props(raw))


def parse_index_range_access(raw: Dict) -> IndexRangeAccess:
    base = parse(raw['children'][0])
    assert isinstance(base, Expression)

    start = parse(raw['children'][1])
    assert isinstance(start, Expression)

    end = None
    if len(raw['children']) > 2:
        end = parse(raw['children'][2])
        assert isinstance(end, Expression)

    return IndexRangeAccess(base, start, end, **_extract_expr_props(raw))


def parse_identifier(raw: Dict) -> Identifier:
    """
    attributes:
        type (string)
        value (string)
    """

    return Identifier(raw['attributes']['value'], **_extract_expr_props(raw))


def parse_elementary_type_name_expression(raw: Dict) -> ElementaryTypeNameExpression:
    typename_parsed = parse(raw['children'][0])
    assert isinstance(typename_parsed, ElementaryTypeName)

    return ElementaryTypeNameExpression(typename_parsed, **_extract_expr_props(raw))


def parse_literal(raw: Dict) -> Literal:
    attrs = raw['attributes']
    return Literal(attrs['token'], attrs['value'], attrs['hexvalue'], attrs['subdenomination'],
                   **_extract_expr_props(raw))


def parse_unsupported(raw: Dict) -> ASTNode:
    raise ParsingError("unsupported legacy json node", raw['name'], raw.keys(),
                       [node['name'] for node in raw['children']] if 'children' in raw else [], raw)


def parse(raw: Dict) -> ASTNode:
    try:
        return PARSERS.get(raw['name'], parse_unsupported)(raw)
    except ParsingError as e:
        raise e
    except Exception as e:
        raise ParsingError("failed to parse legacy json node", raw['name'], e, raw.keys(), raw)


PARSERS: Dict[str, Callable[[Dict], ASTNode]] = {
    'SourceUnit': parse_source_unit,
    'PragmaDirective': parse_pragma_directive,
    # 'ImportDirective': parse_import_directive,
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
    # 'EventDefinition': parse_event_definition,
    'ElementaryTypeName': parse_elementary_type_name,
    'UserDefinedTypeName': parse_user_defined_type_name,
    # 'FunctionTypeName': parse_function_type_name,
    # 'Mapping': parse_mapping,
    'ArrayTypeName': parse_array_type_name,
    'InlineAssembly': parse_inline_assembly,
    'Block': parse_block,
    'PlaceholderStatement': parse_placeholder_statement,
    # 'IfStatement': parse_if_statement,
    # 'TryCatchClause': parse_try_catch_clause,
    # 'TryStatement': parse_try_statement,
    # 'WhileStatement': parse_while_statement,
    # 'DoWhileStatement': parse_do_while_statement,
    # 'ForStatement': parse_for_statement,
    # 'Continue': parse_continue,
    # 'Break': parse_break,
    'Return': parse_return,
    'Throw': parse_throw,
    # 'EmitStatement': parse_emit_statement,
    'VariableDeclarationStatement': parse_variable_definition_statement,  # >=0.4.7
    'VariableDefinitionStatement': parse_variable_definition_statement,  # <=0.4.6
    'ExpressionStatement': parse_expression_statement,
    'Conditional': parse_conditional,
    'Assignment': parse_assignment,
    'TupleExpression': parse_tuple_expression,
    # 'UnaryOperation': parse_unary_operation,
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
