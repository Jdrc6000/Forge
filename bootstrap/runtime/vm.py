import os

from bootstrap.frontend.token_types import *
from bootstrap.exceptions import *
from .builtins_registry import BUILTINS
from .methods import resolve_member

from bootstrap.frontend.lexer import Lexer
from bootstrap.frontend.parser import Parser
from bootstrap.semantic.analyser import Analyser
from bootstrap.semantic.symbol_table import SymbolTable
from bootstrap.optimiser.optimiser import Optimiser
from bootstrap.ir.generator import IRGenerator
from bootstrap.ir.cfg_builder import build_cfg
from bootstrap.ir.liveness import remove_unreachable
from bootstrap.runtime.regalloc import linear_scan_allocate

# past-josh: PLEASE FOR THE LOVE OF GOD REFACTOR TO REGISTER-BASED!!
# future-josh: your wish is my command

# other past-josh: ok... PLEASE GET RID OF THIS AND COMPILE TO BYTECODE!!!!!!
class VM:
    def __init__(self, num_regs, source_dir="."):
        self.num_regs = num_regs
        self.regs = [None] * self.num_regs
        self.free_regs = list(range(self.num_regs))
        self.vars = {}
        self.stack = {}
        self.call_stack = [] # (ip, locals)
        self.code = None # to be set in main.py
        self.ip = 0 # instruction pointer
        
        self.builtins = BUILTINS
        
        self.structs = {}
        self.struct_methods = {}
        
        self.source_dir = source_dir
    
    def _compile_and_run_module(self, module_name):
        path = os.path.join(self.source_dir, f"{module_name}.fg")
        if not os.path.exists(path):
            raise RuntimeError(
                message=f"Module '{module_name}' not found at '{path}'",
                ip=self.ip
            )
        
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()
        
        tokens = Lexer(source).get_tokens()
        tree = Parser(tokens).parse()
        Analyser(SymbolTable(), source_dir=self.source_dir).analyse(tree)
        tree = Optimiser().optimise(tree)
        ir_gen = IRGenerator()
        ir_gen.generate(tree)
        cfg = build_cfg(ir_gen.ir.code)
        remove_unreachable(cfg)
        
        flat = cfg.flatten()
        allocated = linear_scan_allocate(flat, num_regs=self.num_regs)
        
        child_vm = VM(num_regs=self.num_regs, source_dir=self.source_dir)
        child_vm.code = allocated
        child_vm.ip = child_vm.find_label("__main__")
        child_vm.run(allocated)
        return child_vm.vars, allocated
    
    def dump_regs(self): # simple dump debugger
        print(f"used regs: {len([reg for reg in self.regs if reg is not None])}")
        print(f"used spills: {len(self.stack)}")
        
        for index, reg in enumerate(self.regs): # prints every used reg
            if reg is not None:
                print(f"reg {index} {reg}")
        
        for slot, value in self.stack.items(): # prints every spill var in stack
            print(f"spill {slot} {value}")
    
    def find_label(self, label_name): # for functions / gen calls
        for i, instr in enumerate(self.code):
            if instr.op == "LABEL" and instr.a == label_name:
                return i
        
        raise LabelNotFoundError(
            message=f"Label not found: {label_name}",
            ip=self.ip
        )
    
    def run(self, code):
        self.code = code
        self.structs = {}
        self.struct_methods = {}
        
        for i, instr in enumerate(code):
            if instr.op == "STRUCT_DEF":
                self.struct_methods[instr.a] = {
                    "fields": getattr(instr, "fields", []),
                    "methods": getattr(instr, "methods", [])
                }
            
            elif instr.op == "LABEL" and getattr(instr, "struct_names", None) is not None:
                self.struct_methods[instr.a] = i
        
        while self.ip < len(self.code):
            instr = self.code[self.ip]
            op, a, b, c = instr.op, instr.a, instr.b, instr.c
            
            if op == "LOAD_CONST":
                self.regs[a.id] = b.value
            
            elif op == "LOAD_VAR":
                if b not in self.vars:
                    if any(k.startswith(f"{b}.") for k in self.vars):
                        self.regs[a.id] = _ModuleNamespace(b)
                    
                    else:
                        raise RuntimeError(
                            message=f"Undefined variable '{b}'",
                            ip=self.ip
                        )
                
                else:
                    self.regs[a.id] = self.vars[b]
            
            elif op == "STORE_VAR":
                self.vars[a] = self.regs[b.id]
            
            elif op == "GET_ATTR":
                obj = self.regs[b.id]
                attr_name = c
                
                if isinstance(obj, _ModuleNamespace):
                    ns_key = f"{obj.alias}.{attr_name}"
                    if ns_key not in self.vars:
                        raise RuntimeError(
                            message=f"Module '{obj.alias}' has no export '{attr_name}'",
                            ip=self.ip
                        )
                    
                    self.regs[a.id] = self.vars[ns_key]
                
                elif isinstance(obj, dict):
                    if attr_name not in obj:
                        raise RuntimeError(
                            message=f"Struct has no field '{attr_name}'",
                            ip=self.ip
                        )
                    
                    self.regs[a.id] = obj[attr_name]
                
                else:
                    try:
                        handler = resolve_member(obj, attr_name)
                        self.regs[a.id] = handler(obj, [])
                    
                    except AttributeError as e:
                        raise RuntimeError(
                            message=str(e),
                            ip=self.ip
                        )
            
            elif op == "CALL_METHOD":
                obj = self.regs[b.id]
                method_name = c
                arg_regs = getattr(instr, "arg_regs", [])
                args = [self.regs[r.id] for r in arg_regs]
                
                if isinstance(obj, _ModuleNamespace):
                    func_val = self.vars.get(f"{obj.alias}.{method_name}")
                    
                    if isinstance(func_val, tuple) and func_val[0] == "__func__":
                        target_ip = func_val[1]
                        self.call_stack.append((self.ip + 1, self.vars.copy(), self.regs[:], a))
                        self.ip = target_ip
                        label_instr = self.code[target_ip]
                        param_names = getattr(label_instr, "param_names", [])
                        self.vars = {}
                        for name, val in zip(param_names, args):
                            self.vars[name] = val
                        continue
                    
                    raise RuntimeError(
                        message=f"Module '{obj.alias}' has no function '{method_name}'",
                        ip=self.ip
                    )
                
                elif isinstance(obj, dict) and "__type__" in obj:
                    struct_type = obj["__type__"]
                    full_name = f"{struct_type}.{method_name}"
                    
                    if full_name in self.struct_methods:
                        target_ip = self.struct_methods[full_name]
                        self.call_stack.append((self.ip + 1, self.vars.copy(), self.regs[:], a))
                        self.ip = target_ip
                        label_instr = self.code[target_ip]
                        param_names = getattr(label_instr, "param_names", [])
                        
                        self.vars = {}
                        if param_names:
                            self.vars[param_names[0]] = obj
                            for name, val in zip(param_names[1:], args):
                                self.vars[name] = val
                        
                        continue
                
                try:
                    handler = resolve_member(obj, method_name)
                    result = handler(obj, args)
                    self.regs[a.id] = result
                
                except AttributeError as e:
                    raise RuntimeError(
                        message=str(e),
                        ip=self.ip
                    )
                
                except (TypeError, NotImplementedError) as e:
                    raise RuntimeError(
                        message=str(e),
                        ip=self.ip
                    )
            
            elif op == "CALL":
                func_name = instr.a
                
                if func_name in self.builtins:
                    builtin = self.builtins[func_name]
                    arg_regs = getattr(instr, "arg_regs", [])
                    ret = builtin(self, arg_regs)
                    if hasattr(instr, "c") and instr.c:
                        self.regs[instr.c.id] = ret
                
                else:
                    func_val = self.vars.get(func_name)
                    if isinstance(func_val, tuple) and func_val[0] == "__func__":
                        target_ip = func_val[1]
                    else:
                        target_ip = self.find_label(func_name)
                    
                    # saves ip, vars, and dest reg
                    self.call_stack.append((self.ip + 1, self.vars.copy(), self.regs[:], c))
                    
                    self.ip = target_ip
                    self.vars = {}

                    # get param names from the LABEL instruction itself
                    label_instr = self.code[target_ip]
                    param_names = getattr(label_instr, "param_names", [])
                    arg_regs = getattr(instr, "arg_regs", [])

                    for name, reg in zip(param_names, arg_regs):
                        self.vars[name] = self.regs[reg.id]

                    continue
            
            elif op == "CALL_BUILTIN":
                func_name = instr.a
                arg_regs = instr.b
                builtin = self.builtins[func_name]
                ret = builtin(self, arg_regs)
                if instr.c:
                    self.regs[instr.c.id] = ret

            elif op == "IMPORT_MODULE":
                alias, module_name = a, b
                module_vars, module_code = self._compile_and_run_module(module_name)
                for var_name, value in module_vars.items():
                    self.vars[f"{alias}.{var_name}"] = value
                offset = len(self.code)
                
                # Patch all absolute jump targets in module_code to be offset-adjusted
                from bootstrap.ir.ir import Instr as _Instr
                patched_module_code = []
                for minstr in module_code:
                    new_instr = _Instr(minstr.op, minstr.a, minstr.b, minstr.c)
                    
                    for attr in ("arg_regs", "param_names", "fields", "struct_names", "methods"):
                        if hasattr(minstr, attr):
                            setattr(new_instr, attr, getattr(minstr, attr))
                    
                    if minstr.op == "JUMP" and isinstance(minstr.a, int):
                        new_instr.a = minstr.a + offset
                    
                    elif minstr.op in ("JUMP_IF_TRUE", "JUMP_IF_FALSE") and isinstance(minstr.b, int):
                        new_instr.b = minstr.b + offset
                    
                    patched_module_code.append(new_instr)
                
                self.code = self.code + patched_module_code
                for i, minstr in enumerate(patched_module_code):
                    if (minstr.op == "LABEL" and minstr.a != "__main__"
                        and not getattr(minstr, "struct_names", None)):
                        self.vars[f"{alias}.{minstr.a}"] = ("__func__", offset + i)

            elif op == "RETURN":
                ret_value = None
                if a is not None:
                    ret_value = self.regs[a.id]

                if self.call_stack:
                    self.ip, caller_vars, saved_regs, dest_reg = self.call_stack.pop()
                    self.vars = caller_vars
                    self.regs = saved_regs

                    if ret_value is not None and dest_reg is not None:
                        self.regs[dest_reg.id] = ret_value

                    continue
                else:
                    break
            
            elif op == "BUILD_LIST":
                arg_regs = getattr(instr, "arg_regs", [])
                self.regs[a.id] = [self.regs[r.id] for r in arg_regs]
            
            elif op == "BUILD_STRUCT":
                # works alongside `STRUCT_DEF` below
                arg_regs = getattr(instr, "arg_regs", [])
                struct_name = b
                fields = self.structs.get(struct_name, {}).get("fields", [])
                obj = {"__type__": struct_name}
                
                for field, reg in zip(fields, arg_regs):
                    obj[field] = self.regs[reg.id]
                
                self.regs[a.id] = obj
            
            elif op == "STRUCT_DEF":
                self.structs[instr.a] = {
                    "fields": getattr(instr, "fields", []),
                    "methods": getattr(instr, "methods", [])
                }
            
            elif op == "LABEL":
                if getattr(instr, "struct_names", None) is not None:
                    self.struct_methods[instr.a] = self.ip
            
            elif op == "JUMP":
                self.ip = a
                continue
            
            elif op == "JUMP_IF_TRUE":
                if self.regs[a.id]:
                    self.ip = b
                    continue
            
            elif op == "JUMP_IF_FALSE":
                if not self.regs[a.id]:
                    self.ip = b
                    continue
            
            elif op == "MOVE":
                self.regs[a.id] = self.regs[b.id]
            
            # spilling
            elif op == "SPILL_STORE":
                self.stack[a] = self.regs[b.id]

            elif op == "SPILL_LOAD":
                self.regs[a.id] = self.stack[b] # im conflicted... is it a then b, or b then a??
            
            # arithmetic
            elif op == "ADD":
                self.regs[a.id] = self.regs[b.id] + self.regs[c.id]
            elif op == "SUB":
                self.regs[a.id] = self.regs[b.id] - self.regs[c.id]
            elif op == "MUL":
                self.regs[a.id] = self.regs[b.id] * self.regs[c.id]
            elif op == "DIV":
                self.regs[a.id] = self.regs[b.id] / self.regs[c.id]
            elif op == "POW":
                self.regs[a.id] = self.regs[b.id] ** self.regs[c.id]
            elif op == "NEG":
                self.regs[a.id] = -self.regs[b.id]
            elif op == "NOT":
                self.regs[a.id] = not self.regs[b.id]

            # comparisons
            elif op == "EQ":
                self.regs[a.id] = self.regs[b.id] == self.regs[c.id]
            elif op == "NE":
                self.regs[a.id] = self.regs[b.id] != self.regs[c.id]
            elif op == "LT":
                self.regs[a.id] = self.regs[b.id] < self.regs[c.id]
            elif op == "GT":
                self.regs[a.id] = self.regs[b.id] > self.regs[c.id]
            elif op == "LE":
                self.regs[a.id] = self.regs[b.id] <= self.regs[c.id]
            elif op == "GE":
                self.regs[a.id] = self.regs[b.id] >= self.regs[c.id]
            elif op == "AND":
                self.regs[a.id] = self.regs[b.id] and self.regs[c.id]

            else:
                raise UnknownOpcodeError(
                    message=f"Unknown opcode {op}",
                    ip=self.ip,
                    instruction=f"{op} {instr.a} {instr.b} {instr.c}"
                )
    
            self.ip += 1

class _ModuleNamespace:
    def __init__(self, alias):
        self.alias = alias
    
    def __repr__(self):
        return f"<module:{self.alias}>"