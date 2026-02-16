from src.frontend.ast_nodes import Constant, BinOp, UnOp, If

class Pass:
    def __init__(self):
        self.visited = set()
    
    def run(self, node):
        if id(node) in self.visited:
            return node
        self.visited.add(id(node))
        
        method = f"visit_{type(node).__name__}"
        if hasattr(self, method):
            return getattr(self, method, self.generic)(node)
        else:
            return self.generic(node)
    
    def generic(self, node):
        # safe guard against edge case #4282
        method = f"visit_{type(node).__name__}"
        if hasattr(self, method):
            return getattr(self, method)(node)
        
        # safe guard against edge case #382
        if not hasattr(node, "__dict__"):
            return node
        
        for field, value in vars(node).items():
            if isinstance(value, list):
                new_list = []
                for v in value:
                    result = self.run(v)
                    if isinstance(result, list):
                        new_list.extend(result)
                    else:
                        new_list.append(result)
                setattr(node, field, new_list)

            elif hasattr(value, "__dict__"):
                result = self.run(value)
                setattr(node, field, result)

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
    
    def visit_Compare(self, node):
        node.left = self.run(node.left)
        node.comparators = [self.run(c) for c in node.comparators]

        if isinstance(node.left, Constant) and isinstance(node.comparators[0], Constant):
            l = node.left.value
            r = node.comparators[0].value

            if node.op == "EE": return Constant(l == r)
            if node.op == "NE": return Constant(l != r)
            if node.op == "LESS": return Constant(l < r)
            if node.op == "GREATER": return Constant(l > r)
            if node.op == "LE": return Constant(l <= r)
            if node.op == "GE": return Constant(l >= r)

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