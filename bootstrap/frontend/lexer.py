from bootstrap.frontend.token_maps import *
from bootstrap.frontend.token import Token
from bootstrap.frontend.token_types import *
from bootstrap.exceptions import *

class Lexer:
    def __init__(self, text):
        self.text = text
        self.line = 1
        self.col = 1
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None
    
    def advance(self):
        if self.current_char == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        
        self.pos += 1
        
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
        else:
            self.current_char = None
    
    def skip_whitespace(self):
        while self.current_char and self.current_char in " \t":
            self.advance()
    
    def peek(self):
        if self.pos + 1 < len(self.text):
            return self.text[self.pos + 1]
        return None
    
    # had to crack this like the alan turing cracked cyphertext
    def number(self):
        start_line = self.line
        start_col = self.col
        num_str = ""
        dot_count = 0

        while self.current_char and self.current_char in "0123456789.":
            if self.current_char == ".":
                dot_count += 1
                # Critical: if this is the first dot, peek ahead
                if dot_count == 1:
                    next_char = self.peek()
                    # If we see . followed by another . do NOT consume this dot as part of number
                    if next_char == ".":
                        break  # leave the .. for the range rule
                    # Optional: also block trailing dot with no digit after (like 42.)
                    if next_char is None or not next_char.isdigit():
                        break

            num_str += self.current_char
            self.advance()

        if not num_str:
            raise LexerError(
                message=f"Illegal character: {self.current_char!r}", # !r forces __repr__
                token=Token(TokenType.ILLEGAL, self.current_char, self.line, self.col)
            )

        if dot_count == 0:
            return Token(TokenType.INT, int(num_str), line=start_line, column=start_col)
        elif dot_count == 1 and num_str[-1] != ".":
            return Token(TokenType.FLOAT, float(num_str), line=start_line, column=start_col)
        else:
            raise LexerError(
                message=f"Illegal character: {self.current_char!r}",
                token=Token(TokenType.ILLEGAL, self.current_char, self.line, self.col)
            )
    
    def string(self):
        start_line = self.line
        start_col = self.col
        string_val = ""
        quote_char = self.current_char
        self.advance() # skip opening quote
        
        while self.current_char and self.current_char != quote_char:
            string_val += self.current_char
            self.advance()
        
        self.advance()
        
        return Token(TokenType.STRING, string_val, line=start_line, column=start_col)
    
    def name(self):
        start_line = self.line
        start_col = self.col
        name_str = ""

        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            name_str += self.current_char
            self.advance()

        tok_type = KEYWORDS.get(name_str, TokenType.NAME)
        value = name_str if tok_type == TokenType.NAME else None
        tok = Token(tok_type, value, line=start_line, column=start_col)
        
        return tok
    
    def get_tokens(self):
        tokens = []
        
        while self.current_char is not None:
            if self.current_char == "\n":
                self.advance()
                continue
            
            elif self.current_char.isspace():
                self.skip_whitespace()
            
            elif self.current_char == "!" and self.peek() == "=":
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.NE, line=start_line, column=start_col))
            elif self.current_char == "=" and self.peek() == "=":
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.EE, line=start_line, column=start_col))
            elif self.current_char == "<" and self.peek() == "=":
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.LE, line=start_line, column=start_col))
            elif self.current_char == ">" and self.peek() == "=":
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.GE, line=start_line, column=start_col))
            elif self.current_char == "." and self.peek() == ".": # range
                start_line = self.line
                start_col = self.col
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.RANGE, line=start_line, column=start_col))
            
            elif self.current_char == ">":
                start_line = self.line
                start_col = self.col
                self.advance()
                tokens.append(Token(TokenType.GREATER, line=start_line, column=start_col))
            elif self.current_char == "<":
                start_line = self.line
                start_col = self.col
                self.advance()
                tokens.append(Token(TokenType.LESS, line=start_line, column=start_col))
            
            elif self.current_char in SINGLE_CHAR_TOKENS:
                start_line = self.line
                start_col = self.col
                tok_type = SINGLE_CHAR_TOKENS[self.current_char]
                tokens.append(Token(tok_type, line=start_line, column=start_col))
                self.advance()
            
            elif self.current_char.isdigit():
                tokens.append(self.number())
            
            elif self.current_char.isalpha() or self.current_char == "_":
                tokens.append(self.name())
            
            elif self.current_char in "\"'":
                tokens.append(self.string())
            
            else:
                raise LexerError(
                    message=f"Illegal character: {self.current_char!r}",
                    token=Token(TokenType.ILLEGAL, self.current_char, self.line, self.col)
                )
        
        tokens.append(Token(TokenType.EOF))
        return tokens