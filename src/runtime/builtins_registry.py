from typing import Dict, Callable, List, TYPE_CHECKING
from src.ir.operands import Reg

if TYPE_CHECKING:
    from .vm import VM

class Builtin:
    def __init__(self, name: str, func: Callable, min_args: int = 0, max_args: int = None):
        self.name = name
        self.func = func
        self.min_args = min_args
        self.max_args = max_args or min_args

    def __call__(self, vm: VM, arg_regs: List[Reg]):
        args = [vm.regs[r.id] for r in arg_regs]
        
        if len(args) < self.min_args or (self.max_args is not None and len(args) > self.max_args):
            raise RuntimeError(
                message=f"Builtin '{self.name}' expected {self.min_args}-{self.max_args} args, got {len(args)}"
            )
        
        return self.func(vm, args)

def builtin_print(vm: VM, args: list):
    print(*args, sep=" ", end="")

def builtin_println(vm: VM, args: list):
    print(*args)

def builtin_len(vm: VM, args: list):
    if len(args) != 1:
        raise ValueError("len() takes exactly one argument")
    return len(args[0])

BUILTINS: Dict[str, Builtin] = {
    "print": Builtin("print",   builtin_print,   min_args=0, max_args=999),
    "println": Builtin("println", builtin_println, min_args=0, max_args=999),
    "len": Builtin("len",     builtin_len,     min_args=1, max_args=1), # consider removing since dot notation function ".len()" exists
}