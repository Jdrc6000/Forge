class SymbolTable():
    def __init__(self):
        self.scopes = [{}]  # stack of scopes
    
    def define(self, name, _type):
        self.scopes[-1][name] = {"type": _type}
    
    def exists(self, name):
        return any(name in scope for scope in self.scopes)
    
    def get(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def enter_scope(self):
        self.scopes.append({})
    
    def exit_scope(self):
        self.scopes.pop()