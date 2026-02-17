from dataclasses import dataclass
from typing import List, Optional, Any, Union

class AST():
    inferred_type = None

@dataclass
class Module():
    body: List[AST]

@dataclass
class Call(AST):
    func: AST
    args: List[AST]

@dataclass
class Assign(AST):
    target: AST
    value: AST

@dataclass
class Expr(AST):
    value: AST

@dataclass
class Name(AST):
    id: str

@dataclass
class Constant(AST):
    value: Any

@dataclass
class BinOp(AST):
    left: AST
    op: str
    right: AST

@dataclass
class UnOp(AST):
    op: str
    operand: AST

@dataclass
class If(AST):
    test: AST
    body: Block
    orelse: Optional[Union[Block, "If"]] = None

@dataclass
class Compare(AST):
    left: AST
    ops: list[str]
    comparators: List[AST]

@dataclass
class FunctionDef(AST):
    name: str
    args: list[str]
    body: list[AST]

@dataclass
class Return(AST):
    value: Optional[AST] = None

@dataclass
class While(AST):
    test: AST
    body: list[AST]

@dataclass
class For(AST):
    target: Name
    start: AST
    end: AST
    body: list[AST]

@dataclass
class Block(AST):
    statements: List[AST]