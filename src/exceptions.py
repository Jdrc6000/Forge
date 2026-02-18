from dataclasses import dataclass
from typing import Optional

from src.frontend.token import Token

def format_diagnostic(
    source: str,
    filename: str,
    line: int,
    column: int,
    message: str,
    level: str = "error",           # error / warning / note
    highlight_length: int = 1
) -> str:
    lines = source.splitlines()
    if not (1 <= line <= len(lines)):
        return f"{filename}:{line}:{column}: {level}: {message} (line out of range)"

    lineno = line - 1
    bad_line = lines[lineno].rstrip()
    
    # Simple trimming for very long lines
    MAX = 72
    start = max(0, column - 1 - MAX // 2)
    end = min(len(bad_line), start + MAX)
    snippet = bad_line[start:end]
    caret_pos = (column - 1) - start

    color = {
        "error": "\033[91m",    # red
        "warning": "\033[93m",    # yellow
        "note": "\033[94m",    # blue
    }.get(level, "")

    reset = "\033[0m"

    return (
        f"{filename}:{line}:{column}: {color}{level}:{reset} {message}\n"
        f"   {line:3} │ {snippet}\n"
        f"       │ {' ' * caret_pos}{'^' * highlight_length}\n"
    )

@dataclass
class CompileError(Exception):
    message: str
    token: Optional[Token] = None
    line: Optional[int] = None
    column: Optional[int] = None
    level: str = "error" # error / warning / note
    
    # special to dataclasses
    # after class is created -> runs this
    def __post_init__(self):
        if self.token:
            self.line = self.line or self.token.line
            self.column = self.column or self.token.column
    
    def __str__(self) -> str:
        loc = ""
        if self.line is not None:
            loc = f"[{self.line}:{self.column or '?'}] "
        return f"{self.level.upper()} {loc}{self.message}"

@dataclass
class RuntimeError(Exception):
    message: str
    ip: Optional[int] = None
    instruction: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    
    def __str__(self) -> str:
        loc = ""
        if self.ip is not None:
            loc = f" at ip={self.ip}"
        
        if self.line is not None:
            loc += f" (source:{self.line}:{self.column or '?'})"
        
        return f"RUNTIME ERROR{loc}: {self.message}"

class LexerError(CompileError): pass
class ParseError(CompileError): pass
class SemanticError(CompileError): pass
class TypeError(CompileError): pass
class UndefinedVariableError(SemanticError): pass
class UnreachableCodeWarning(CompileError): pass

class DivisionByZeroError(RuntimeError): pass
class TypeMismatchError(RuntimeError): pass
class IndexOutOfBoundsError(RuntimeError): pass
class InvalidArgumentError(RuntimeError): pass
class StackUnderflowError(RuntimeError): pass # future-proofing
class UnknownOpcodeError(RuntimeError): pass
class LabelNotFoundError(RuntimeError): pass