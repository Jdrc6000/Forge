def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(
                prev[j] + 1, # deletion
                curr[j - 1] + 1, # insertion
                prev[j - 1] + (ca != cb), # substitution
            ))
        prev = curr
    
    return prev[-1]

class SymbolTable():
    def __init__(self):
        self.scopes = [{}]  # stack of scopes
    
    def define(self, name, _type):
        if isinstance(_type, dict):
            self.scopes[-1][name] = _type
        else:
            self.scopes[-1][name] = {"type": _type}
    
    def exists(self, name):
        return any(name in scope for scope in self.scopes)
    
    def get(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def all_names(self):
        names = set()
        for scope in self.scopes:
            names.update(scope.keys())
        return names
    
    def closest_match(self, name: str, max_distance: int = 2) -> str | None:
        candidates = self.all_names()
        best, best_dist = None, max_distance + 1
        
        for candidate in candidates:
            d = levenshtein(name, candidate)
            if d < best_dist:
                best, best_dist = candidate, d
        
        return best if best_dist <= max_distance else None
    
    def enter_scope(self):
        self.scopes.append({})
    
    def exit_scope(self):
        self.scopes.pop()