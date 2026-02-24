from time import time
import os

from bootstrap.frontend.lexer import Lexer
from bootstrap.frontend.parser import Parser
from bootstrap.semantic.analyser import Analyser
from bootstrap.semantic.symbol_table import SymbolTable
from bootstrap.optimiser.optimiser import Optimiser
from bootstrap.ir.generator import IRGenerator
from bootstrap.ir.cfg_builder import build_cfg
from bootstrap.ir.liveness import compute_liveness, eliminate_dead_stores, remove_unreachable
from bootstrap.runtime.regalloc import linear_scan_allocate
from bootstrap.runtime.vm import VM

from bootstrap.ir.operands import Reg, Imm
from bootstrap.exceptions import *

def fmt(x):
    if isinstance(x, Reg): return f"r{x.id}"
    if isinstance(x, Imm): return x.value
    return x

def token_length(token):
    if token is None: return 1
    if hasattr(token, 'id') and isinstance(token.id, str): return len(token.id)
    if hasattr(token, 'value') and token.value is not None: return len(str(token.value))
    return 1

def run_file(filepath):
    source_dir = os.path.dirname(os.path.abspath(filepath))
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    run_source(code, source_dir=source_dir, filename=filepath)

def run_source(code, source_dir=".", filename="<string>", num_regs=1024):
    start = time()
    
    try:
        lexer = Lexer(code)
        tokens = lexer.get_tokens()
        #print(tokens)

        parser = Parser(tokens)
        tree = parser.parse()
        #parser.dump(tree)

        symbol_table = SymbolTable()
        semantic_analysis = Analyser(symbol_table, source_dir=source_dir)
        semantic_analysis.analyse(tree)

        optimiser = Optimiser()
        tree = optimiser.optimise(tree)
        #parser.dump(tree)

        ir_generator = IRGenerator()
        ir_generator.generate(tree)
        #ir_generator.ir.dump()
        
        cfg = build_cfg(ir_generator.ir.code)
        #cfg.dump()
        remove_unreachable(cfg) # first
        compute_liveness(cfg) # second
        eliminate_dead_stores(cfg) # third
        #cfg.dump()

        flat_code = cfg.flatten()
        allocated = linear_scan_allocate(flat_code, num_regs=num_regs)

        #for i, instr in enumerate(allocated):
        #    print(f"realloc{i} {instr.op} {fmt(instr.a)} {fmt(instr.b)} {fmt(instr.c)}") #:04 to pad to 4 0's

        start_vm = time()

        vm = VM(num_regs=num_regs, source_dir=source_dir)
        vm.code = allocated
        start_ip = vm.find_label("__main__")
        vm.ip = start_ip
        
        start_vm = time()
        vm.run(allocated)
        #vm.dump_regs()
        
        print(f"compile: {start_vm - start:.4f}s")
        print(f"run: {time() - start_vm:.4f}s")
        print(f"total: {time() - start:.4f}s")

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
            highlight_length=token_length(getattr(e, 'token', None))
        ))
        exit(1)

    except IndexError as e:
        raise RuntimeError(f"number of regs prolly too low: {e}") from e

    except Exception as e:
        raise RuntimeError(f"couldnt even begin to tell you where this came from: {e}") from e

if __name__ == "__main__":
    run_file(r"./forge/examples/test.fg")

# timeline for additions
#DONE better errors (lineno / badline)
#DONE levenshtein "error: did you mean '...'?"
#     real types
#DONE structs
#DONE dot notation
#     gc
#DONE module system
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
#DONE break / continue in loops
#DONE more builtins
#     type annotations