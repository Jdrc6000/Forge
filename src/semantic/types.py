from dataclasses import dataclass
from typing import Tuple, ClassVar

@dataclass(frozen=True, slots=True)
class Type:
    name: ClassVar[str]

    def is_compatible(self, other: "Type") -> bool:
        if isinstance(other, UnknownType):
            return True
        return self == other

    def supports_binary(self, op: str, other: "Type") -> bool:
        return False

@dataclass(frozen=True)
class NumberType(Type):
    name: ClassVar[str] = "number"

    def supports_binary(self, op: str, other: "Type") -> bool:
        if op in {"+", "-", "*", "/", "^"}:
            return isinstance(other, NumberType)
        return False

@dataclass(frozen=True)
class StringType(Type):
    name: ClassVar[str] = "string"

    def supports_binary(self, op: str, other: "Type") -> bool:
        if op == "+":
            return isinstance(other, StringType)
        return False

@dataclass(frozen=True)
class BoolType(Type):
    name: ClassVar[str] = "bool"
    
    def supports_binary(self, op, other):
        return op in {"and", "or"} and isinstance(other, BoolType)

# future proofing
@dataclass(frozen=True)
class ListType(Type):
    name: ClassVar[str] = "list"
    element_type: Type

@dataclass(frozen=True)
class UnknownType(Type):
    name: str = "unknown"

    def is_compatible(self, other: "Type") -> bool:
        return True
    
    def supports_binary(self, op: str, other: "Type") -> bool:
        # allow the operation and "become" the other type
        return True

NUMBER = NumberType()
STRING = StringType()
BOOL = BoolType()
UNKNOWN = UnknownType()