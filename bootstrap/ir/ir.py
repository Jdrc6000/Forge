from bootstrap.ir.operands import Reg, Imm
from dataclasses import dataclass
from typing import Any, List

@dataclass
class Instr:
    op: str
    a: Reg | Imm | None = None
    b: Reg | Imm | None = None
    c: Reg | Imm | None = None

class IR:
    def __init__(self):
        self.code: List[Instr] = []
        self.reg = 0
    
    def new_reg(self):
        r = Reg(self.reg)
        self.reg += 1
        return r
    
    def emit(self, op, a=None, b=None, c=None):
        self.code.append(Instr(op, a, b, c))
    
    # ast-dump had a child!!
    def dump(self):
        def fmt(x):
            if isinstance(x, Reg):
                return f"r{x.id}"
            if isinstance(x, Imm):
                return x.value
            return x
        
        for i, instr in enumerate(self.code):
            print(f"{i} {instr.op} {fmt(instr.a)} {fmt(instr.b)} {fmt(instr.c)}") #:04 to pad to 4 0's