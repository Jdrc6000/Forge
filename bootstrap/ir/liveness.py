from bootstrap.ir.cfg import BasicBlock, CFG
from bootstrap.ir.operands import Reg
from bootstrap.runtime.regalloc import get_defs_uses

from collections import deque

def reverse_postorder(cfg):
    visited = set()
    order = []
    
    def dfs(bb):
        visited.add(bb.id)
        for succ in bb.succs:
            if succ.id not in visited:
                dfs(succ)
    
    dfs(cfg.entry)
    return list(reversed(order)) # actually reverse postorder

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
    rpo = reverse_postorder(cfg)
    while changed:
        changed = False
        
        for bb in rpo:
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
                "JUMP", "JUMP_IF_TRUE", "JUMP_IF_FALSE", "LABEL",
                "STRUCT_DEF", "IMPORT_MODULE"
            ) or (instr.op == "STORE_VAR" and instr.a in read_vars)
            if is_side_affect or (defined_regs and any(d in needed for d in defined_regs)):
                new_instrs.append(instr)
                
            for d in defined_regs:
                needed.discard(d)
                
            for u in uses:
                if isinstance(u, Reg):
                    needed.add(u)
        
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
    
    def is_function_entry(bb):
        return (bb.instrs and 
                bb.instrs[0].op == "LABEL" and 
                isinstance(bb.instrs[0].a, str) and
                bb.instrs[0].a != "__main__")
    
    cfg.blocks = [
        bb for bb in cfg.blocks
        if bb.id in visited or is_function_entry(bb)
    ]