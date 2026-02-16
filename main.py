from time import time

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyser import Analyser, SymbolTable
from src.optimiser.optimiser import Optimiser
from src.ir.generator import IRGenerator
from src.runtime.regalloc import linear_scan_allocate
from src.runtime.vm import VM

from src.ir.operands import Reg, Imm

code = """
fn check(a, b):
    if a == b:
        return true
    else:
        return false

print(check(5, 1))
"""

start = time()

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

num_regs = 1024
allocated = linear_scan_allocate(ir_generator.ir.code, num_regs=num_regs)

def fmt(x):
    if isinstance(x, Reg):
        return f"r{x.id}"
    if isinstance(x, Imm):
        return x.value
    return x
for i, instr in enumerate(allocated):
    print(f"realloc{i} {instr.op} {fmt(instr.a)} {fmt(instr.b)} {fmt(instr.c)}") #:04 to pad to 4 0's

vm = VM(num_regs=num_regs)
vm.code = allocated
start_ip = vm.find_label("__main__")
vm.ip = start_ip
vm.run(allocated)
vm.dump_regs()

print(f"took {time() - start} secs")