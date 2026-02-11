from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.semantic.analyser import Analyser, SymbolTable
from src.ir.generator import IRGenerator
from src.runtime.vm import VM

code = """
x = 4 + 3
print(2 + x)
"""

lexer = Lexer(code)
tokens = lexer.get_tokens()
print(tokens)

parser = Parser(tokens)
tree = parser.parse()
parser.dump(tree)

symbol_table = SymbolTable()
semantic_analysis = Analyser(symbol_table)
semantic_analysis.analyse(tree)

ir_generator = IRGenerator()
ir_generator.generate(tree)
ir_generator.ir.dump()

vm = VM(num_regs=6)
vm.run(ir_generator.ir.code)
for index, reg in enumerate(vm.regs):
    if reg: print(f"r{index} {reg}")