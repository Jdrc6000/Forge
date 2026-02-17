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

code = """
a = 
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
    tree = optimiser.optimize(tree)
    parser.dump(tree)

    ir_generator = IRGenerator()
    ir_generator.generate(tree)
    ir_generator.ir.dump()

    allocated = linear_scan_allocate(ir_generator.ir.code, num_regs=num_regs)

    for i, instr in enumerate(allocated):
        print(f"realloc{i} {instr.op} {fmt(instr.a)} {fmt(instr.b)} {fmt(instr.c)}") #:04 to pad to 4 0's

    vm = VM(num_regs=num_regs)
    vm.code = allocated
    start_ip = vm.find_label("__main__")
    vm.ip = start_ip
    vm.run(allocated)
    vm.dump_regs()
    
    print(f"took {time() - start} secs")

except CompileError as e:
    print(e)
    print(format_diagnostic(
        source=code,
        filename="<string>",
        line=e.line or 1,
        column=e.column or 1,
        message=e.message,
        level=e.level,
        highlight_length=1
    ))
    exit(1)

except Exception as e:
    print(f"random error that shouldnt of appeared appeared: {e}")
    raise


# timeline for additions:
    # better errors (lineno / badline)
    # real types
    # structs + dot notation
    # gc
    # module system
    # decent optimiser
    # better backend (x86-64)
    # self-hosting