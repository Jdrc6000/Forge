from bootstrap.frontend.token_types import TokenType

KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "break": TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "struct": TokenType.STRUCT,
    
    "fn": TokenType.FN,
    "return": TokenType.RETURN,
}

SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MUL,
    "/": TokenType.DIV,
    "^": TokenType.POW,
    
    "=": TokenType.EQ,
    "!": TokenType.BANG,
    "<": TokenType.LESS,
    ">": TokenType.GREATER,
    
    ",": TokenType.COMMA,
    ":": TokenType.COLON,
    ".": TokenType.DOT,
    
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
}

COMPARISIONS = {
    "EE": "EQ",
    "NE": "NE",
    "LESS": "LT",
    "GREATER": "GT",
    "LE": "LE",
    "GE": "GE"
}

BINOPS = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "^": "POW"
}

CMP_OP_TO_IR = {
    "==": "EQ",
    "!=": "NE",
    "<" : "LT",
    ">" : "GT",
    "<=": "LE",
    ">=": "GE"
}

CMP_TOK_TO_STR = {
    TokenType.EE: "==",
    TokenType.NE: "!=",
    TokenType.LESS: "<",
    TokenType.GREATER: ">",
    TokenType.LE: "<=",
    TokenType.GE: ">=",
}