from dataclasses import dataclass, field
from typing import List as TypingList, Optional, Any, Union, Tuple

@dataclass
class AST:
    inferred_type = None

@dataclass
class Module(AST):
    body: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class Block(AST):
    statements: TypingList[AST]
    line: int = 0
    column: int = 0
    
    def __iter__(self):
        return iter(self.statements)

@dataclass
class Call(AST):
    func: AST
    args: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class Assign(AST):
    target: AST
    value: AST
    line: int = 0
    column: int = 0

@dataclass
class Expr(AST):
    value: AST
    line: int = 0
    column: int = 0

@dataclass
class Name(AST):
    id: str
    line: int = 0
    column: int = 0

@dataclass
class Constant(AST):
    value: Any
    line: int = 0
    column: int = 0

@dataclass
class BinOp(AST):
    left: AST
    op: str
    right: AST
    line: int = 0
    column: int = 0

@dataclass
class UnOp(AST):
    op: str
    operand: AST
    line: int = 0
    column: int = 0

@dataclass
class If(AST):
    test: AST
    body: Block
    orelse: Optional[Union[Block, "If"]] = None
    line: int = 0
    column: int = 0

@dataclass
class Compare(AST):
    left: AST
    ops: TypingList[str]
    comparators: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class FunctionDef(AST):
    name: str
    args: TypingList[str]
    body: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class Return(AST):
    value: Optional[AST] = None
    line: int = 0
    column: int = 0

@dataclass
class While(AST):
    test: AST
    body: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class For(AST):
    target: Name
    start: AST
    end: AST
    body: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class List(AST):
    elements: TypingList[AST]
    line: int = 0
    column: int = 0

@dataclass
class Attribute(AST):
    obj: AST
    attr: str
    line: int = 0
    column: int = 0

@dataclass
class MethodCall(AST):
    obj: AST
    method: str
    args: TypingList[AST]
    line: int = 0
    column: int = 0