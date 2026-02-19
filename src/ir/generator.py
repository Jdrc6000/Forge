from src.frontend.ast_nodes import *
from src.frontend.token_maps import *
from src.ir.ir import IR, Instr
from src.ir.operands import Imm
from src.runtime.builtins_registry import BUILTINS

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
        func_name = node.func.id
        
        if func_name in BUILTINS:
            arg_regs = [self.generate(a) for a in node.args]
            dest = self.ir.new_reg()
            self.ir.emit("CALL_BUILTIN", func_name, arg_regs, dest) # NEW OPCODE!!!!!!
            return dest

        else:
            arg_regs = [self.generate(a) for a in node.args]
            dest = self.ir.new_reg()
            instr = Instr("CALL", node.func.id, dest)
            instr.arg_regs = arg_regs
            instr.param_names = []  # will be resolved at runtime from FunctionDef label
            self.ir.code.append(instr)
            
            return dest
    
    def gen_Attribute(self, node):
        obj_reg = self.generate(node.obj)
        dest = self.ir.new_reg()
        instr = Instr("GET_ATTR", dest, obj_reg, node.attr)
        self.ir.code.append(instr)
        return dest
    
    def gen_MethodCall(self, node):
        obj_reg = self.generate(node.obj)
        arg_regs = [self.generate(a) for a in node.args]
        dest = self.ir.new_reg()
        instr = Instr("CALL_METHOD", dest, obj_reg, node.method)
        instr.arg_regs = arg_regs
        self.ir.code.append(instr)
        return dest
    
    def gen_List(self, node):
        element_regs = [self.generate(element) for element in node.elements]
        dest = self.ir.new_reg()
        instr = Instr("BUILD_LIST", dest)
        instr.arg_regs = element_regs
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

            orelse = node.orelse
            if isinstance(orelse, (If, Block)):
                orelse = [orelse]
            for stmt in orelse:
                self.generate(stmt)

            self.ir.code[jmp_end].a = len(self.ir.code)
        else:
            self.ir.code[jmp_false].b = len(self.ir.code)
    
    # here be dragons
    # honestly tho, i havent a clue whats going on, but all i know is that you can now do:
    #   a < b < c
    def gen_Compare(self, node):
        # We generate:   result = left op1 comp[0]  AND  comp[0] op2 comp[1]  AND ...
        left_reg = self.generate(node.left)
        result_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", result_reg, Imm(True)) # start assuming true

        current_left = left_reg

        for op_str, right_ast in zip(node.ops, node.comparators):
            right_reg = self.generate(right_ast)
            cmp_reg = self.ir.new_reg()
            ir_op = CMP_OP_TO_IR[op_str]
            self.ir.emit(ir_op, cmp_reg, current_left, right_reg)
            self.ir.emit("AND", result_reg, result_reg, cmp_reg)
            current_left = right_reg

        return result_reg
    
    # binop the goat for using less regs
    def gen_BinOp(self, node):
        # short-circuit logic
        if node.op in ("and", "or"):
            return self.gen_logic(node)

        # generate left first
        left = self.generate(node.left)
        right = self.generate(node.right)

        dest = self.ir.new_reg()
        self.ir.emit(BINOPS[node.op], dest, left, right)
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
        
        stmts = node.body.statements if isinstance(node.body, Block) else node.body
        for stmt in stmts:
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