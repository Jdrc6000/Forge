from dataclasses import dataclass, field
from typing import List, Optional
from bootstrap.ir.ir import Instr

_JUMP_OPS = ("JUMP", "JUMP_IF_TRUE", "JUMP_IF_FALSE")

@dataclass
class BasicBlock:
    id: int
    instrs: List[Instr] = field(default_factory=list)
    succs: List["BasicBlock"] = field(default_factory=list)
    preds: List["BasicBlock"] = field(default_factory=list)
    
    def __repr__(self):
        return f"BB{self.id}({len(self.instrs)} instrs)"

@dataclass
class CFG:
    blocks: List[BasicBlock] = field(default_factory=list)
    entry: Optional[BasicBlock] = None
    
    def add_edge(self, src: BasicBlock, dst: BasicBlock):
        src.succs.append(dst)
        dst.preds.append(src)
    
    def flatten(self):
        code = []
        orig_to_new = {}
        for bb in self.blocks:
            for instr in bb.instrs:
                orig = getattr(instr, "_orig_idx", None)
                if orig is not None:
                    orig_to_new[orig] = len(code)
                code.append(instr)

        for instr in code:
            if instr.op == "JUMP":
                t = instr.a
                if isinstance(t, int):
                    instr.a = orig_to_new.get(t, t)
            elif instr.op in ("JUMP_IF_TRUE", "JUMP_IF_FALSE"):
                t = instr.b
                if isinstance(t, int):
                    instr.b = orig_to_new.get(t, t)

        return code
    
    # we are blessed with another dump function once again!!
    def dump(self):
        for bb in self.blocks:
            print(f"\nBB{bb.id}")
            for instr in bb.instrs:
                print(f"  {instr.op} {instr.a} {instr.b} {instr.c}")
            print(f"  0> {[str(s) for s in bb.succs]}")