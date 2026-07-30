from bootstrap.ir.ir import Instr
from bootstrap.ir.operands import Reg
#from collections import namedtuple

# Live range structure
class LiveRange:
    def __init__(self, reg, start, end):
        self.reg = reg       # virtual register
        self.start = start   # first instruction index
        self.end = end       # last instruction index
        self.phys = None     # physical register assigned
        self.slot = None

# compute defs and uses per opcode
def get_defs_uses(instr):
    if instr.op in ("LOAD_CONST", "LOAD_VAR"):
        return [instr.a], []

    # arithmetic / comparisons that write to dest (a) and read b,c
    elif instr.op in ("ADD", "SUB", "MUL", "DIV", "POW", "EQ", "NE", "LT", "GT", "LE", "GE", "AND"):
        uses = []
        if instr.b: uses.append(instr.b)
        if instr.c: uses.append(instr.c)
        return [instr.a], uses
    
    elif instr.op in ("NEG", "NOT", "MOVE"):
        return [instr.a], [instr.b]

    elif instr.op == "STORE_VAR":
        return [], [instr.b]

    elif instr.op in ("JUMP", "JUMP_IF_TRUE", "JUMP_IF_FALSE"):
        return [], [instr.a] if instr.op in ("JUMP_IF_TRUE", "JUMP_IF_FALSE") else []

    elif instr.op == "SPILL_STORE":
        return [], [instr.b]

    elif instr.op == "SPILL_LOAD":
        return [instr.a], []

    elif instr.op == "CALL":
        # CALL defines instr.c (return value), uses arg_regs
        defs = [instr.c] if instr.c else []
        uses = instr.arg_regs if hasattr(instr, 'arg_regs') else []
        return defs, uses
    
    elif instr.op == "CALL_BUILTIN":
        defs = [instr.c] if instr.c else []
        uses = instr.b if isinstance(instr.b, list) else ([instr.b] if instr.b else [])
        return defs, uses

    elif instr.op == "GET_ATTR":
        # a = dest, b = obj_reg, c = attr_name (str)
        return [instr.a], [instr.b]
    
    elif instr.op == "CALL_METHOD":
        # a = dest, b = obj_reg, c = method_name (str)
        uses = [instr.b] + (instr.arg_regs if hasattr(instr, "arg_regs") else [])
        return [instr.a], uses

    elif instr.op == "RETURN":
        return [], [instr.a] if instr.a else []

    elif instr.op == "BUILD_LIST":
        uses = instr.arg_regs if hasattr(instr, "arg_regs") else []
        return [instr.a], uses

    elif instr.op == "BUILD_STRUCT":
        uses = instr.arg_regs if hasattr(instr, "arg_regs") else []
        return [instr.a], uses
    
    elif instr.op in ("LABEL", "STRUCT_DEF", "IMPORT_MODULE"):
        return [], []

    else:
        print(f"Warning: unknown op in regalloc: {instr.op}")
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
    new_code = []
    
    # Dynamically determine how many scratch registers we need.
    # An instruction might need 1 scratch per spilled use + 1 for a spilled def.
    max_uses = 0
    for instr in code:
        _, uses = get_defs_uses(instr)
        if len(uses) > max_uses:
            max_uses = len(uses)
            
    num_scratch = max_uses + 1 # +1 to account for defs
    if num_scratch >= num_regs:
        num_scratch = num_regs - 1 # fallback
        
    usable_regs = num_regs - num_scratch
    free_regs = list(range(usable_regs))
    scratch_regs = list(range(usable_regs, num_regs))
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
                victim.slot = next_slot
                next_slot += 1
                free_regs.append(victim.phys)
                victim.phys = None  # FIX: victim loses its physical register
                active.remove(victim)
        r.phys = free_regs.pop(0)
        active.append(r)
        active.sort(key=lambda x: x.end)
        
    # FIX: range_map should be computed ONCE here, outside the loops
    range_map = {r.reg: r for r in ranges}
    
    for instr in code:
        defs, uses = get_defs_uses(instr)
        
        scratch_idx = 0
        use_mapping = {}
        
        # load spilled uses into unique scratch registers
        for u in uses:
            if isinstance(u, Reg) and u not in use_mapping:
                lr = range_map.get(u)
                if lr and lr.slot is not None:
                    s = scratch_regs[scratch_idx % len(scratch_regs)]
                    scratch_idx += 1
                    new_code.append(Instr("SPILL_LOAD", Reg(s), lr.slot))
                    use_mapping[u] = Reg(s)
                    
        # assign scratch registers for spilled defs
        def_mapping = {}
        for d in defs:
            if isinstance(d, Reg) and d not in def_mapping:
                lr = range_map.get(d)
                if lr and lr.slot is not None:
                    s = scratch_regs[scratch_idx % len(scratch_regs)]
                    scratch_idx += 1
                    def_mapping[d] = Reg(s)
                    
        def rewrite_operand(op):
            if isinstance(op, Reg):
                if op in use_mapping:
                    return use_mapping[op]
                if op in def_mapping:
                    return def_mapping[op]
                lr = range_map.get(op)
                if lr is None:
                    return op
                if lr.phys is not None:
                    return Reg(lr.phys)
            return op

        if instr.op == "CALL_BUILTIN":
            new_instr = Instr(
                instr.op,
                rewrite_operand(instr.a),
                [rewrite_operand(r) for r in instr.b] if isinstance(instr.b, list) else rewrite_operand(instr.b),
                rewrite_operand(instr.c)
            )
        elif instr.op in ("GET_ATTR", "CALL_METHOD"):
            new_instr = Instr(
                instr.op,
                rewrite_operand(instr.a),
                rewrite_operand(instr.b),
                instr.c 
            )
        elif instr.op == "IMPORT_MODULE":
            new_instr = Instr(instr.op, instr.a, instr.b)
        elif instr.op in ("BUILD_LIST", "BUILD_STRUCT"):
            new_instr = Instr(instr.op, rewrite_operand(instr.a), instr.b)
        else:
            new_instr = Instr(
                instr.op,
                rewrite_operand(instr.a),
                rewrite_operand(instr.b),
                rewrite_operand(instr.c)
            )
            
        if hasattr(instr, "arg_regs"):
            new_instr.arg_regs = [rewrite_operand(r) for r in instr.arg_regs]
        if hasattr(instr, "param_names"):
            new_instr.param_names = instr.param_names
        if hasattr(instr, "fields"):
            new_instr.fields = instr.fields
        if hasattr(instr, "struct_names"):
            new_instr.struct_names = instr.struct_names
        if hasattr(instr, "methods"):
            new_instr.methods = instr.methods
        new_code.append(new_instr)
        
        # store spilled defs back to memory from their scratch registers
        for d in defs:
            if isinstance(d, Reg):
                lr = range_map.get(d)
                if lr and lr.slot is not None:
                    s = def_mapping.get(d)
                    if s:
                        new_code.append(Instr("SPILL_STORE", lr.slot, s))
    return new_code