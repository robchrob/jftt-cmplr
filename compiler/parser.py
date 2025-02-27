import ply.yacc as yacc
from .lexer import tokens

# AST node classes


class Node:
    pass


class Program(Node):
    def __init__(self, const_decls, var_decls, commands):
        self.const_decls = const_decls
        self.var_decls = var_decls
        self.commands = commands


class ConstDecl(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value


class VarDecl(Node):
    def __init__(self, name):
        self.name = name


class Assignment(Node):
    def __init__(self, name, expr):
        self.name = name
        self.expr = expr


class IfElse(Node):
    def __init__(self, condition, then_cmds, else_cmds):
        self.condition = condition
        self.then_cmds = then_cmds
        self.else_cmds = else_cmds


class While(Node):
    def __init__(self, condition, commands):
        self.condition = condition
        self.commands = commands


class Read(Node):
    def __init__(self, name):
        self.name = name


class Write(Node):
    def __init__(self, name):
        self.name = name


class Number(Node):
    def __init__(self, value):
        self.value = value


class Identifier(Node):
    def __init__(self, name):
        self.name = name


class BinOp(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class Condition(Node):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

# Grammar rules


def p_program(p):
    'program : CONST cdeclarations VAR vdeclarations BEGIN commands END'
    p[0] = Program(p[2], p[4], p[6])


def p_cdeclarations_empty(p):
    'cdeclarations : '
    p[0] = []


def p_cdeclarations(p):
    'cdeclarations : cdeclarations IDENTIFIER ASSIGN NUMBER'
    p[0] = p[1] + [ConstDecl(p[2], p[4])]


def p_vdeclarations_empty(p):
    'vdeclarations : '
    p[0] = []


def p_vdeclarations(p):
    'vdeclarations : vdeclarations IDENTIFIER'
    p[0] = p[1] + [VarDecl(p[2])]


def p_commands_multiple(p):
    'commands : commands command'
    p[0] = p[1] + [p[2]]


def p_commands_single(p):
    'commands : command'
    p[0] = [p[1]]


def p_command_assignment(p):
    'command : IDENTIFIER ASSIGN expression SEMICOLON'
    p[0] = Assignment(p[1], p[3])


def p_command_if(p):
    'command : IF condition THEN commands ELSE commands END'
    p[0] = IfElse(p[2], p[4], p[6])


def p_command_while(p):
    'command : WHILE condition DO commands END'
    p[0] = While(p[2], p[4])


def p_command_read(p):
    'command : READ IDENTIFIER SEMICOLON'
    p[0] = Read(p[2])


def p_command_write(p):
    'command : WRITE IDENTIFIER SEMICOLON'
    p[0] = Write(p[2])


def p_expression_number(p):
    'expression : NUMBER'
    p[0] = Number(p[1])


def p_expression_identifier(p):
    'expression : IDENTIFIER'
    p[0] = Identifier(p[1])


def p_expression_plus(p):
    'expression : IDENTIFIER PLUS IDENTIFIER'
    p[0] = BinOp(Identifier(p[1]), '+', Identifier(p[3]))


def p_expression_minus(p):
    'expression : IDENTIFIER MINUS IDENTIFIER'
    p[0] = BinOp(Identifier(p[1]), '-', Identifier(p[3]))


def p_expression_times(p):
    'expression : IDENTIFIER TIMES IDENTIFIER'
    p[0] = BinOp(Identifier(p[1]), '*', Identifier(p[3]))


def p_expression_divide(p):
    'expression : IDENTIFIER DIVIDE IDENTIFIER'
    p[0] = BinOp(Identifier(p[1]), '/', Identifier(p[3]))


def p_expression_modulo(p):
    'expression : IDENTIFIER MODULO IDENTIFIER'
    p[0] = BinOp(Identifier(p[1]), '%', Identifier(p[3]))


def p_condition(p):
    '''condition : IDENTIFIER EQUAL IDENTIFIER
                 | IDENTIFIER NOTEQUAL IDENTIFIER
                 | IDENTIFIER LESS IDENTIFIER
                 | IDENTIFIER GREATER IDENTIFIER
                 | IDENTIFIER LESSEQUAL IDENTIFIER
                 | IDENTIFIER GREATEREQUAL IDENTIFIER'''
    p[0] = Condition(Identifier(p[1]), p[2], Identifier(p[3]))

# Error rule


def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}' (line {p.lineno})")
    else:
        print("Syntax error at EOF")


# Build the parser
parser = yacc.yacc()


def parse(data, lexer=None):
    return parser.parse(data, lexer=lexer)
