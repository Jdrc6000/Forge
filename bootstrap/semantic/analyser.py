from bootstrap.semantic.types import *
from bootstrap.frontend.ast_nodes import *
from bootstrap.semantic.symbol_table import *
from bootstrap.exceptions import *
from bootstrap.runtime.builtins_registry import BUILTINS

# message for future-josh
#  this is going to be the most confusing, awful, horrid-looking code you have ever seen,
#  so dont even bother trying to debug this pile of horse-doodoo

# future-josh here, i have to debug this now...
# future-future-josh here, its currently 1:37am, and i am refactoring 2085 lines of goddamn code
# future-future-future-josh here, its currently 1:33am on a wednesday, and the code base has grown to 2800 lines of bloody code

class Analyser:
    def __init__(self, symbols):
        self.symbols: SymbolTable = symbols
        self.current_function = None
        self.current_struct_fields = None
        self.loop_depth = 0
    
    def analyse(self, node):
        if isinstance(node, Module):
            for stmt in node.body:
                self.analyse(stmt)
        
        elif isinstance(node, Call):
            func_name = node.func.id
            if func_name in BUILTINS:
                for arg in node.args:
                    self.analyse(arg)
                return UNKNOWN
            
            # check if its a struct constructor
            if self.symbols.exists(func_name):
                sym = self.symbols.get(func_name)
                if sym["type"] == "struct":
                    if len(node.args) != sym["field_count"]:
                        raise TypeError(
                            message=f"Struct '{func_name}' has {sym["field_count"]} fields, got {len(node.args)}",
                            token=node.func
                        )
                    
                    for arg in node.args:
                        self.analyse(arg)
                    
                    node.__class__ = StructLiteral
                    node.name = func_name
                    return UNKNOWN
            
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
            
            return UNKNOWN
        
        elif isinstance(node, Attribute):
            self.analyse(node.obj)
            return UNKNOWN
        
        elif isinstance(node, MethodCall):
            self.analyse(node.obj)
            for arg in node.args:
                self.analyse(arg)
            return UNKNOWN
        
        # unused?
        # no past-josh... if an expression node occurs, it just passes straight through since its a wrapper
        elif isinstance(node, Expr):
            self.analyse(node.value)
        
        elif isinstance(node, Assign):
            value_type = self.analyse(node.value)
            self.symbols.define(node.target.id, value_type)
        
        elif isinstance(node, Name):
            if not self.symbols.exists(node.id):
                if self.current_struct_fields and node.id in self.current_struct_fields:
                    return UNKNOWN
                
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
            
            self.loop_depth += 1
            for stmt in node.body:
                self.analyse(stmt)
            self.loop_depth -= 1
        
        elif isinstance(node, For):
            start_type = self.analyse(node.start)
            end_type = self.analyse(node.end)

            if start_type != NUMBER or end_type != NUMBER:
                raise TypeError(
                    message="For loop start and end must be numbers",
                    token=node
                )

            self.symbols.define(node.target.id, NUMBER)

            self.loop_depth += 1
            for stmt in node.body:
                self.analyse(stmt)
            self.loop_depth -= 1
        
        elif isinstance(node, Break):
            if self.loop_depth == 0:
                raise SemanticError(
                    message="'break' outside of loop",
                    token=node
                )
        elif isinstance(node, Continue):
            if self.loop_depth == 0:
                raise SemanticError(
                    message="'continue' outside of loop",
                    token=node
                )
        
        elif isinstance(node, List):
            element_types = [self.analyse(element) for element in node.elements]
            
            if element_types and all(t == element_types[0] for t in element_types):
                node.inferred_type = ListType(element_types[0])
                return ListType(element_types[0])
            
            node.inferred_type = ListType(UNKNOWN)
            return ListType(UNKNOWN)
        
        elif isinstance(node, StructDef):
            self.symbols.define(node.name, {
                "type": "struct",
                "fields": node.fields,
                "field_count": len(node.fields),
                "methods": [m.name for m in node.methods]
            })
            
            for method in node.methods:
                self.symbols.enter_scope()
                self.symbols.define("self", UNKNOWN)
                for arg in method.args:
                    self.symbols.define(arg, UNKNOWN)
                old_fn = self.current_function
                old_fields = self.current_struct_fields
                self.current_function = method
                self.current_struct_fields = node.fields
                stmts = method.body.statements if hasattr(method.body, "statements") else method.body
                for stmt in stmts:
                    self.analyse(stmt)
                self.current_function = old_fn
                self.current_struct_fields = old_fields
                self.symbols.exit_scope()
        
        else:
            return None