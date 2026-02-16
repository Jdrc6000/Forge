from src.frontend.token_maps import *
from src.frontend.token import Token
from src.frontend.token_types import *

class Lexer():
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_char = self.text[self.pos] if self.text else None
        self.indents = [0]
    
    def advance(self):
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
    
    def handle_indentation(self, tokens):
        count = 0
        while self.current_char == " ":
            count += 1
            self.advance()

        if self.current_char == "\n":
            return

        if count > self.indents[-1]:
            self.indents.append(count)
            tokens.append(Token(TokenType.INDENT))
        else:
            while count < self.indents[-1]:
                self.indents.pop()
                tokens.append(Token(TokenType.DEDENT))
    
    # had to crack this like the alan turing cracked cyphertext
    def number(self):
        num_str = ""
        dot_count = 0
        start_pos = self.pos  # optional: for better error messages

        while self.current_char and self.current_char in "0123456789.":
            if self.current_char == ".":
                dot_count += 1
                # Critical: if this is the first dot, peek ahead
                if dot_count == 1:
                    next_char = self.peek()
                    next_next_char = self.text[self.pos + 2] if self.pos + 2 < len(self.text) else None
                    # If we see . followed by another . → do NOT consume this dot as part of number
                    if next_char == ".":
                        break  # leave the .. for the range rule
                    # Optional: also block trailing dot with no digit after (like 42.)
                    if next_char is None or not next_char.isdigit():
                        break

            num_str += self.current_char
            self.advance()

        if not num_str:
            raise Exception("Expected number")

        if dot_count == 0:
            return Token(TokenType.INT, int(num_str))
        elif dot_count == 1 and num_str[-1] != ".":
            return Token(TokenType.FLOAT, float(num_str))
        else:
            # Optional: give better position info
            raise Exception(f"Invalid number format near position {start_pos}: '{num_str}'")
    
    def string(self):
        string_val = ""
        quote_char = self.current_char
        self.advance() # skip opening quote
        
        while self.current_char and self.current_char != quote_char:
            string_val += self.current_char
            self.advance()
        
        self.advance()
        
        return Token(TokenType.STRING, string_val)
    
    def name(self):
        name_str = ""

        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            name_str += self.current_char
            self.advance()

        tok_type = KEYWORDS.get(name_str, TokenType.NAME)

        if tok_type == TokenType.NAME:
            return Token(tok_type, name_str)
        else:
            return Token(tok_type)
    
    def get_tokens(self):
        tokens = []
        
        while self.current_char is not None:
            if self.current_char == "\n":
                self.advance()
                tokens.append(Token(TokenType.NEWLINE))
                self.handle_indentation(tokens)
            
            elif self.current_char.isspace():
                self.skip_whitespace()
            
            elif self.current_char == "!" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.NE))
            elif self.current_char == "=" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.EE))
            elif self.current_char == "<" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.LE))
            elif self.current_char == ">" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.GE))
            elif self.current_char == ">":
                self.advance()
                tokens.append(Token(TokenType.GREATER))
            elif self.current_char == "<":
                self.advance()
                tokens.append(Token(TokenType.LESS))
            
            elif self.current_char == "." and self.peek() == ".":
                self.advance()
                self.advance()
                tokens.append(Token(TokenType.RANGE))
            
            elif self.current_char in SINGLE_CHAR_TOKENS:
                tok_type = SINGLE_CHAR_TOKENS[self.current_char]
                tokens.append(Token(tok_type))
                self.advance()
            
            elif self.current_char.isdigit():
                tokens.append(self.number())
            
            elif self.current_char.isalpha() or self.current_char == "_":
                tokens.append(self.name())
            
            elif self.current_char in "\"'":
                tokens.append(self.string())
            
            else:
                raise Exception(f"Illegal character: {self.current_char}")
        
        while len(self.indents) > 1:
            self.indents.pop()
            tokens.append(Token(TokenType.DEDENT))
        
        tokens.append(Token(TokenType.EOF))
        return tokens