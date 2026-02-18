from src.frontend.token_types import *
from src.frontend.ast_nodes import *
from src.frontend.token import Token
from src.exceptions import *

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
    
    # an awesome helper function that parses an arg list that i totally wrote myself
    def _parse_arg_list(self):
        args = []
        
        if self.current_token.type != TokenType.RPAREN:
            while True:
                args.append(self.parse_expr())
                
                if self.current_token.type == TokenType.COMMA:
                    self.advance()
                
                elif self.current_token.type == TokenType.RPAREN:
                    break
                
                else:
                    raise ParseError(
                        message="Expected ',' or ')' in argument list",
                        line=self.current_token.line,
                        column=self.current_token.column
                    )
        
        self.advance()  # consume ')'
        return args
    
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
            return self.parse_block()
        
        elif self.current_token.type == TokenType.IF:
            return self.parse_if()
        
        elif self.current_token.type == TokenType.NAME:
            if self.peek() and self.peek().type == TokenType.LPAREN:
                return self.parse_call()
            elif self.peek() and self.peek().type == TokenType.EQ:
                return self.parse_assign()
            else:
                return Expr(
                    value=Name(
                        id=self.current_token.value,
                        line=self.current_token.line,
                        column=self.current_token.column
                    ),
                    line=self.current_token.line,
                    column=self.current_token.column
                )
        
        elif self.current_token.type == TokenType.FN:
            return self.parse_function()
        
        elif self.current_token.type == TokenType.WHILE:
            return self.parse_while()
        
        elif self.current_token.type == TokenType.FOR:
            return self.parse_for()
        
        elif self.current_token.type == TokenType.RETURN:
            return self.parse_return()
        else:
            return Expr(
                value=self.parse_expr(),
                line=self.current_token.line,
                column=self.current_token.column
            )
    
    def parse_primary(self):
        tok = self.current_token
        
        if tok.type in (TokenType.INT, TokenType.FLOAT, TokenType.STRING):
            self.advance()
            node = Constant(
                value=tok.value,
                line=tok.line,
                column=tok.column
            )
        
        elif tok.type == TokenType.NAME:
            self.advance()
            node = Name(
                id=tok.value,
                line=tok.line,
                column=tok.column
            )

            # handle call syntax
            if self.current_token.type == TokenType.LPAREN:
                self.advance()
                args = self._parse_arg_list() # our hero in action
                node = Call(
                    func=node,
                    args=args,
                    line=tok.line,
                    column=tok.column
                )

        elif tok.type == TokenType.LPAREN:
            self.advance()
            if self.current_token.type == TokenType.RPAREN:
                node = Constant(None)
            else:
                node = self.parse_expr()
            
            if self.current_token.type != TokenType.RPAREN:
                raise ParseError(
                    message=f"Expected ')' after expression",
                    line=self.current_token.line,
                    column=self.current_token.column
                )
            
            self.advance()
        
        elif tok.type == TokenType.TRUE:
            self.advance()
            node = Constant(
                value=True,
                line=tok.line,
                column=tok.column
            )

        elif tok.type == TokenType.FALSE:
            self.advance()
            node = Constant(
                value=False,
                line=tok.line,
                column=tok.column
            )
        
        else:
            raise ParseError(
                message=f"Unexpected token: {tok}",
                line=self.current_token.line,
                column=self.current_token.column
            )
        
        # runs after primary, consumes .name + .name()
        while self.current_token.type == TokenType.DOT:
            dot_line = self.current_token.line
            dot_col = self.current_token.column
            self.advance()
            
            if self.current_token.type != TokenType.NAME:
                raise ParseError(
                    message="Expected attribute or method name after '.'",
                    line=self.current_token.line,
                    column=self.current_token.column
                )
            
            attr_tok = self.current_token
            self.advance() # eat the name
            
            if self.current_token.type == TokenType.LPAREN:
                self.advance() # eat '('
                args = self._parse_arg_list()
                node = MethodCall(
                    obj=node,
                    method=attr_tok.value,
                    args=args,
                    line=dot_line,
                    column=dot_col
                )
            
            else:
                node = Attribute(
                    obj=node,
                    attr=attr_tok.value,
                    line=dot_line,
                    column=dot_col
                )
        
        return node
    
    def parse_assign(self):
        name_token = self.current_token
        self.advance()
        
        if self.current_token.type != TokenType.EQ:
            raise ParseError(
                message=f"Expected '=' after variable name",
                line=name_token.line,
                column=name_token.column
            )
        self.advance()
        
        value_node = self.parse_expr()
        
        return Assign(
            target=Name(
                id=name_token.value,
                line=name_token.line,
                column=name_token.column
            ),
            value=value_node,
            line=name_token.line,
            column=name_token.column
        )
    
    def parse_comparison(self):
        comparision_token = self.current_token
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
            return Compare(
                left=left,
                op=ops,
                comparators=comparators,
                line=comparision_token.line,
                column=comparision_token.column
            )
        return left
    
    def parse_logic_or(self):
        left = self.parse_logic_and()
        
        while self.current_token.type == TokenType.OR:
            self.advance()
            right = self.parse_logic_and()
            left = BinOp(
                left=left,
                op="or",
                right=right,
                line=self.current_token.line,
                column=self.current_token.column
            )
        
        return left

    def parse_logic_and(self):
        left = self.parse_comparison()
        
        while self.current_token.type == TokenType.AND:
            self.advance()
            right = self.parse_comparison()
            left = BinOp(
                left=left,
                op="and",
                right=right,
                line=self.current_token.line,
                column=self.current_token.column
            )
        
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
                    right=right,
                    line=self.current_token.line,
                    column=self.current_token.column
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
            return UnOp(
                op="not",
                operand=self.parse_unary(),
                line=tok.line,
                column=tok.column
            )
        
        else:
            return self.parse_primary()
    
    def parse_function(self):
        function_token = self.current_token
        self.advance()  # consume 'fn'
        if self.current_token.type != TokenType.NAME:
            raise ParseError(
                message=f"Expected function name",
                line=function_token.line,
                column=function_token.column
            )
        func_name = self.current_token.value
        self.advance()

        if self.current_token.type != TokenType.LPAREN:
            raise ParseError(
                message=f"Expected '(' after function name",
                line=self.current_token.line,
                column=self.current_token.column
            )
        self.advance()

        args = []
        if self.current_token.type != TokenType.RPAREN:
            while True:
                if self.current_token.type != TokenType.NAME:
                    raise ParseError(
                        message=f"Expected argument name",
                        line=self.current_token.line,
                        column=self.current_token.column
                    )
                
                args.append(self.current_token.value)
                self.advance()
                
                if self.current_token.type == TokenType.RPAREN:
                    break
                
                elif self.current_token.type == TokenType.COMMA:
                    self.advance()
                
                else:
                    raise ParseError(
                        message=f"Expected ',' or ')'",
                        line=self.current_token.line,
                        column=self.current_token.column
                    )

        self.advance()  # consume ')'

        body = self.parse_block()

        return FunctionDef(
            name=func_name,
            args=args,
            body=body,
            line=function_token.line,
            column=function_token.column
        )
    
    def parse_if(self):
        if_token = self.current_token
        self.advance()  # skip 'if'
        test = self.parse_expr()
        body = self.parse_block()
        orelse = None
        if self.current_token.type == TokenType.ELSE:
            self.advance()  # skip 'else'
            
            if self.current_token.type == TokenType.IF:
                # recursion!!! (else if { ... }) just becomes a new if branch
                orelse = [self.parse_if()]
            
            else:
                if self.current_token.type != TokenType.LBRACE:
                    raise ParseError(
                        message="Expected '{' or 'if' after 'else'",
                        line=self.current_token.line,
                        column=self.current_token.column
                    )
                # else { ... }
                orelse = self.parse_block()

        return If(
            test=test,
            body=body,
            orelse=orelse,
            line=if_token.line,
            column=if_token.column
        )
    
    def parse_while(self):
        while_token = self.current_token
        self.advance()  # skip 'while'
        test = self.parse_expr()
        body = self.parse_block()
        return While(
            test=test,
            body=body,
            line=while_token.line,
            column=while_token.column
        )
    
    def parse_call(self):
        func_token = self.current_token
        self.advance()  # skip function name

        if self.current_token.type != TokenType.LPAREN:
            raise ParseError(
                message=f"Expected '(' in function call",
                line=self.current_token.line,
                column=self.current_token.column
            )
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
                    raise ParseError(
                        message="Expected ',' or ')' in argument list",
                        line=self.current_token.line,
                        column=self.current_token.column
                    )
        
        self.advance()  # skip ')'
        return Call(
            func=Name(
                id=func_token.value,
                line=func_token.line,
                column=func_token.column
            ),
            args=args,
            line=func_token.line,
            column=func_token.column
        )

    def parse_for(self):
        for_token = self.current_token
        self.advance()  # skip 'for'

        if self.current_token.type != TokenType.NAME:
            raise ParseError(
                message=f"Expected loop variable name",
                line=self.current_token.line,
                column=self.current_token.column
            )
        loop_var = Name(
            id=self.current_token.value,
            line=self.current_token.line,
            column=self.current_token.column
        )
        self.advance()

        if self.current_token.type != TokenType.IN:
            raise ParseError(
                message=f"Expected 'in' in for loop",
                line=self.current_token.line,
                column=self.current_token.column
            )
        self.advance()

        start = self.parse_expr()

        if self.current_token.type != TokenType.RANGE:
            raise ParseError(
                message=f"Expected '..' in for loop",
                line=self.current_token.line,
                column=self.current_token.column
            )
        self.advance()

        end = self.parse_expr()
        body = self.parse_block()
        
        return For(
            target=loop_var,
            start=start,
            end=end,
            body=body,
            line=for_token.line,
            column=for_token.column
        )

    def parse_return(self):
        return_token = self.current_token
        self.advance()  # consume 'return'
        value = self.parse_expr()
        return Return(
            value=value,
            line=return_token.line,
            column=return_token.column
        )
    
    def parse_block(self):
        block_token = self.current_token
        
        if self.current_token.type != TokenType.LBRACE:
            raise ParseError(
                message="Expected '{' to start block",
                line=self.current_token.line,
                column=self.current_token.column
            )
        self.advance() # eat '{'
        
        body = []
        while self.current_token.type not in (TokenType.RBRACE, TokenType.EOF):
            stmt = self.statement()
            if stmt is not None: # future-proof - empty statements
                body.append(stmt)
        
        if self.current_token.type != TokenType.RBRACE:
            raise ParseError(
                message="Expected '}' to close block",
                line=self.current_token.line,
                column=self.current_token.column
            )
        self.advance() # eat '}'
        
        return Block(
            statements=body,
            line=block_token.line,
            column=block_token.column
        )
    
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
                    self.dump(node.orelse, indent + 2)
                
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
                print(f"{pad}   {arg}")
            
            print(f"{pad}  Body:")
            for stmt in node.body:
                self.dump(stmt, indent + 2)
        
        elif isinstance(node, While):
            print(f"{pad}While")
            self.dump(node.test, indent + 1)
            
            print(f"{pad}  Body:")
            for stmt in node.body:
                self.dump(stmt, indent + 2)
        
        elif isinstance(node, For):
            print(f"{pad}For({node.target.id})")
            self.dump(node.start, indent + 1)
            self.dump(node.end, indent + 1)
            
            print(f"{pad}  Body:")
            for stmt in node.body:
                self.dump(stmt, indent + 2)
        
        elif isinstance(node, Block):
            print(f"{pad}Block")
            for stmt in node:
                self.dump(stmt, indent + 1)
        
        elif isinstance(node, Return):
            print(f"{pad}Return")
            if node.value:
                self.dump(node.value, indent + 1)
        
        else:
            print(f"{pad}{node}")