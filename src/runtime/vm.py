from src.frontend.token_types import *
from src.exceptions import *

# past-josh: PLEASE FOR THE LOVE OF GOD REFACTOR TO REGISTER-BASED!!
# future-josh: your wish is my command

# other past-josh: ok... PLEASE GET RID OF THIS AND COMPILE TO BYTECODE!!!!!!
class VM:
    def __init__(self, num_regs):
        self.num_regs = num_regs
        self.regs = [None] * self.num_regs
        self.free_regs = list(range(self.num_regs))
        self.vars = {}
        self.stack = {}
        self.call_stack = [] # (ip, locals)
        self.code = None # to be set in main.py
        self.ip = 0 # instruction pointer
    
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
        
        while self.ip < len(code):
            instr = code[self.ip]
            op, a, b, c = instr.op, instr.a, instr.b, instr.c
            
            if op == "LOAD_CONST":
                self.regs[a.id] = b.value
            
            elif op == "LOAD_VAR":
                self.regs[a.id] = self.vars[b]
            
            elif op == "STORE_VAR":
                self.vars[a] = self.regs[b.id]
            
            elif op == "PRINT":
                print(self.regs[a.id])
            
            elif op == "CALL":
                # saves ip, vars, and dest reg
                self.call_stack.append((self.ip + 1, self.vars.copy(), b))
                
                target_ip = self.find_label(a)
                self.ip = target_ip
                self.vars = {}

                # get param names from the LABEL instruction itself
                label_instr = code[target_ip]
                param_names = getattr(label_instr, "param_names", [])
                arg_regs = getattr(instr, "arg_regs", [])

                for name, reg in zip(param_names, arg_regs):
                    self.vars[name] = self.regs[reg.id]

                continue

            elif op == "RETURN":
                ret_value = None
                if a is not None:
                    ret_value = self.regs[a.id]

                if self.call_stack:
                    self.ip, caller_vars, dest_reg = self.call_stack.pop()
                    self.vars = caller_vars

                    if ret_value is not None and dest_reg is not None:
                        self.regs[dest_reg.id] = ret_value

                    continue
                else:
                    break
            
            elif op == "LABEL":
                # its literally just a label...
                # its meant to do nothing
                pass
            
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
                self.stack[a] = self.regs[b]

            elif op == "SPILL_LOAD":
                self.regs[a] = self.stack[b] # im conflicted... is it a then b, or b then a??
            
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
                # i literally dont know what error type to use, so i just used compiler
                raise UnknownOpcodeError(
                    message=f"Unknown opcode {op}",
                    ip=self.ip,
                    instruction=f"{op} {instr.a} {instr.b} {instr.c}"
                )
    
            self.ip += 1