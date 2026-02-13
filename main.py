from time import time

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyser import Analyser, SymbolTable
from src.optimiser.optimiser import Optimiser
from src.ir.generator import IRGenerator
from src.runtime.regalloc import linear_scan_allocate
from src.runtime.vm import VM

code = """
a = ((1+2) * (3+4)) + 3 - ((1+2) * (3+4)) + 3
print(5)
if a == 5:
    print("yes")
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

num_regs = 2
allocated = linear_scan_allocate(ir_generator.ir.code, num_regs=num_regs)

for i, instr in enumerate(allocated):
    print(f"realloc{i} {instr.op} {instr.a} {instr.b} {instr.c}") #:04 to pad to 4 0's

vm = VM(num_regs=num_regs)
vm.run(allocated)
vm.dump_regs()

print(f"took {time() - start} secs")