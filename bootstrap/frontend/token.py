from dataclasses import dataclass
from bootstrap.frontend.token_types import TokenType
from typing import Any, Optional

@dataclass
class Token:
    type: TokenType
    value: Optional[Any] = None
    line: int = 0
    column: int = 0

    def __repr__(self):
        if self.value is not None:
            return f"{self.type.name}:{self.value}"
        return f"{self.type.name}"