class SymbolTable():
    def __init__(self):
        # name, type (string, number)
        self.symbols = {}
    
    def define(self, name, _type):
        self.symbols[name] = {"type": _type, "scope": "global"} # just for testing
    
    def exists(self, name):
        return name in self.symbols
    
    def get(self, name):
        return self.symbols.get(name)