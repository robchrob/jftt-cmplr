import ply.lex as lex

# List of token names
tokens = [
    'IDENTIFIER', 'NUMBER',
    'ASSIGN', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'MODULO',
    'EQUAL', 'NOTEQUAL', 'LESS', 'GREATER', 'LESSEQUAL', 'GREATEREQUAL',
    'SEMICOLON'
]

# Reserved keywords (case-insensitive)
reserved = {
    'const': 'CONST',
    'var': 'VAR',
    'begin': 'BEGIN',
    'end': 'END',
    'if': 'IF',
    'then': 'THEN',
    'else': 'ELSE',
    'while': 'WHILE',
    'do': 'DO',
    'read': 'READ',
    'write': 'WRITE'
}

tokens += list(reserved.values())

# Token regex rules
t_ASSIGN = r':='
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_MODULO = r'%'
t_EQUAL = r'=='
t_NOTEQUAL = r'!='
t_LESS = r'<'
t_GREATER = r'>'
t_LESSEQUAL = r'<='
t_GREATEREQUAL = r'>='
t_SEMICOLON = r';'

t_ignore = ' \t'


def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value.lower(), 'IDENTIFIER')
    return t


def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


def t_COMMENT(t):
    r'\(\*.*?\*\)'
    pass


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)


def t_error(t):
    print(f"Illegal character '{t.value[0]}' at line {t.lineno}, position {t.lexpos}")
    t.lexer.skip(1)


# Build the lexer
lexer = lex.lex()
