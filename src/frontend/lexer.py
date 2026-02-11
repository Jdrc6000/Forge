from src.frontend.tokens import *

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
            tokens.append(Token(tt_indent))
        else:
            while count < self.indents[-1]:
                self.indents.pop()
                tokens.append(Token(tt_dedent))
    
    # had to crack this like the alan turing cracked cyphertext
    def number(self):
        num_str = ""
        dot_count = 0
        
        while self.current_char and (self.current_char.isdigit() or self.current_char == "."):
            if self.current_char == ".":
                if dot_count == 1:
                    break
                
                dot_count += 1
                num_str += "."
            else:
                num_str += self.current_char
            
            self.advance()
        
        if dot_count == 0:
            return Token(tt_int, int(num_str))
        else:
            return Token(tt_float, float(num_str))
    
    def string(self):
        string_val = ""
        quote_char = self.current_char
        self.advance() # skip opening quote
        
        while self.current_char and self.current_char != quote_char:
            string_val += self.current_char
            self.advance()
        
        self.advance()
        
        return Token(tt_string, string_val)
    
    def name(self):
        name_str = ""

        while self.current_char and (self.current_char.isalnum() or self.current_char == "_"):
            name_str += self.current_char
            self.advance()

        tok_type = keywords.get(name_str, tt_name)

        if tok_type == tt_name:
            return Token(tok_type, name_str)
        else:
            return Token(tok_type)
    
    def get_tokens(self):
        tokens = []
        
        while self.current_char is not None:
            if self.current_char == "\n":
                self.advance()
                tokens.append(Token(tt_newline))
                self.handle_indentation(tokens)
            
            elif self.current_char.isspace():
                self.skip_whitespace()
            
            elif self.current_char == "!" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(tt_ne))
            elif self.current_char == "=" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(tt_ee))
            elif self.current_char == "<" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(tt_le))
            elif self.current_char == ">" and self.peek() == "=":
                self.advance()
                self.advance()
                tokens.append(Token(tt_ge))
            elif self.current_char == ">":
                self.advance()
                tokens.append(Token(tt_greater))
            elif self.current_char == "<":
                self.advance()
                tokens.append(Token(tt_less))
            
            elif self.current_char in single_char_tokens:
                tok_type = single_char_tokens[self.current_char]
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
            tokens.append(Token(tt_dedent))
        
        tokens.append(Token(tt_eof))
        return tokens