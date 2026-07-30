from bootstrap.frontend.ast_nodes import *
from bootstrap.frontend.token_maps import *
from bootstrap.ir.ir import IR, Instr
from bootstrap.ir.operands import Imm
from bootstrap.runtime.builtins_registry import BUILTINS

class IRGenerator:
    def __init__(self):
        self.ir = IR()
        self.loop_stack = [] # [continue_ip, [break_patch_indicies]]
        self.current_struct_fields = None
    
    def _gen_struct_method(self, struct_name, method_node):
        label = f"{struct_name}.{method_node.name}"
        instr = Instr("LABEL", label)
        args = list(method_node.args)
        if not args or args[0] != "self":
            args = ["self"] + args
        instr.param_names = args
        instr.struct_names = struct_name
        self.ir.code.append(instr)
        
        struct_fields = None
        for i in self.ir.code:
            if i.op == "STRUCT_DEF" and i.a == struct_name:
                struct_fields = getattr(i, "fields", [])
                break
        
        old_fields = self.current_struct_fields
        self.current_struct_fields = struct_fields or []
        
        stmts = method_node.body.statements if isinstance(method_node.body, Block) else method_node.body
        for stmt in stmts:
            self.generate(stmt)
        
        self.current_struct_fields = old_fields
        
        default_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", default_reg, Imm(0))
        self.ir.emit("RETURN", default_reg)
    
    # helper
    def new_instr(self, op, a=None, b=None, c=None):
        return Instr(op, a, b, c, line=self.ir.current_line, column=self.ir.current_column)

    def generate(self, node):
        self.ir.current_line = getattr(node, 'line', 0) or self.ir.current_line
        self.ir.current_column = getattr(node, 'column', 0) or self.ir.current_column
        method = f"gen_{type(node).__name__}"
        return getattr(self, method)(node)
    
    def gen_Module(self, node):
        self.ir.emit("LABEL", "__main__")
        for stmt in node.body:
            if not isinstance(stmt, FunctionDef):
                self.generate(stmt)
                
        jmp = len(self.ir.code)
        self.ir.emit("JUMP", None)
        
        for stmt in node.body:
            if isinstance(stmt, FunctionDef):
                self.generate(stmt)
            elif isinstance(stmt, StructDef):
                for method in stmt.methods:
                    self._gen_struct_method(stmt.name, method)
                    
        self.ir.code[jmp].a = len(self.ir.code)
        
        end_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", end_reg, Imm(0))
        self.ir.emit("RETURN", end_reg)
    
    def gen_Expr(self, node):
        return self.generate(node.value)
    
    def gen_Constant(self, node):
        r = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", r, Imm(node.value))
        return r
    
    def gen_Name(self, node):
        if self.current_struct_fields and node.id in self.current_struct_fields:
            self_reg = self.ir.new_reg()
            self.ir.emit("LOAD_VAR", self_reg, "self")
            dest = self.ir.new_reg()
            instr = Instr("GET_ATTR", dest, self_reg, node.id)
            self.ir.code.append(instr)
            return dest
        
        r = self.ir.new_reg()
        self.ir.emit("LOAD_VAR", r, node.id)
        return r
    
    def gen_Assign(self, node):
        # Handle index assignment: map[key] = val or list[i] = val
        if isinstance(node.target, IndexGet):
            obj_reg = self.generate(node.target.obj)
            index_reg = self.generate(node.target.index)
            value_reg = self.generate(node.value)
            instr = self.new_instr("INDEX_SET", obj_reg, index_reg, value_reg)
            self.ir.code.append(instr)
            return
        # Handle attribute assignment: struct.field = val
        if isinstance(node.target, Attribute):
            obj_reg = self.generate(node.target.obj)
            value_reg = self.generate(node.value)
            instr = self.new_instr("SET_ATTR", obj_reg, node.target.attr, value_reg)
            self.ir.code.append(instr)
            return

        # Standard variable assignment
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
            instr = Instr("CALL", node.func.id, None, dest)
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
        instr = self.new_instr("CALL_METHOD", dest, obj_reg, node.method)
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
    # this is fixed now?
    def gen_Compare(self, node):
        if len(node.ops) == 1:
            left_reg = self.generate(node.left)
            right_reg = self.generate(node.comparators[0])
            dest = self.ir.new_reg()
            self.ir.emit(CMP_OP_TO_IR[node.ops[0]], dest, left_reg, right_reg)
            return dest

        result_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", result_reg, Imm(True))
        current_left = self.generate(node.left)
        
        jmp_indices = []
        for op_str, right_ast in zip(node.ops, node.comparators):
            right_reg = self.generate(right_ast)
            cmp_reg = self.ir.new_reg()
            self.ir.emit(CMP_OP_TO_IR[op_str], cmp_reg, current_left, right_reg)
            # AND first, then jump if the accumulated result is False
            self.ir.emit("AND", result_reg, result_reg, cmp_reg)
            jmp = len(self.ir.code)
            self.ir.emit("JUMP_IF_FALSE", result_reg, None)
            jmp_indices.append(jmp)
            current_left = right_reg
            
        end_ip = len(self.ir.code)
        for jmp in jmp_indices:
            self.ir.code[jmp].b = end_ip
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

        self.loop_stack.append(([], []))
        for stmt in node.body:
            self.generate(stmt)
        continue_patches, break_patches = self.loop_stack.pop()

        self.ir.emit("JUMP", start_label)      # jump back to start
        exit_ip = len(self.ir.code)
        self.ir.code[jmp_exit].b = exit_ip  # patch exit
        
        for patch in continue_patches:
            self.ir.code[patch].a = start_label
        for patch in break_patches:
            self.ir.code[patch].a = exit_ip
    
    def gen_For(self, node):
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
        
        self.loop_stack.append(([], []))
        for stmt in node.body:
            self.generate(stmt)
        continue_patches, break_patches = self.loop_stack.pop()

        # Increment loop variable
        increment_ip = len(self.ir.code)
        self.ir.emit("LOAD_VAR", var_reg, node.target.id)
        one_reg = self.ir.new_reg()
        self.ir.emit("LOAD_CONST", one_reg, Imm(1))
        self.ir.emit("ADD", var_reg, var_reg, one_reg)
        self.ir.emit("STORE_VAR", node.target.id, var_reg)

        # Jump back to start
        self.ir.emit("JUMP", loop_start)
        
        exit_ip = len(self.ir.code)
        self.ir.code[jmp_exit].b = exit_ip
        
        for patch in continue_patches:
            self.ir.code[patch].a = increment_ip
        for patch in break_patches:
            self.ir.code[patch].a = exit_ip
    
    def gen_Break(self, node):
        patch_index = len(self.ir.code)
        self.ir.emit("JUMP", None)
        self.loop_stack[-1][1].append(patch_index)
    
    def gen_Continue(self, node):
        patch_index = len(self.ir.code)
        self.ir.emit("JUMP", None)
        self.loop_stack[-1][0].append(patch_index)
    
    def gen_StructLiteral(self, node):
        arg_regs = [self.generate(a) for a in node.args]
        dest = self.ir.new_reg()
        instr = Instr("BUILD_STRUCT", dest, node.name)
        instr.arg_regs = arg_regs
        self.ir.code.append(instr)
        return dest
    
    def gen_Import(self, node):
        instr = Instr("IMPORT_MODULE", node.alias, node.module_name)
        self.ir.code.append(instr)
    
    def gen_Block(self, node):
        for stmt in node.statements:
            self.generate(stmt)
    
    def gen_StructDef(self, node):
        instr = Instr("STRUCT_DEF", node.name)
        instr.fields = node.fields
        instr.methods = [m.name for m in node.methods]
        self.ir.code.append(instr)
    
    # get ready for hashmaps!!!
    def gen_MapLiteral(self, node):
        kv_regs = []
        for key_ast, val_ast in node.pairs:
            kv_regs.append(self.generate(key_ast))
            kv_regs.append(self.generate(val_ast))
        dest = self.ir.new_reg()
        instr = self.new_instr("BUILD_MAP", dest)
        instr.arg_regs = kv_regs
        self.ir.code.append(instr)
        return dest

    def gen_IndexGet(self, node):
        obj_reg = self.generate(node.obj)
        index_reg = self.generate(node.index)
        dest = self.ir.new_reg()
        instr = self.new_instr("INDEX_GET", dest, obj_reg, index_reg)
        self.ir.code.append(instr)
        return dest

    def gen_IndexSet(self, node):
        obj_reg = self.generate(node.obj)
        index_reg = self.generate(node.index)
        value_reg = self.generate(node.value)
        instr = self.new_instr("INDEX_SET", obj_reg, index_reg, value_reg)
        self.ir.code.append(instr)
        return None