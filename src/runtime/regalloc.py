from collections import namedtuple

# Live range structure
class LiveRange:
    def __init__(self, reg, start, end):
        self.reg = reg       # virtual register
        self.start = start   # first instruction index
        self.end = end       # last instruction index
        self.phys = None     # physical register assigned

# Compute defs and uses per opcode
def get_defs_uses(instr):
    if instr.op in ("LOAD_CONST", "LOAD_VAR"):
        return [instr.a], []
    elif instr.op in ("ADD","SUB","MUL","DIV","POW"):
        return [instr.a], [instr.b, instr.c]
    elif instr.op in ("NEG","NOT","MOVE"):
        return [instr.a], [instr.b]
    elif instr.op == "STORE_VAR":
        return [], [instr.b]
    elif instr.op in ("PRINT",):
        return [], [instr.a]
    elif instr.op in ("JUMP", "JUMP_IF_TRUE", "JUMP_IF_FALSE"):
        return [], [instr.a] if instr.op == "JUMP_IF_TRUE" or instr.op == "JUMP_IF_FALSE" else []
    else:
        return [], []

# Compute live ranges based on defs/uses
def compute_live_ranges(code):
    first = {}
    last = {}

    for i, instr in enumerate(code):
        defs, uses = get_defs_uses(instr)
        for r in defs + uses:
            if isinstance(r, int):
                first.setdefault(r, i)
                last[r] = i

    ranges = [LiveRange(r, first[r], last[r]) for r in first]
    ranges.sort(key=lambda x: x.start)
    return ranges

# Linear scan allocator
def linear_scan_allocate(code, num_regs):
    ranges = compute_live_ranges(code)
    active = []
    free_regs = list(range(num_regs))
    new_code = []

    def expire_old(current_start):
        nonlocal active, free_regs
        still_active = []
        for r in active:
            if r.end >= current_start:
                still_active.append(r)
            else:
                free_regs.append(r.phys)
        active[:] = still_active

    for r in ranges:
        expire_old(r.start)
        if not free_regs:
            raise RuntimeError("Out of registers (spilling not implemented)")
        r.phys = free_regs.pop(0)  # assign lowest-numbered free reg
        active.append(r)
        active.sort(key=lambda x: x.end)

    # Rewrite registers in a new IR list
    mapping = {r.reg: r.phys for r in ranges}
    for instr in code:
        new_instr = type(instr)(instr.op, instr.a, instr.b, instr.c)

        defs, uses = get_defs_uses(instr)
        reg_operands = set(defs + uses)

        if new_instr.a in reg_operands:
            new_instr.a = mapping[new_instr.a]

        if new_instr.b in reg_operands:
            new_instr.b = mapping[new_instr.b]

        if new_instr.c in reg_operands:
            new_instr.c = mapping[new_instr.c]

        new_code.append(new_instr)

    return new_code