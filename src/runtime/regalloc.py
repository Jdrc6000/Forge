from src.ir.ir import Instr
from src.ir.operands import Reg
from collections import namedtuple

# Live range structure
class LiveRange:
    def __init__(self, reg, start, end):
        self.reg = reg       # virtual register
        self.start = start   # first instruction index
        self.end = end       # last instruction index
        self.phys = None     # physical register assigned
        self.slot = None

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
    elif instr.op == "SPILL_STORE":
        return [], [instr.b]
    elif instr.op == "SPILL_LOAD":
        return [instr.a], []
    else:
        return [], []

# Compute live ranges based on defs/uses
def compute_live_ranges(code):
    first = {}
    last = {}

    for i, instr in enumerate(code):
        defs, uses = get_defs_uses(instr)
        for r in defs + uses:
            if isinstance(r, Reg):
                first.setdefault(r, i)
                last[r] = i

    ranges = [LiveRange(r, first[r], last[r]) for r in first]
    ranges.sort(key=lambda x: x.start)
    return ranges

def pick_spill(active, current):
    candidates = active + [current]
    return max(candidates, key=lambda r: r.end)

def linear_scan_allocate(code, num_regs):
    ranges = compute_live_ranges(code)
    active = []
    free_regs = list(range(num_regs))
    new_code = []
    
    next_slot = 0

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
            victim = pick_spill(active, r)

            if victim is r:
                r.slot = next_slot
                next_slot += 1
                r.phys = None
                continue
            else:
                # spill an active range
                victim.slot = next_slot
                next_slot += 1

                free_regs.append(victim.phys)
                active.remove(victim)
        
        r.phys = free_regs.pop(0)
        active.append(r)
        active.sort(key=lambda x: x.end)
    
    def rewrite_operand(op):
        if isinstance(op, Reg):
            lr = range_map[op]      # lookup virtual Reg object
            if lr.phys is not None:
                return Reg(lr.phys)
        return op
    
    # Rewrite registers in a new IR list
    range_map = {r.reg: r for r in ranges}
    for instr in code:

        defs, uses = get_defs_uses(instr)

        # reload uses
        for u in uses:
            if not isinstance(u, Reg):
                continue
            lr = range_map[u]
            if lr.slot is not None:
                new_code.append(Instr("SPILL_LOAD", lr.phys, lr.slot))

        new_instr = Instr(
            instr.op,
            rewrite_operand(instr.a),
            rewrite_operand(instr.b),
            rewrite_operand(instr.c)
        )

        new_code.append(new_instr)

        # spill defs
        for d in defs:
            if not isinstance(d, Reg):
                continue
            lr = range_map[d]
            if lr.slot is not None:
                new_code.append(Instr("SPILL_STORE", lr.slot, lr.phys))

    return new_code