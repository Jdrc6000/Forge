from src.frontend.tokens import *
from src.frontend.ast_nodes import *

class Parser():
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
    
    def advance(self):
        self.pos += 1
        
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token("EOF")
    
    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None
    
    def skip_newlines(self):
        while self.current_token.type == "NEWLINE":
            self.advance()
    
    def parse(self):
        body = []

        while self.current_token.type != "EOF":
            self.skip_newlines()
            if self.current_token.type == "EOF":
                break
            body.append(self.statement())

        return Module(body)
    
    def statement(self):
        if self.current_token.type == "PRINT":
            return self.parse_print()
        elif self.current_token.type == "IF":
            return self.parse_if()
        elif self.current_token.type == "NAME":
            if self.peek() and self.peek().type == "LPAREN":
                return self.parse_call()
            elif self.peek() and self.peek().type == "EQ":
                return self.parse_assign()
            else:
                return Expr(Name(self.current_token.value))
        elif self.current_token.type == "FN":
            return self.parse_function()
        elif self.current_token.type == "WHILE":
            return self.parse_while()
        elif self.current_token.type == "FOR":
            return self.parse_for()
        elif self.current_token.type == "RETURN":
            return self.parse_return()
        else:
            return Expr(self.parse_expr())
    
    def parse_print(self):
        # CONSUME
        self.advance()
        if self.current_token.type != "LPAREN":
            raise Exception("Expected '(' after print")
        self.advance()
        
        expr_node = self.parse_expr()
        
        if self.current_token.type != "RPAREN":
            raise Exception("Expected ')' after print argument")
        self.advance()
        
        return Call(
            func=Name("print"), # because it makes the interpreter happy
            args=[expr_node]
        )
    
    def parse_if(self):
        self.advance()  # skip 'if'
        test = self.parse_expr()

        if self.current_token.type != "COLON":
            raise Exception("Expected ':' after if condition")
        self.advance()

        if self.current_token.type != "NEWLINE":
            raise Exception("Expected newline after ':'")
        self.advance()

        if self.current_token.type != "INDENT":
            raise Exception("Expected indent")
        self.advance()

        body = []

        while True:
            self.skip_newlines()
            if self.current_token.type == "DEDENT":
                break
            body.append(self.statement())

        if self.current_token.type == "DEDENT" and self.peek() and self.peek().type == "ELSE":
            self.advance()      # DEDENT
            self.advance()      # ELSE

            if self.current_token.type != "COLON":
                raise Exception("Expected ':' after else")
            self.advance()

            if self.current_token.type != "NEWLINE":
                raise Exception("Expected newline after ':'")
            self.advance()

            if self.current_token.type != "INDENT":
                raise Exception("Expected indent in else block")
            self.advance()  # consume INDENT

            else_body = []
            while True:
                self.skip_newlines()
                if self.current_token.type == "DEDENT":
                    break
                else_body.append(self.statement())
            self.advance()  # consume DEDENT at end of else
            return If(test, body, else_body)
        else:
            self.advance()  # consume DEDENT
            return If(test, body)
    
    def parse_assign(self):
        name_token = self.current_token
        self.advance()
        
        if self.current_token.type != "EQ":
            raise Exception("Expected '=' after variable name")
        self.advance()
        
        value_node = self.parse_expr()
        
        return Assign(
            target=Name(name_token.value),
            value=value_node
        )
    
    def parse_comparison(self):
        left = self.parse_binop()
        comparators = []
        ops = []

        while self.current_token.type in ("EE","NE","LESS","GREATER","LE","GE"):
            ops.append(self.current_token.type)
            self.advance()
            comparators.append(self.parse_binop())

        if ops:
            # adjust AST if needed
            return Compare(left, ops[0], comparators)

        return left
    
    def parse_logic_or(self):
        left = self.parse_logic_and()
        
        while self.current_token.type == "OR":
            self.advance()
            right = self.parse_logic_and()
            left = BinOp(left, "or", right)
        
        return left

    def parse_logic_and(self):
        left = self.parse_comparison()
        
        while self.current_token.type == "AND":
            self.advance()
            right = self.parse_comparison()
            left = BinOp(left, "and", right)
        
        return left
    
    # why?
    #  for hotswapping past-josh, obviously...
    def parse_expr(self):
        return self.parse_logic_or()
    
    def parse_binop(self, min_prec=0):
        left = self.parse_unary()
        
        while True:
            op_token = self.current_token
            
            if op_token.type in ("PLUS", "MINUS", "MUL", "DIV", "POW"):
                prec = self.get_precedence(op_token)
                
                if prec < min_prec:
                    break
                self.advance()
                
                right = self.parse_binop(prec+1)
                left = BinOp(
                    left=left,
                    op=self.token_to_op(op_token),
                    right=right
                )

            else:
                break
        
        return left
    
    def parse_unary(self):
        tok = self.current_token
        if tok.type in ("PLUS", "MINUS"):
            self.advance()
            return UnOp(op=self.token_to_op(tok), operand=self.parse_unary())
        elif tok.type == "NOT":
            self.advance()
            return UnOp(op="not", operand=self.parse_unary())
        else:
            return self.parse_primary()
    
    def parse_primary(self):
        tok = self.current_token
        
        if tok.type == "INT" or tok.type == "FLOAT":
            self.advance()
            return Constant(tok.value)
        
        elif tok.type == "NAME":
            self.advance()
            node = Name(tok.value)

            # handle call syntax
            if self.current_token.type == "LPAREN":
                self.advance()  # skip '('
                args = []

                if self.current_token.type != "RPAREN":
                    while True:
                        args.append(self.parse_expr())
                        if self.current_token.type == "COMMA":
                            self.advance()
                        elif self.current_token.type == "RPAREN":
                            break
                        else:
                            raise Exception("Expected ',' or ')' in argument list")

                self.advance()  # skip ')'
                return Call(node, args)

            return node
        
        elif tok.type == "NAME":
            self.advance()
            return Name(tok.value)

        elif tok.type == "LPAREN":
            self.advance()
            if self.current_token.type == "RPAREN":
                expr = Constant(None)
            else:
                expr = self.parse_expr()
            
            if self.current_token.type != "RPAREN":
                raise Exception("Expected ')' after expression")
            self.advance()
            return expr
        
        elif tok.type == "TRUE":
            self.advance()
            return Constant(True)

        elif tok.type == "FALSE":
            self.advance()
            return Constant(False)
        
        else:
            raise Exception(f"Unexpected token: {tok}")
    
    def parse_function(self):
        self.advance() # skip fn
        
        if self.current_token.type != "NAME":
            raise Exception("Expected function name")
        func_name = self.current_token.value
        self.advance()
        
        if self.current_token.type != "LPAREN":
            raise Exception("Expected '(' after function name")
        self.advance()  # skip '('

        # parse argument names (can be empty)
        args = []
        if self.current_token.type != "RPAREN":
            while True:
                if self.current_token.type != "NAME":
                    raise Exception("Expected argument name")
                args.append(self.current_token.value)
                self.advance()
                if self.current_token.type == "RPAREN":
                    break
                elif self.current_token.type == "COMMA":
                    self.advance()
                else:
                    raise Exception("Expected ',' or ')' in argument list")

        self.advance()  # skip )
        
        if self.current_token.type != "COLON":
            raise Exception("Expected ':' after function header")
        self.advance()
        
        if self.current_token.type != "NEWLINE":
            raise Exception("Expected newline after ':'")
        self.advance()
        
        if self.current_token.type != "INDENT":
            raise Exception("Expected indent in function body")
        self.advance()
        
        body = []
        while self.current_token.type != "DEDENT":
            self.skip_newlines()
            if self.current_token.type == "DEDENT":
                break
            body.append(self.statement())
        
        self.advance()
        return FunctionDef(func_name, args, body)
    
    def parse_while(self):
        self.advance()  # skip 'while'
        test = self.parse_expr()

        if self.current_token.type != "COLON":
            raise Exception("Expected ':' after while condition")
        self.advance()

        if self.current_token.type != "NEWLINE":
            raise Exception("Expected newline after ':'")
        self.advance()

        if self.current_token.type != "INDENT":
            raise Exception("Expected indent in while body")
        self.advance()

        body = []
        while self.current_token.type != "DEDENT":
            self.skip_newlines()
            if self.current_token.type == "DEDENT":
                break
            body.append(self.statement())

        self.advance()  # consume DEDENT
        return While(test, body)
    
    def parse_call(self):
        func_name = self.current_token.value
        self.advance()  # skip function name

        if self.current_token.type != "LPAREN":
            raise Exception("Expected '(' in function call")
        self.advance()  # skip '('

        args = []
        if self.current_token.type != "RPAREN":
            while True:
                args.append(self.parse_expr())
                if self.current_token.type == "COMMA":
                    self.advance()
                elif self.current_token.type == "RPAREN":
                    break
                else:
                    raise Exception("Expected ',' or ')' in argument list")
        self.advance()  # skip ')'
        return Call(Name(func_name), args)

    def parse_for(self):
        self.advance()  # skip 'for'

        if self.current_token.type != "NAME":
            raise Exception("Expected loop variable name")
        loop_var = Name(self.current_token.value)
        self.advance()

        if self.current_token.type != "IN":
            raise Exception("Expected 'in' in for loop")
        self.advance()

        start = self.parse_expr()

        if self.current_token.type != "RANGE":
            raise Exception("Expected '..' in for loop")
        self.advance()

        end = self.parse_expr()

        if self.current_token.type != "COLON":
            raise Exception("Expected ':' after for header")
        self.advance()

        if self.current_token.type != "NEWLINE":
            raise Exception("Expected newline after ':'")
        self.advance()

        if self.current_token.type != "INDENT":
            raise Exception("Expected indent in for body")
        self.advance()

        body = []
        while self.current_token.type != "DEDENT":
            self.skip_newlines()
            if self.current_token.type == "DEDENT":
                break
            body.append(self.statement())

        self.advance()  # consume DEDENT
        return For(loop_var, start, end, body)

    def parse_return(self):
        self.advance()  # consume 'return'

        # return with no value
        if self.current_token.type in ("NEWLINE", "DEDENT"):
            return Return(None)

        value = self.parse_expr()
        return Return(value)
    
    def token_to_op(self, token):
        mapping = {
            "PLUS": "+",
            "MINUS": "-",
            "MUL": "*",
            "DIV": "/",
            "POW": "^"
        }
        
        return mapping[token.type]
    
    # if i have to spell "precedence" again
    # i will literally light my codebase on fire
    def get_precedence(self, token):
        prec = {
            "PLUS": 1,
            "MINUS": 1,
            "MUL": 2,
            "DIV": 2,
            "POW": 3
        }
        
        return prec[token.type]
    
    # my beloved dump function, i love this piece of scrap
    def dump(self, node, indent=0):
        pad = "  " * indent

        if isinstance(node, Module):
            print(f"{pad}Module")
            for stmt in node.body:
                self.dump(stmt, indent + 1)
        
        elif isinstance(node, Expr):
            print(f"{pad}Expr")
            self.dump(node.value, indent + 1)
        
        elif isinstance(node, Call):
            print(f"{pad}Call")
            self.dump(node.func, indent + 1)
            for arg in node.args:
                self.dump(arg, indent + 1)
        
        elif isinstance(node, Name):
            print(f"{pad}Name({node.id})")
        
        elif isinstance(node, Constant):
            print(f"{pad}Constant({node.value})")
        
        elif isinstance(node, Assign):
            print(f"{pad}Assign")
            self.dump(node.target, indent + 1)
            self.dump(node.value, indent + 1)
        
        elif isinstance(node, BinOp):
            print(f"{pad}BinaryOp({node.op})")
            self.dump(node.left, indent + 1)
            self.dump(node.right, indent + 1)
        
        elif isinstance(node, UnOp):
            print(f"{pad}UnaryOp({node.op})")
            self.dump(node.operand, indent + 1)
        
        elif isinstance(node, If):
            print(f"{pad}If")
            self.dump(node.test, indent + 1)
            print(f"{pad}  Body:")
            for line in node.body:
                self.dump(line, indent + 2)
            if node.orelse:
                print(f"{pad}  Else:")
                for line in node.orelse:
                    self.dump(line, indent + 2)
        
        elif isinstance(node, Compare):
            print(f"{pad}Compare({node.op})")
            self.dump(node.left, indent + 1)
            for comparator in node.comparators:
                self.dump(comparator, indent + 1)
        
        elif isinstance(node, FunctionDef):
            print(f"{pad}FunctionDef({node.name})")
            print(f"{pad}  Args:")
            for arg in node.args:
                self.dump(arg, indent + 2)
            
            print(f"{pad}  Body:")
            for something in node.body: # chat remind me to change this
                self.dump(something, indent + 2)
        
        elif isinstance(node, While):
            print(f"{pad}While")
            self.dump(node.test, indent + 1)
            
            print(f"{pad}  Body:")
            for something in node.body: # chat also remind me to change this
                self.dump(something, indent + 2)
        
        elif isinstance(node, For):
            print(f"{pad}For({node.target.id})")
            self.dump(node.start, indent + 1)
            self.dump(node.end, indent + 1)
            
            print(f"{pad}  Body:")
            for something in node.body: # chat also also remind me to change this
                self.dump(something, indent + 2)
        
        else:
            print(f"{pad}{node}")