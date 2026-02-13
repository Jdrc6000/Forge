from src.frontend.ast_nodes import Constant, BinOp, UnOp, If

class Pass:
    def run(self, node):
        method = f"visit_{type(node).__name__}"
        return getattr(self, method, self.generic)(node)

    def generic(self, node):
        for field, value in vars(node).items():
            if isinstance(value, list):
                setattr(node, field, [self.run(v) for v in value])
            elif hasattr(value, "__dict__"):
                setattr(node, field, self.run(value))
        return node

class ConstantFolder(Pass):
    def visit_BinOp(self, node):
        node.left = self.run(node.left)
        node.right = self.run(node.right)
        
        if isinstance(node.left, Constant) and isinstance(node.right, Constant):
            l = node.left.value
            r = node.right.value
            
            if node.op == "+": return Constant(l + r)
            if node.op == "-": return Constant(l - r)
            if node.op == "*": return Constant(l * r)
            if node.op == "/": return Constant(l / r)
            if node.op == "^": return Constant(l ** r)
            if node.op == "and": return Constant(l and r)
            if node.op == "or": return Constant(l or r)
        
        return node
    
    def visit_UnOp(self, node):
        node.operand = self.run(node.operand)
        
        if isinstance(node.operand, Constant):
            val = node.operand.value
            
            if node.op == "-":
                return Constant(-val)
            
            if node.op == "not":
                return Constant(not val)
        
        return node

class DeadCodeEliminator(Pass):
    def visit_If(self, node):
        node.test = self.run(node.test)
        
        if isinstance(node.test, Constant):
            if node.test.value:
                return [self.run(stmt) for stmt in node.body]
            else:
                return [self.run(stmt) for stmt in (node.orelse or [])]
        
        node.body = [self.run(s) for s in node.body]
        
        if node.orelse:
            node.orelse = [self.run(s) for s in node.orelse]
        
        return node