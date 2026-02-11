import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import *
from parser import *
import random

tokens = [tt_int, tt_plus, tt_name, tt_lparen, tt_rparen, tt_colon, tt_if, tt_else]
for _ in range(500):
    program = " ".join(random.choice(tokens) for _ in range(random.randint(3, 15)))
    try:
        lexer = Lexer(program)
        tree = Parser(lexer.get_tokens()).parse()
    except Exception as e:
        print("Parser crash:", program, e)