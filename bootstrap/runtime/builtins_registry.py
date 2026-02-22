from typing import Dict, Callable, List, TYPE_CHECKING
from bootstrap.ir.operands import Reg
import os

if TYPE_CHECKING: # what?
    from .vm import VM

class Builtin:
    def __init__(self, name: str, func: Callable, min_args: int = 0, max_args: int = None):
        self.name = name
        self.func = func
        self.min_args = min_args
        self.max_args = max_args if max_args is not None else min_args

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

def builtin_input(vm: VM, args: list):
    prompt = args[0] if args else ""
    return input(prompt)

def builtin_read_file(vm: VM, args: list):
    path = args[0]
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    
    except FileNotFoundError:
        raise RuntimeError(message=f"read_file: no such file '{path}'")
    
    except OSError as e:
        raise RuntimeError(message=f"read_file: {e}")

def builtin_write_file(vm: VM, args: list):
    path, content = args[0], args[1]
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))
    
    except OSError as e:
        raise RuntimeError(message=f"write_file: {e}")
    
    return 0

def builtin_append_file(vm: VM, args: list):
    path, content = args[0], args[1]
    
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(str(content))
    
    except OSError as e:
        raise RuntimeError(message=f"write_file: {e}")
    
    return 0

def builtin_file_exists(vm: VM, args: list):
    return os.path.exists(args[0])

def builtin_int(vm, args):
    try:
        return int(args[0])
    except (ValueError, TypeError):
        raise RuntimeError(message=f"int: cannot convert '{args[0]}' to int")

def builtin_float(vm, args):
    try:
        return float(args[0])
    except (ValueError, TypeError):
        raise RuntimeError(message=f"float: cannot convert '{args[0]}' to float")

def builtin_str(vm, args):
    return str(args[0])

BUILTINS: Dict[str, Builtin] = {
    "print": Builtin("print", builtin_print, min_args=0, max_args=999),
    "println": Builtin("println", builtin_println, min_args=0, max_args=999),

    "input": Builtin("input", builtin_input, min_args=0, max_args=1),

    "read_file": Builtin("read_file", builtin_read_file, min_args=1, max_args=1),
    "write_file": Builtin("write_file", builtin_write_file, min_args=2, max_args=2),
    "append_file": Builtin("append_file", builtin_append_file, min_args=2, max_args=2),
    "file_exists": Builtin("file_exists", builtin_file_exists, min_args=1, max_args=1),

    "len": Builtin("len", builtin_len, min_args=1, max_args=1),

    "int": Builtin("int", builtin_int, min_args=1, max_args=1),
    "float": Builtin("float", builtin_float, min_args=1, max_args=1),
    "str": Builtin("str", builtin_str, min_args=1, max_args=1),
}