from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Reg:
    id: int

@dataclass(frozen=True)
class Imm:
    value: Any