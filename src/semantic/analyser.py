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
        self.current_function = None
    
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

        # here be dragons, lets hope it works
        elif isinstance(node, FunctionDef):
            self.symbols.define(node.name, "function")
            
            self.symbols.enter_scope()
            old_fn = self.current_function
            self.current_function = node

            for arg in node.args:
                self.symbols.define(arg, UNKNOWN)

            for stmt in node.body:
                self.analyse(stmt)

            self.current_function = old_fn
            self.symbols.exit_scope()
        
        elif isinstance(node, Return):
            if self.current_function is None:
                raise Exception("Return outside function")

            if node.value:
                return_type = self.analyse(node.value)
            else:
                return_type = NUMBER  # your default implicit return type

            return return_type
        
        elif isinstance(node, While):
            test_type = self.analyse(node.test)
            if test_type != BOOL:
                raise TypeError("While condition must be boolean")
            for stmt in node.body:
                self.analyse(stmt)
        
        elif isinstance(node, For):
            start_type = self.analyse(node.start)
            end_type = self.analyse(node.end)

            if start_type != NUMBER or end_type != NUMBER:
                raise TypeError("For loop start and end must be numbers")

            self.symbols.define(node.target.id, NUMBER)

            for stmt in node.body:
                self.analyse(stmt)
        
        else:
            return None