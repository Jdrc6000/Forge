tt_int = "INT"
tt_float = "FLOAT"
tt_string = "STRING"
tt_name = "NAME"
tt_plus = "PLUS"
tt_minus = "MINUS"
tt_mul = "MUL"
tt_div = "DIV"
tt_pow = "POW"
tt_lparen = "LPAREN"
tt_rparen = "RPAREN"
tt_eq = "EQ"
tt_bang = "BANG"
tt_less = "LESS"
tt_greater = "GREATER"
tt_ne = "NE"
tt_ee = "EE"
tt_le = "LE"
tt_ge = "GE"
tt_comma = "COMMA"
tt_colon = "COLON"
tt_newline = "NEWLINE"
tt_indent = "INDENT"
tt_dedent = "DEDENT"
tt_eof = "EOF"
tt_if = "IF"
tt_else = "ELSE"
tt_print = "PRINT"
tt_and = "AND"
tt_or = "OR"
tt_not = "NOT"

keywords = {
    "if": tt_if,
    "else": tt_else,
    "print": tt_print,
    "and": tt_and,
    "or": tt_or,
    "not": tt_not
}

single_char_tokens = {
    "+": tt_plus,
    "-": tt_minus,
    "*": tt_mul,
    "/": tt_div,
    "^": tt_pow,
    "(": tt_lparen,
    ")": tt_rparen,
    "=": tt_eq,
    "!": tt_bang,
    "<": tt_less,
    ">": tt_greater,
    ",": tt_comma,
    ":": tt_colon
}

binops = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "^": "POW"
}

cmp = {
    "EE": "EQ",
    "NE": "NE",
    "LESS": "LT",
    "GREATER": "GT",
    "LE": "LE",
    "GE": "GE"
}

class Token():
    def __init__(self, _type, value=None):
        self.type = _type
        self.value = value
        
    def __repr__(self):
        if self.value is not None:
            return f"{self.type}:{self.value}"
        return self.type