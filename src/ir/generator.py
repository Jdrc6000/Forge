from src.frontend.ast_nodes import *
from src.frontend.tokens import *
from src.ir.ir import IR, Instr
from src.ir.operands import Imm

class IRGenerator:
    def __init__(self):
        self.ir = IR()
    
    def generate(self, node):
        method = f"gen_{type(node).__name__}"
        return getattr(self, method)(node)
    
    def gen_Module(self, node):
        self.ir.emit("LABEL", "__main__")
        
        # first generate top-level statements
        for stmt in node.body:
            if not isinstance(stmt, FunctionDef):
                self.generate(stmt)

        # jump over function definitions so we don't fall into them
        jmp = len(self.ir.code)
        self.ir.emit("JUMP", None)

        # then generate function definitions
        for stmt in node.body:
            if isinstance(stmt, FunctionDef):
                self.generate(stmt)
        
        # patch the jump to land here (after all functions)
        self.ir.code[jmp].a = len(self.ir.code)
    
    def gen_Expr(self, node):
        return self.generate(node.value)
    
    def gen_Constant(self, node):
        r = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", r, Imm(node.value))
        return r
    
    def gen_Name(self, node):
        r = self.ir.new_reg()
        self.ir.emit("LOAD_VAR", r, node.id)
        return r
    
    def gen_Assign(self, node):
        value_reg = self.generate(node.value)
        self.ir.emit("STORE_VAR", node.target.id, value_reg)
    
    def gen_Call(self, node):
        if node.func.id == "print":
            arg_regs = [self.generate(a) for a in node.args]
            self.ir.emit("PRINT", arg_regs[0])
            return None
        else:
            arg_regs = [self.generate(a) for a in node.args]
            dest = self.ir.new_reg()
            instr = Instr("CALL", node.func.id, dest)
            instr.arg_regs = arg_regs
            instr.param_names = []  # will be resolved at runtime from FunctionDef label
            self.ir.code.append(instr)
            
            return dest
    
    # uses backpatching
    def gen_If(self, node):
        test = self.generate(node.test)

        jmp_false = len(self.ir.code)
        self.ir.emit("JUMP_IF_FALSE", test, None)

        for stmt in node.body:
            self.generate(stmt)

        if node.orelse:
            jmp_end = len(self.ir.code)
            self.ir.emit("JUMP", None)

            self.ir.code[jmp_false].b = len(self.ir.code)

            for stmt in node.orelse:
                self.generate(stmt)

            self.ir.code[jmp_end].a = len(self.ir.code)
        else:
            self.ir.code[jmp_false].b = len(self.ir.code)
    
    # here be dragons
    # honestly tho, i havent a clue whats going on, but all i know
    # is that you can now do:
    #   a < b < c
    def gen_Compare(self, node):
        left = self.generate(node.left)

        result = None
        current_left = left

        for comp in node.comparators:
            right = self.generate(comp)
            dest = self.ir.new_reg()
            
            # safeguards against idiots using wrongs ops (me)
            opcode = cmp.get(node.op)
            if not opcode:
                raise RuntimeError(f"Unsupported comparison {node.op}")
            self.ir.emit(opcode, dest, left, right)

            if result is None:
                result = dest
            else:
                # combine with AND
                tmp = self.ir.new_reg()
                self.ir.emit("AND", tmp, result, dest)
                result = tmp

            current_left = right

        return result
    
    # binop the goat for using less regs
    def gen_BinOp(self, node):
        # short-circuit logic
        if node.op in ("and", "or"):
            return self.gen_logic(node)

        # generate left first
        left = self.generate(node.left)
        right = self.generate(node.right)

        # reuse left register as destination
        dest = left
        self.ir.emit(binops[node.op], dest, left, right)
        return dest
    
    def gen_logic(self, node):
        left = self.generate(node.left)
        dest = self.ir.new_reg()

        # copy left into dest
        self.ir.emit("MOVE", dest, left)

        if node.op == "and":
            jmp = len(self.ir.code)
            self.ir.emit("JUMP_IF_FALSE", dest, None)

            right = self.generate(node.right)
            self.ir.emit("MOVE", dest, right)

            self.ir.code[jmp].b = len(self.ir.code)

        else: # or
            jmp = len(self.ir.code)
            self.ir.emit("JUMP_IF_TRUE", dest, None)

            right = self.generate(node.right)
            self.ir.emit("MOVE", dest, right)

            self.ir.code[jmp].b = len(self.ir.code)

        return dest
    
    def gen_UnOp(self, node):
        src = self.generate(node.operand)
        dest = self.ir.new_reg()

        if node.op == "-":
            self.ir.emit("NEG", dest, src)
        elif node.op == "not":
            self.ir.emit("NOT", dest, src)
        else:
            self.ir.emit("MOVE", dest, src)

        return dest
    
    def gen_FunctionDef(self, node):
        instr = Instr("LABEL", node.name)
        instr.param_names = node.args
        self.ir.code.append(instr)
        
        for stmt in node.body:
            self.generate(stmt)
        
        default_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", default_reg, Imm(0))
        self.ir.emit("RETURN", default_reg)
    
    def gen_Return(self, node):
        if node.value:
            reg = self.generate(node.value)
        else:
            reg = self.ir.new_reg()
            self.ir.emit("LOAD_CONST", reg, Imm(0))

        self.ir.emit("RETURN", reg)
    
    def gen_While(self, node):
        start_label = len(self.ir.code)       # start of loop
        test_reg = self.generate(node.test)

        jmp_exit = len(self.ir.code)
        self.ir.emit("JUMP_IF_FALSE", test_reg, None)  # exit if false

        for stmt in node.body:
            self.generate(stmt)

        self.ir.emit("JUMP", start_label)      # jump back to start
        self.ir.code[jmp_exit].b = len(self.ir.code)  # patch exit
    
    def gen_For(self, node):
        # Generate start and end values
        start_reg = self.generate(node.start)
        end_reg = self.generate(node.end)

        # Store start in loop variable
        var_reg = self.ir.new_reg()
        self.ir.emit("MOVE", var_reg, start_reg)
        self.ir.emit("STORE_VAR", node.target.id, var_reg)

        loop_start = len(self.ir.code)  # start of loop

        # Load loop variable
        loop_var_reg = self.ir.new_reg()
        self.ir.emit("LOAD_VAR", loop_var_reg, node.target.id)

        # Compare with end
        cmp_reg = self.ir.new_reg()
        self.ir.emit("LT", cmp_reg, loop_var_reg, end_reg)  # loop while var < end

        jmp_exit = len(self.ir.code)
        self.ir.emit("JUMP_IF_FALSE", cmp_reg, None)

        # Generate loop body
        for stmt in node.body:
            self.generate(stmt)

        # Increment loop variable
        self.ir.emit("LOAD_VAR", var_reg, node.target.id)
        one_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", one_reg, Imm(1))
        self.ir.emit("ADD", var_reg, var_reg, one_reg)
        self.ir.emit("STORE_VAR", node.target.id, var_reg)

        # Jump back to start
        self.ir.emit("JUMP", loop_start)
        self.ir.code[jmp_exit].b = len(self.ir.code)