from src.semantic.types import *
from src.frontend.ast_nodes import *
from src.semantic.symbol_table import *
from src.exceptions import *
from src.runtime.builtins_registry import BUILTINS

# message for future-josh
#  this is going to be the most confusing, awful, horrid-looking code you have ever seen,
#  so dont even bother trying to debug this pile of horse-doodoo

# future-josh here, i have to debug this now...
# future-future-josh here, its currently 1:37am, and i am refactoring 2085 lines of goddamn code

class Analyser():
    def __init__(self, symbols):
        self.symbols: SymbolTable = symbols
        self.current_function = None
    
    def analyse(self, node):
        if isinstance(node, Module):
            for stmt in node.body:
                self.analyse(stmt)
        
        elif isinstance(node, Call):
            func_name = node.func.id
            if func_name in BUILTINS:
                for arg in node.args:
                    self.analyse(arg)
                return None
            
            func_name = node.func.id
            
            if not self.symbols.exists(func_name):
                suggestion = self.symbols.closest_match(func_name)
                hint = f" Did you mean '{suggestion}'?" if suggestion else ""
                raise UndefinedVariableError(
                    message=f"Undefined function '{func_name}'.{hint}",
                    token=node.func
                )
            
            sym = self.symbols.get(func_name)
            if sym["type"] != "function":
                raise TypeError(
                    message=f"'{func_name}' is not a function",
                    token=node.func
                )
            
            expected = sym.get("param_count")
            actual = len(node.args)
            if expected is not None and actual != expected:
                raise TypeError(
                    message=f"Function '{func_name}' expected {expected} argument(s), but {len(node.args)} given",
                    token=node.func
                )
            
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
                suggestion = self.symbols.closest_match(node.id)
                hint = f" Did you mean '{suggestion}'?" if suggestion else ""
                raise UndefinedVariableError(
                    message=f"Undefined variable '{node.id}'.{hint}",
                    token=node
                )
            
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
                raise TypeError(
                    message=f"Operator '{node.op}' not supported between {left} and {right}",
                    token=node
                )

            node.inferred_type = left
            return left
        
        elif isinstance(node, If):
            test_type = self.analyse(node.test)
            if test_type not in (BOOL, UNKNOWN) and test_type is not None:
                raise TypeError(
                    message="If condition must be boolean",
                    token=node
                )

            for stmt in node.body:
                self.analyse(stmt)

            if node.orelse:
                for stmt in node.orelse:
                    self.analyse(stmt)
        
        elif isinstance(node, Compare):
            left = self.analyse(node.left)
            right = self.analyse(node.comparators[0])

            if not left.is_compatible(right):
                raise TypeError(
                    message=f"Cannot compare {left} with {right}",
                    token=node
                )

            node.inferred_type = BOOL
            return BOOL

        # here be dragons, lets hope it works
        elif isinstance(node, FunctionDef):
            self.symbols.define(node.name, {
                "type": "function",
                "param_count": len(node.args),
                "params": node.args
            })
            
            self.symbols.enter_scope()
            old_fn = self.current_function
            self.current_function = node

            for arg in node.args:
                self.symbols.define(arg, UNKNOWN)

            for stmt in node.body.statements:
                self.analyse(stmt)

            self.current_function = old_fn
            self.symbols.exit_scope()
        
        elif isinstance(node, Return):
            if self.current_function is None:
                raise SemanticError(
                    message="Return outside function",
                    token= node
                )

            if node.value:
                return_type = self.analyse(node.value)
            else:
                return_type = NUMBER  # your default implicit return type

            return return_type
        
        elif isinstance(node, While):
            test_type = self.analyse(node.test)
            if test_type not in (BOOL, UNKNOWN) and test_type is not None:
                raise TypeError(
                    message="While condition must be boolean",
                    token=node
                )
            
            for stmt in node.body:
                self.analyse(stmt)
        
        elif isinstance(node, For):
            start_type = self.analyse(node.start)
            end_type = self.analyse(node.end)

            if start_type != NUMBER or end_type != NUMBER:
                raise TypeError(
                    message="For loop start and end must be numbers",
                    token=node
                )

            self.symbols.define(node.target.id, NUMBER)

            for stmt in node.body:
                self.analyse(stmt)
        
        else:
            return None