from src.ir.cfg import BasicBlock, CFG
from src.ir.operands import Reg
from src.runtime.regalloc import get_defs_uses

from collections import deque

def compute_liveness(cfg: CFG):
    for bb in cfg.blocks:
        bb.live_in = set()
        bb.live_out = set()
        
        # ue_vars - upward-exposed uses
        bb.ue_vars = set()
        bb.defs = set()
        
        for instr in bb.instrs:
            d, u = get_defs_uses(instr)
            
            for r in u:
                if isinstance(r, Reg) and r not in bb.defs:
                    bb.ue_vars.add(r)
            
            for r in d:
                if isinstance(r, Reg):
                    bb.defs.add(r)

    changed = True
    while changed:
        changed = False
        
        for bb in reversed(cfg.blocks): # backward pass?
            new_out = set()
            
            for succ in bb.succs:
                new_out |= succ.live_in
            
            new_in = bb.ue_vars | (new_out - bb.defs)
            if new_in != bb.live_in or new_out != bb.live_out:
                bb.live_in = new_in
                bb.live_out = new_out
                changed = True

def eliminate_dead_stores(cfg: CFG):
    read_vars = set()
    for bb in cfg.blocks:
        for instr in bb.instrs:
            if instr.op == "LOAD_VAR":
                read_vars.add(instr.b)
    
    for bb in cfg.blocks:
        needed = set(bb.live_out)
        new_instrs = []
        
        for instr in reversed(bb.instrs):
            defs, uses = get_defs_uses(instr)
            defined_regs = [d for d in defs if isinstance(d, Reg)]
            
            is_side_affect = instr.op in (
                "CALL", "CALL_BUILTIN", "CALL_METHOD", "RETURN",
                "JUMP", "JUMP_IF_TRUE", "JUMP_IF_FALSE", "LABEL"
            ) or (instr.op == "STORE_VAR" and instr.a in read_vars)
            if is_side_affect or (defined_regs and any(d in needed for d in defined_regs)):
                new_instrs.append(instr)
                
                for u in uses:
                    if isinstance(u, Reg):
                        needed.add(u)

            for d in defined_regs:
                needed.discard(d)
        
        bb.instrs = list(reversed(new_instrs))

def remove_unreachable(cfg: CFG):
    visited = set()
    q = deque([cfg.entry])
    
    while q:
        bb = q.popleft()
        
        if bb.id in visited:
            continue
        
        visited.add(bb.id)
        for s in bb.succs:
            q.append(s)
    
    cfg.blocks = [bb for bb in cfg.blocks if bb.id in visited]