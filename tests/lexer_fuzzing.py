import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lexer import *
import random

chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/^=<>!:\" \t\n"

for _ in range(20_000):
    program = "".join(random.choice(chars) for _ in range(random.randint(1, 50)))
    try:
        lexer = Lexer(program)
        tokens = lexer.get_tokens()
    except Exception as e:
        print("Lexer crash:", program, e)