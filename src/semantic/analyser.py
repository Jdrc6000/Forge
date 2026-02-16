from src.semantic.types import *
from src.frontend.ast_nodes import *
from src.semantic.symbol_table import *

# message for future-josh
#  this is going to be the most confusing, awful, horrid-looking code you have ever seen,
#  so dont even bother trying to debug this pile of horse-doodoo

# future-josh here, i have to debug this now...

class Analyser():
    def __init__(self, symbols):
        self.symbols: SymbolTable = symbols
    
    def analyse(self, node):
        if isinstance(node, Module):
            for stmt in node.body:
                self.analyse(stmt)
        
        elif isinstance(node, Call):
            for arg in node.args:
                self.analyse(arg)
            
            return None
        
        # unused?
        elif isinstance(node, Expr):
            self.analyse(node.value)
        
        elif isinstance(node, Assign):
            value_type = self.analyse(node.value)
            self.symbols.define(node.target.id, value_type)
        
        elif isinstance(node, Name):
            if not self.symbols.exists(node.id):
                raise Exception(f"Undefined variable '{node.id}'")
            
            return self.symbols.get(node.id)["type"]
        
        elif isinstance(node, Constant):
            value = node.value
            
            if isinstance(value, str):
                node.inferred_type = STRING
                return STRING
            
            elif isinstance(value, bool):
                node.inferred_type = BOOL
                return BOOL
            
            elif isinstance(value, (float, int)):
                node.inferred_type = NUMBER
                return NUMBER
        
        elif isinstance(node, BinOp):
            left = self.analyse(node.left)
            right = self.analyse(node.right)

            # if left is unknown, adopt right's type
            if isinstance(left, UnknownType):
                left = right
                node.left.inferred_type = right

            if isinstance(right, UnknownType):
                right = left
                node.right.inferred_type = left

            if not left.supports_binary(node.op, right):
                raise TypeError(f"Operator '{node.op}' not supported between {left} and {right}")

            node.inferred_type = left
            return left
        
        elif isinstance(node, If):
            test_type = self.analyse(node.test)
            if test_type != BOOL:
                raise TypeError("If condition must be boolean")

            for stmt in node.body:
                self.analyse(stmt)

            if node.orelse:
                for stmt in node.orelse:
                    self.analyse(stmt)
        
        elif isinstance(node, Compare):
            left = self.analyse(node.left)
            right = self.analyse(node.comparators[0])

            if not left.is_compatible(right):
                raise TypeError(f"Cannot compare {left} with {right}")

            node.inferred_type = BOOL
            return BOOL

        elif isinstance(node, FunctionDef):
            self.symbols.define(node.name, "function")
            
            #self.symbols.enter_scope() # lets just pretend this exists
            for arg in node.args:
                self.symbols.define(arg, UNKNOWN)
            for stmt in node.body:
                self.analyse(stmt)
            #self.symbols.exit_scope()
        
        else:
            return None