

# past-josh: PLEASE FOR THE LOVE OF GOD REFACTOR TO REGISTER-BASED!!
# future-josh: your wish is my command
class VM:
    def __init__(self, num_regs):
        self.num_regs = num_regs
        self.regs = [None] * self.num_regs
        self.free_regs = list(range(self.num_regs))
        self.vars = {}
        self.ip = 0 # instruction pointer
    
    def alloc_reg(self):
        print("allocating reg")
        if not self.free_regs:
            raise RuntimeError("Out of registers")
        return self.free_regs.pop(0)
    
    def free_reg(self, reg):
        print(f"freeing reg: {reg} ({self.regs[reg]})")
        if True: #reg not in self.free_regs:
            self.free_regs.insert(0, reg)
            self.regs[reg] = None
    
    def run(self, code):
        self.ip = 0
        
        while self.ip < len(code):
            instr = code[self.ip]
            op, a, b, c = instr.op, instr.a, instr.b, instr.c
            
            if op in ("LOAD_CONST", "LOAD_VAR"):
                if a is None:
                    a = self.alloc_reg()
                    instr.a = a
            elif op in ("ADD","SUB","MUL","DIV","POW","NEG","NOT","EQ","NE","LT","GT","LE","GE"):
                if a is None:
                    a = self.alloc_reg()
                    instr.a = a
            
            if op == "LOAD_CONST":
                self.regs[a] = b
            
            elif op == "LOAD_VAR":
                self.regs[a] = self.vars[b]
            
            elif op == "STORE_VAR":
                self.vars[a] = self.regs[b]
                self.free_reg(b)
            
            elif op == "PRINT":
                print(self.regs[a])
                self.free_reg(a)
            
            elif op == "JUMP":
                self.ip = a
                continue
            
            elif op == "JUMP_IF_TRUE":
                if self.regs[a]:
                    self.ip = b
                    continue
                self.free_reg(a)
            
            elif op == "JUMP_IF_FALSE":
                if not self.regs[a]:
                    self.ip = b
                    continue
                self.free_reg(a)
            
            elif op == "MOVE":
                self.regs[a] = self.regs[b]
            
            # arithmetic
            elif op == "ADD":
                self.regs[a] = self.regs[b] + self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "SUB":
                self.regs[a] = self.regs[b] - self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "MUL":
                self.regs[a] = self.regs[b] * self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "DIV":
                self.regs[a] = self.regs[b] / self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "POW":
                self.regs[a] = self.regs[b] ** self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "NEG":
                self.regs[a] = -self.regs[b]
                self.free_reg(b)

            elif op == "NOT":
                self.regs[a] = not self.regs[b]
                self.free_reg(b)

            # comparisons
            elif op == "EQ":
                self.regs[a] = self.regs[b] == self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "NE":
                self.regs[a] = self.regs[b] != self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "LT":
                self.regs[a] = self.regs[b] < self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "GT":
                self.regs[a] = self.regs[b] > self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "LE":
                self.regs[a] = self.regs[b] <= self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            elif op == "GE":
                self.regs[a] = self.regs[b] >= self.regs[c]
                self.free_reg(b)
                self.free_reg(c)

            else:
                raise RuntimeError(f"Unknown opcode {op}")
    
            self.ip += 1