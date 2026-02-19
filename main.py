from time import time

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyser import Analyser, SymbolTable
from src.optimiser.optimiser import Optimiser
from src.ir.generator import IRGenerator
from src.runtime.regalloc import linear_scan_allocate
from src.runtime.vm import VM

from src.ir.operands import Reg, Imm
from src.exceptions import *

def fmt(x):
    if isinstance(x, Reg):
        return f"r{x.id}"
    if isinstance(x, Imm):
        return x.value
    return x

def token_length(token):
    if token is None:
        return 1
    if hasattr(token, 'id') and isinstance(token.id, str):
        return len(token.id)
    # Token with a value
    if hasattr(token, 'value') and token.value is not None:
        return len(str(token.value))
    return 1

code = """
fn check(a) {
    if a == 1 {
        return "a is 1"
    } else if a == 2 {
        return "a Is 2"
    } else if a == 3 {
        return "a is 3"
    } else {
        return "idk what a is"
    }
}

result = check(2)

i = 0
while i < result.len() {
    print(result.at(i).lower())
    i = i + 1
}

println()

nums = [1, 2, 3, 4, 5]
i = 0
while i < nums.len() {
    print(nums.at(i))
    i = i + 1
}
"""
num_regs = 1024
start = time()

try:
    lexer = Lexer(code)
    tokens = lexer.get_tokens()
    print(tokens)

    parser = Parser(tokens)
    tree = parser.parse()
    parser.dump(tree)

    symbol_table = SymbolTable()
    semantic_analysis = Analyser(symbol_table)
    semantic_analysis.analyse(tree)

    optimiser = Optimiser()
    tree = optimiser.optimise(tree)
    parser.dump(tree)

    ir_generator = IRGenerator()
    ir_generator.generate(tree)
    ir_generator.ir.dump()

    allocated = linear_scan_allocate(ir_generator.ir.code, num_regs=num_regs)

    for i, instr in enumerate(allocated):
        print(f"realloc{i} {instr.op} {fmt(instr.a)} {fmt(instr.b)} {fmt(instr.c)}") #:04 to pad to 4 0's

    start_vm = time()

    vm = VM(num_regs=num_regs)
    vm.code = allocated
    start_ip = vm.find_label("__main__")
    vm.ip = start_ip
    vm.run(allocated)
    vm.dump_regs()
    
    print(f"took {time() - start} secs")
    print(f"took {time() - start_vm} secs to run vm")

except CompileError as e:
    print(format_diagnostic(
        source=code,
        filename="<string>",
        line=e.line or 1,
        column=e.column or 1,
        message=e.message,
        level=e.level,
        highlight_length=token_length(e.token)
    ))
    exit(1)

except RuntimeError as e:
    print(format_diagnostic(
        source=code,
        filename="<string>",
        line=e.line or 1,
        column=e.column or 1,
        message=e.message,
        highlight_length=token_length(e.token)
    ))
    exit(1)

except IndexError as e:
    raise RuntimeError(f"number of regs prolly too low: {e}") from e

except Exception as e:
    raise RuntimeError(f"couldnt even begin to tell you where this came from: {e}") from e


# timeline for additions
#DONE better errors (lineno / badline)
#DONE levenshtein "error: did you mean '...'?"
#     real types
#     structs
#DONE dot notation
#     gc
#     module system
#     decent optimiser
#     better backend (x86-64)
#     bytecode + vm backend (its never too late to back down btw)
#     self-hosting

# further additions to my pain
#DONE test suite
#DONE list / arrays
#     multiple return values
#     error messages through vm
#     proper call frame model instead of copying vars every call
#     string interpolations (hopefully josh knows what this means)
#     default function arugments
#     break / continue in loops (PLEASE IMPLEMENT ME NOW!!!)
#     more builtins