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
        print(f"used spills: {len(self.stack)}")
        
        for index, reg in enumerate(self.regs): # prints every used reg
            if reg is not None:
                print(f"reg {index} {reg}")
        
        for slot, value in self.stack.items(): # prints every spill var in stack
            print(f"spill {slot} {value}")
    
    def run(self, code):
        self.ip = 0
        
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
                self.regs[a] = self.stack[b]
            
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
                raise RuntimeError(f"Unknown opcode {op}")
    
            self.ip += 1