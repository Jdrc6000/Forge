# past-josh: PLEASE FOR THE LOVE OF GOD REFACTOR TO REGISTER-BASED!!
# future-josh: your wish is my command
class VM:
    def __init__(self, num_regs):
        self.num_regs = num_regs
        self.regs = [None] * self.num_regs
        self.free_regs = list(range(self.num_regs))
        self.vars = {}
        self.stack = {}
        self.ip = 0 # instruction pointer
    
    def dump_regs(self): # simple dump debugger
        print(f"used regs: {len([reg for reg in self.regs if reg is not None])}")
        
        for index, reg in enumerate(self.regs): # prints every used reg
            if reg:
                print(f"reg {index} {reg}")
    
    def run(self, code):
        self.ip = 0
        
        while self.ip < len(code):
            instr = code[self.ip]
            op, a, b, c = instr.op, instr.a, instr.b, instr.c
            
            if op == "LOAD_CONST":
                self.regs[a] = b
            
            elif op == "LOAD_VAR":
                self.regs[a] = self.vars[b]
            
            elif op == "STORE_VAR":
                self.vars[a] = self.regs[b]
            
            elif op == "PRINT":
                print(self.regs[a])
            
            elif op == "JUMP":
                self.ip = a
                continue
            
            elif op == "JUMP_IF_TRUE":
                if self.regs[a]:
                    self.ip = b
                    continue
            
            elif op == "JUMP_IF_FALSE":
                if not self.regs[a]:
                    self.ip = b
                    continue
            
            elif op == "MOVE":
                self.regs[a] = self.regs[b]
            
            # spilling
            elif op == "SPILL_STORE":
                self.stack[a] = self.regs[b]

            elif op == "SPILL_LOAD":
                self.regs[a] = self.stack[b]
            
            # arithmetic
            elif op == "ADD":
                self.regs[a] = self.regs[b] + self.regs[c]

            elif op == "SUB":
                self.regs[a] = self.regs[b] - self.regs[c]

            elif op == "MUL":
                self.regs[a] = self.regs[b] * self.regs[c]

            elif op == "DIV":
                self.regs[a] = self.regs[b] / self.regs[c]

            elif op == "POW":
                self.regs[a] = self.regs[b] ** self.regs[c]

            elif op == "NEG":
                self.regs[a] = -self.regs[b]

            elif op == "NOT":
                self.regs[a] = not self.regs[b]

            # comparisons
            elif op == "EQ":
                self.regs[a] = self.regs[b] == self.regs[c]

            elif op == "NE":
                self.regs[a] = self.regs[b] != self.regs[c]

            elif op == "LT":
                self.regs[a] = self.regs[b] < self.regs[c]

            elif op == "GT":
                self.regs[a] = self.regs[b] > self.regs[c]

            elif op == "LE":
                self.regs[a] = self.regs[b] <= self.regs[c]

            elif op == "GE":
                self.regs[a] = self.regs[b] >= self.regs[c]

            else:
                raise RuntimeError(f"Unknown opcode {op}")
    
            self.ip += 1