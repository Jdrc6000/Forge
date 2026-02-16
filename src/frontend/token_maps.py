from src.frontend.token_types import TokenType

KEYWORDS = {
    "if": TokenType.IF,
    "else": TokenType.ELSE,
    "print": TokenType.PRINT,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "fn": TokenType.FN,
    "while": TokenType.WHILE,
    "for": TokenType.FOR,
    "in": TokenType.IN,
    "return": TokenType.RETURN,
}

SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "*": TokenType.MUL,
    "/": TokenType.DIV,
    "^": TokenType.POW,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "=": TokenType.EQ,
    "!": TokenType.BANG,
    "<": TokenType.LESS,
    ">": TokenType.GREATER,
    ",": TokenType.COMMA,
    ":": TokenType.COLON,
    ".": TokenType.DOT,
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