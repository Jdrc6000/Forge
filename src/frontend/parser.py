from src.frontend.token_types import *
from src.frontend.ast_nodes import *
from src.frontend.token import Token

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
            self.current_token = Token(TokenType.EOF)
    
    def peek(self):
        if self.pos + 1 < len(self.tokens):
            return self.tokens[self.pos + 1]
        return None
    
    # here lay our beloved skip_newlines function before we migrated to brace delimited blocks...
    
    def parse(self):
        body = []

        while self.current_token.type != TokenType.EOF:
            if self.current_token.type == TokenType.EOF:
                break
            body.append(self.statement())

        return Module(body)
    
    def statement(self):
        if self.current_token.type == TokenType.PRINT:
            return self.parse_print()
        
        elif self.current_token.type == TokenType.LBRACE:
            return Block(self.parse_block())
        
        elif self.current_token.type == TokenType.IF:
            return self.parse_if()
        
        elif self.current_token.type == TokenType.NAME:
            if self.peek() and self.peek().type == TokenType.LPAREN:
                return self.parse_call()
            elif self.peek() and self.peek().type == TokenType.EQ:
                return self.parse_assign()
            else:
                return Expr(Name(self.current_token.value))
        
        elif self.current_token.type == TokenType.FN:
            return self.parse_function()
        
        elif self.current_token.type == TokenType.WHILE:
            return self.parse_while()
        
        elif self.current_token.type == TokenType.FOR:
            return self.parse_for()
        
        elif self.current_token.type == TokenType.RETURN:
            return self.parse_return()
        else:
            return Expr(self.parse_expr())
    
    def parse_primary(self):
        tok = self.current_token
        
        if tok.type in (TokenType.INT, TokenType.FLOAT):
            self.advance()
            return Constant(tok.value)
        
        elif tok.type == TokenType.STRING:
            self.advance()
            return Constant(tok.value)
        
        elif tok.type == TokenType.NAME:
            self.advance()
            node = Name(tok.value)

            # handle call syntax
            if self.current_token.type == TokenType.LPAREN:
                self.advance()  # skip '('
                args = []

                if self.current_token.type != TokenType.RPAREN:
                    while True:
                        args.append(self.parse_expr())
                        if self.current_token.type == TokenType.COMMA:
                            self.advance()
                        elif self.current_token.type == TokenType.RPAREN:
                            break
                        else:
                            raise Exception("Expected ',' or ')' in argument list")

                self.advance()  # skip ')'
                return Call(node, args)

            return node

        elif tok.type == TokenType.LPAREN:
            self.advance()
            if self.current_token.type == TokenType.RPAREN:
                expr = Constant(None)
            else:
                expr = self.parse_expr()
            
            if self.current_token.type != TokenType.RPAREN:
                raise Exception("Expected ')' after expression")
            self.advance()
            return expr
        
        elif tok.type == TokenType.TRUE:
            self.advance()
            return Constant(True)

        elif tok.type == TokenType.FALSE:
            self.advance()
            return Constant(False)
        
        else:
            raise Exception(f"Unexpected token: {tok}")
    
    def parse_print(self):
        # CONSUME
        self.advance()
        if self.current_token.type != TokenType.LPAREN:
            raise Exception("Expected '(' after print")
        self.advance()
        
        expr_node = self.parse_expr()
        
        if self.current_token.type != TokenType.RPAREN:
            raise Exception("Expected ')' after print argument")
        self.advance()
        
        return Call(
            func=Name("print"), # because it makes the interpreter happy
            args=[expr_node]
        )
    
    def parse_assign(self):
        name_token = self.current_token
        self.advance()
        
        if self.current_token.type != TokenType.EQ:
            raise Exception("Expected '=' after variable name")
        self.advance()
        
        value_node = self.parse_expr()
        
        return Assign(
            target=Name(name_token.value),
            value=value_node
        )
    
    def parse_comparison(self):
        left = self.parse_binop()
        ops = []
        comparators = []
        while self.current_token.type in (
            TokenType.EE, TokenType.NE, TokenType.LESS,
            TokenType.GREATER, TokenType.LE, TokenType.GE
        ):
            # Store string operator instead of TokenType
            op_str = {
                TokenType.EE: "==",
                TokenType.NE: "!=",
                TokenType.LESS: "<",
                TokenType.GREATER: ">",
                TokenType.LE: "<=",
                TokenType.GE: ">=",
            }[self.current_token.type]
            ops.append(op_str)
            self.advance()
            comparators.append(self.parse_binop())

        if ops:
            return Compare(left, ops, comparators)
        return left
    
    def parse_logic_or(self):
        left = self.parse_logic_and()
        
        while self.current_token.type == TokenType.OR:
            self.advance()
            right = self.parse_logic_and()
            left = BinOp(left, "or", right)
        
        return left

    def parse_logic_and(self):
        left = self.parse_comparison()
        
        while self.current_token.type == TokenType.AND:
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
            
            if op_token.type in (
                TokenType.PLUS, TokenType.MINUS, TokenType.MUL,
                TokenType.DIV, TokenType.POW
            ):
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
        
        if tok.type in (TokenType.PLUS, TokenType.MINUS):
            self.advance()
            return UnOp(op=self.token_to_op(tok), operand=self.parse_unary())
        
        elif tok.type == TokenType.NOT:
            self.advance()
            return UnOp(op="not", operand=self.parse_unary())
        
        else:
            return self.parse_primary()
    
    def parse_function(self):
        self.advance()  # consume 'fn'
        if self.current_token.type != TokenType.NAME:
            raise Exception("Expected function name")
        func_name = self.current_token.value
        self.advance()

        if self.current_token.type != TokenType.LPAREN:
            raise Exception("Expected '(' after function name")
        self.advance()

        args = []
        if self.current_token.type != TokenType.RPAREN:
            while True:
                if self.current_token.type != TokenType.NAME:
                    raise Exception("Expected argument name")
                args.append(self.current_token.value)
                self.advance()
                if self.current_token.type == TokenType.RPAREN:
                    break
                elif self.current_token.type == TokenType.COMMA:
                    self.advance()
                else:
                    raise Exception("Expected ',' or ')'")

        self.advance()  # consume ')'

        body = self.parse_block()

        return FunctionDef(func_name, args, body)
    
    def parse_if(self):
        self.advance()  # skip 'if'
        test = self.parse_expr()
        body = self.parse_block().statements
        orelse = None
        if self.current_token.type == TokenType.ELSE:
            self.advance()  # skip 'else'
            
            if self.current_token.type == TokenType.IF:
                # recursion!!! (else if { ... }) just becomes a new if branch
                orelse = [self.parse_if()]
            
            else:
                if self.current_token.type != TokenType.LBRACE:
                    raise Exception("Expected '{' or 'if' after 'else'")
                # else { ... }
                orelse = self.parse_block().statements

        return If(test, body, orelse)
    
    def parse_while(self):
        self.advance()  # skip 'while'
        test = self.parse_expr()
        body = self.parse_block()
        return While(test, body)
    
    def parse_call(self):
        func_name = self.current_token.value
        self.advance()  # skip function name

        if self.current_token.type != TokenType.LPAREN:
            raise Exception("Expected '(' in function call")
        self.advance()  # skip '('

        args = []
        if self.current_token.type != TokenType.RPAREN:
            while True:
                args.append(self.parse_expr())
                if self.current_token.type == TokenType.COMMA:
                    self.advance()
                elif self.current_token.type == TokenType.RPAREN:
                    break
                else:
                    raise Exception("Expected ',' or ')' in argument list")
        
        self.advance()  # skip ')'
        return Call(Name(func_name), args)

    def parse_for(self):
        self.advance()  # skip 'for'

        if self.current_token.type != TokenType.NAME:
            raise Exception("Expected loop variable name")
        loop_var = Name(self.current_token.value)
        self.advance()

        if self.current_token.type != TokenType.IN:
            raise Exception("Expected 'in' in for loop")
        self.advance()

        start = self.parse_expr()

        if self.current_token.type != TokenType.RANGE:
            raise Exception("Expected '..' in for loop")
        self.advance()

        end = self.parse_expr()
        body = self.parse_block()
        
        return For(loop_var, start, end, body)

    def parse_return(self):
        self.advance()  # consume 'return'
        value = self.parse_expr()
        return Return(value)
    
    def parse_block(self):
        if self.current_token.type != TokenType.LBRACE:
            raise Exception("Expected '{' to start block")
        self.advance() # eat '{'
        
        body = []
        while self.current_token.type not in (TokenType.RBRACE, TokenType.EOF):
            stmt = self.statement()
            if stmt is not None: # future-proof - empty statements
                body.append(stmt)
        
        if self.current_token.type != TokenType.RBRACE:
            raise Exception("Expected '}' to close block")
        self.advance() # eat '}'
        
        return Block(body)
    
    def token_to_op(self, token):
        mapping = {
            TokenType.PLUS: "+",
            TokenType.MINUS: "-",
            TokenType.MUL: "*",
            TokenType.DIV: "/",
            TokenType.POW: "^"
        }
        
        return mapping[token.type]
    
    # if i have to spell "precedence" again
    # i will literally light my codebase on fire
    def get_precedence(self, token):
        prec = {
            TokenType.PLUS: 1,
            TokenType.MINUS: 1,
            TokenType.MUL: 2,
            TokenType.DIV: 2,
            TokenType.POW: 3
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
            for stmt in node.body:
                self.dump(stmt, indent + 2)
            
            if node.orelse:
                print(f"{pad}  Else:")
                if isinstance(node.orelse, If):
                    self.dump(node.orelse, If)
                
                else:
                    for stmt in node.orelse:
                        self.dump(stmt, indent + 2)
        
        elif isinstance(node, Compare):
            print(f"{pad}Compare( {' '.join(node.ops)} )")
            self.dump(node.left, indent + 1)
            for comp in node.comparators:
                self.dump(comp, indent + 1)
        
        elif isinstance(node, FunctionDef):
            print(f"{pad}FunctionDef({node.name})")
            print(f"{pad}  Args:")
            for arg in node.args:
                print(f"")
            
            print(f"{pad}  Body:")
            for stmt in node.body.statements:
                self.dump(stmt, indent + 2)
        
        elif isinstance(node, While):
            print(f"{pad}While")
            self.dump(node.test, indent + 1)
            
            print(f"{pad}  Body:")
            for stmt in node.body.statements:
                self.dump(stmt, indent + 2)
        
        elif isinstance(node, For):
            print(f"{pad}For({node.target.id})")
            self.dump(node.start, indent + 1)
            self.dump(node.end, indent + 1)
            
            print(f"{pad}  Body:")
            for stmt in node.body.statements:
                self.dump(stmt, indent + 2)
        
        elif isinstance(node, Block):
            print(f"{pad}Block")
            for stmt in node.statements:
                self.dump(stmt, indent + 1)
        
        else:
            print(f"{pad}{node}")