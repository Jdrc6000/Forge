from typing import Any, List, Callable
import math

def _require_args(name, args, count):
    if len(args) != count:
        raise TypeError(f"'name' takes {count} argument(s), got {len(args)}")

def _list_push(list, args):
    _require_args("push", args, 1)
    list.append(args[0])
    return list

def _list_pop(list, args):
    if args:
        list.pop(int(args[0]))
    return list

def _list_join(list, args):
    sep = args[0] if args else ""
    return sep.join(str(x) for x in list)

STRING_MEMBERS = {
    "len": lambda s, args: len(s),
    "upper": lambda s, args: s.upper(),
    "lower": lambda s, args: s.lower(),
    "contains": lambda s, args: (_require_args("contains", args, 1) or args[0] in s),
    "replace": lambda s, args: (_require_args("replace", args, 2) or s.replace(args[0], args[1])),
    "split": lambda s, args: s.split(args[0]) if args else s.split(),
    "chars": lambda s, args: list(s),
    "reverse": lambda s, args: s[::-1],
    "at": lambda s, args: (_require_args("at", args, 1) or s[int(args[0])]),
}

LIST_MEMBERS = {
    "len": lambda l, args: len(l),
    "push": _list_push,
    "pop": _list_pop,
    "first": lambda l, args: l[0],
    "last": lambda l, args: l[-1],
    "at": lambda l, args: (_require_args("at", args, 1) or l[int(args[0])]),
    "reverse": lambda l, args: l[::-1],
    "join": _list_join,
}

NUMBER_MEMBERS = {
    "abs": lambda n, args: abs(n),
    "sqrt": lambda n, args: math.sqrt(n),
    "floor": lambda n, args: math.floor(n),
    "ceil": lambda n, args: math.ceil(n),
    "round": lambda n, args: round(n, int(args[0])) if args else round(n),
    "pow": lambda n, args: (_require_args("pow", args, 1) or n ** args[0]),
    "str": lambda n, args: str(n),
    "int": lambda n, args: int(n),
    "float": lambda n, args: float(n),
}

# dispatch
def resolve_member(obj: Any, name: str) -> Callable:
    if isinstance(obj, str):
        if name in STRING_MEMBERS:
            return STRING_MEMBERS[name]
    elif isinstance(obj, list):
        if name in LIST_MEMBERS:
            return LIST_MEMBERS[name]
    elif isinstance(obj, (int, float)):
        if name in NUMBER_MEMBERS:
            return NUMBER_MEMBERS[name]

    type_name = type(obj).__name__
    raise AttributeError(f"'{type_name}' has no attribute or method '{name}'")