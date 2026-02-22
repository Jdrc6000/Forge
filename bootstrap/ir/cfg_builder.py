from bootstrap.ir.cfg import BasicBlock, CFG
from bootstrap.ir.ir import Instr
from typing import List

TERMINATORS = {"JUMP", "JUMP_IF_TRUE", "JUMP_IF_FALSE", "RETURN"}
BRANCH_OPS = {"JUMP_IF_TRUE", "JUMP_IF_FALSE"}

def build_cfg(code: List[Instr]) -> CFG:
    cfg = CFG()
    
    # pass 1
    # leader: first instr, any jump target, or instr after a terminator
    leaders = {0}
    for i, instr in enumerate(code):
        if instr.op in TERMINATORS:
            if i + 1 < len(code):
                leaders.add(i + 1)
        
        if instr.op in ("JUMP", *BRANCH_OPS):
            target = instr.b if instr.op in BRANCH_OPS else instr.a
            
            if isinstance(target, int):
                leaders.add(target)
            
            if instr.op == "LABEL":
                leaders.add(i)
    
    leaders = sorted(leaders)
    
    # pass 2
    # slice into blocks
    block_at = {} # start_index -> BasicBlock
    for idx, start in enumerate(leaders):
        end = leaders[idx + 1] if idx + 1 < len(leaders) else len(code)
        bb = BasicBlock(
            id=idx,
            instrs=code[start:end]
        )
        cfg.blocks.append(bb)
        block_at[start] = bb
    
    cfg.entry = cfg.blocks[0] if cfg.blocks else None
    
    for idx, start in enumerate(leaders):
        end = leaders[idx + 1] if idx + 1 < len(leaders) else len(code)
        bb = block_at[start]
        
        if not bb.instrs:
            continue
        
        last = bb.instrs[-1]
        
        if last.op == "JUMP":
            target = last.a
            if isinstance(target, int) and target in block_at:
                cfg.add_edge(bb, block_at[target])
        
        elif last.op in BRANCH_OPS:
            # false / fall through edge
            if end < len(code) and end in block_at:
                cfg.add_edge(bb, block_at[end])
            
            target = last.b if last.op in BRANCH_OPS else last.a
            if isinstance(target, int) and target in block_at:
                cfg.add_edge(bb, block_at[target])
        
        elif last.op == "RETURN":
            pass # no successors
        
        else:
            if end < len(code) and end in block_at:
                cfg.add_edge(bb, block_at[end])
    
    return cfg