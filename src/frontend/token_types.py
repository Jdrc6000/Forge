from enum import Enum, auto

class TokenType(Enum):
    INT = auto()
    FLOAT = auto()
    STRING = auto()
    NAME = auto()
    
    PLUS = auto()
    MINUS = auto()
    MUL = auto()
    DIV = auto()
    POW = auto()
    
    EQ = auto()
    BANG = auto()
    
    LESS = auto()
    GREATER = auto()
    NE = auto()
    EE = auto()
    LE = auto()
    GE = auto()
    
    COMMA = auto()
    COLON = auto()
    DOT = auto()
    
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    IN = auto()
    RANGE = auto()
    
    AND = auto()
    OR = auto()
    NOT = auto()
    TRUE = auto()
    FALSE = auto()
    
    FN = auto()
    RETURN = auto()
    
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    
    ILLEGAL = auto()
    EOF = auto()
    
    PRINT = auto()
    PRINTLN = auto()