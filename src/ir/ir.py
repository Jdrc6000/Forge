from dataclasses import dataclass
from typing import Any, List

@dataclass()
class Instr:
    op: str
    a: Any = None
    b: Any = None
    c: Any = None

class IR:
    def __init__(self):
        self.code: List[Instr] = []
        self.reg = 0
    
    def new_reg(self):
        r = self.reg
        self.reg += 1
        return r
    
    def emit(self, op, a=None, b=None, c=None):
        self.code.append(Instr(op, a, b, c))
    
    # ast-dump had a child!!
    def dump(self):
        for i, instr in enumerate(self.code):
            print(f"{i} {instr.op} {instr.a} {instr.b} {instr.c}") #:04 to pad to 4 0's