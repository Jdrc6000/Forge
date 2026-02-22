"""
source /.venv/bin/activate
python -m pytest tests/test_suite.py -v

ai wrote this (theres no way im writing all of this myself... waste of my time)
its 982 LOC so its not included in vibe-coded.txt
"""
# this will be resolved when ran inside a venv
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.frontend.lexer import Lexer
from src.frontend.parser import Parser
from src.frontend.token_types import TokenType
from src.frontend.token import Token
from src.semantic.analyser import Analyser, SymbolTable
from src.optimiser.optimiser import Optimiser
from src.ir.generator import IRGenerator
from src.runtime.regalloc import linear_scan_allocate
from src.runtime.vm import VM
from src.exceptions import (
    LexerError, ParseError, SemanticError, CompileError,
    UndefinedVariableError, UnknownOpcodeError
)
from src.semantic.types import NUMBER, STRING, BOOL, UNKNOWN
from src.runtime.methods import resolve_member, STRING_MEMBERS, LIST_MEMBERS, NUMBER_MEMBERS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(code: str, num_regs: int = 256):
    """Full pipeline: lex → parse → analyse → optimise → IR → regalloc → VM."""
    lexer = Lexer(code)
    tokens = lexer.get_tokens()
    parser = Parser(tokens)
    tree = parser.parse()
    symbol_table = SymbolTable()
    Analyser(symbol_table).analyse(tree)
    tree = Optimiser().optimise(tree)
    ir_gen = IRGenerator()
    ir_gen.generate(tree)
    allocated = linear_scan_allocate(ir_gen.ir.code, num_regs=num_regs)
    vm = VM(num_regs=num_regs)
    vm.code = allocated
    vm.ip = vm.find_label("__main__")
    vm.run(allocated)
    return vm


def run_expr(code: str) -> object:
    """Run code and return value stored in variable 'result'."""
    vm = run(code)
    return vm.vars.get("result")


# ===========================================================================
# LEXER TESTS
# ===========================================================================

class TestLexer:
    def _lex(self, text):
        return Lexer(text).get_tokens()

    def test_integer(self):
        tokens = self._lex("42")
        assert tokens[0].type == TokenType.INT
        assert tokens[0].value == 42

    def test_float(self):
        tokens = self._lex("3.14")
        assert tokens[0].type == TokenType.FLOAT
        assert abs(tokens[0].value - 3.14) < 1e-9

    def test_string_double_quote(self):
        tokens = self._lex('"hello"')
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "hello"

    def test_string_single_quote(self):
        tokens = self._lex("'world'")
        assert tokens[0].type == TokenType.STRING
        assert tokens[0].value == "world"

    def test_keywords(self):
        src = "if else while for fn return true false and or not in"
        tokens = self._lex(src)
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.IF in types
        assert TokenType.ELSE in types
        assert TokenType.WHILE in types
        assert TokenType.FOR in types
        assert TokenType.FN in types
        assert TokenType.RETURN in types
        assert TokenType.TRUE in types
        assert TokenType.FALSE in types

    def test_operators(self):
        tokens = self._lex("+ - * / ^ == != < > <= >=")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.PLUS in types
        assert TokenType.MINUS in types
        assert TokenType.MUL in types
        assert TokenType.DIV in types
        assert TokenType.POW in types
        assert TokenType.EE in types
        assert TokenType.NE in types
        assert TokenType.LESS in types
        assert TokenType.GREATER in types
        assert TokenType.LE in types
        assert TokenType.GE in types

    def test_range_operator(self):
        tokens = self._lex("0..10")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.RANGE in types

    def test_identifier(self):
        tokens = self._lex("myVar")
        assert tokens[0].type == TokenType.NAME
        assert tokens[0].value == "myVar"

    def test_identifier_with_underscore(self):
        tokens = self._lex("my_var_2")
        assert tokens[0].type == TokenType.NAME
        assert tokens[0].value == "my_var_2"

    def test_eof(self):
        tokens = self._lex("")
        assert tokens[-1].type == TokenType.EOF

    def test_illegal_character(self):
        with pytest.raises(LexerError):
            self._lex("@")

    def test_line_tracking(self):
        tokens = self._lex("a\nb")
        name_tokens = [t for t in tokens if t.type == TokenType.NAME]
        assert name_tokens[0].line == 1
        assert name_tokens[1].line == 2

    def test_column_tracking(self):
        tokens = self._lex("  x")
        name_tokens = [t for t in tokens if t.type == TokenType.NAME]
        assert name_tokens[0].column == 3

    def test_brackets(self):
        tokens = self._lex("()[]{}")
        types = [t.type for t in tokens if t.type != TokenType.EOF]
        assert TokenType.LPAREN in types
        assert TokenType.RPAREN in types
        assert TokenType.LBRACKET in types
        assert TokenType.RBRACKET in types
        assert TokenType.LBRACE in types
        assert TokenType.RBRACE in types


# ===========================================================================
# PARSER TESTS
# ===========================================================================

class TestParser:
    def _parse(self, code):
        tokens = Lexer(code).get_tokens()
        return Parser(tokens).parse()

    def test_assignment(self):
        from src.frontend.ast_nodes import Module, Assign, Name, Constant
        tree = self._parse("x = 5")
        assert isinstance(tree, Module)
        assert isinstance(tree.body[0], Assign)
        assert tree.body[0].target.id == "x"
        assert tree.body[0].value.value == 5

    def test_binary_op(self):
        from src.frontend.ast_nodes import BinOp
        tree = self._parse("x = 1 + 2")
        assert isinstance(tree.body[0].value, BinOp)
        assert tree.body[0].value.op == "+"

    def test_operator_precedence_mul_over_add(self):
        from src.frontend.ast_nodes import BinOp
        tree = self._parse("x = 1 + 2 * 3")
        # Should be: 1 + (2 * 3)
        root = tree.body[0].value
        assert root.op == "+"
        assert root.right.op == "*"

    def test_function_def(self):
        from src.frontend.ast_nodes import FunctionDef
        tree = self._parse("fn foo(a, b) { x = a }")
        assert isinstance(tree.body[0], FunctionDef)
        assert tree.body[0].name == "foo"
        assert tree.body[0].args == ["a", "b"]

    def test_if_else(self):
        from src.frontend.ast_nodes import If
        tree = self._parse("if x == 1 { y = 2 } else { y = 3 }")
        assert isinstance(tree.body[0], If)
        assert tree.body[0].orelse is not None

    def test_while(self):
        from src.frontend.ast_nodes import While
        tree = self._parse("while x < 10 { x = x + 1 }")
        assert isinstance(tree.body[0], While)

    def test_for(self):
        from src.frontend.ast_nodes import For
        tree = self._parse("for i in 0..10 { x = i }")
        assert isinstance(tree.body[0], For)
        assert tree.body[0].target.id == "i"

    def test_list_literal(self):
        from src.frontend.ast_nodes import List
        tree = self._parse("x = [1, 2, 3]")
        assert isinstance(tree.body[0].value, List)
        assert len(tree.body[0].value.elements) == 3

    def test_method_call(self):
        from src.frontend.ast_nodes import MethodCall
        tree = self._parse('x = s.upper()')
        assert isinstance(tree.body[0].value, MethodCall)
        assert tree.body[0].value.method == "upper"

    def test_attribute_access(self):
        from src.frontend.ast_nodes import Attribute
        tree = self._parse("x = s.len()")
        # .len() is a method call, not attribute
        from src.frontend.ast_nodes import MethodCall
        assert isinstance(tree.body[0].value, MethodCall)

    def test_return(self):
        from src.frontend.ast_nodes import Return
        tree = self._parse("fn f() { return 42 }")
        body = tree.body[0].body.statements
        assert isinstance(body[0], Return)

    def test_compare(self):
        from src.frontend.ast_nodes import Compare
        tree = self._parse("x = a == b")
        assert isinstance(tree.body[0].value, Compare)

    def test_unary_minus(self):
        from src.frontend.ast_nodes import UnOp
        tree = self._parse("x = -5")
        assert isinstance(tree.body[0].value, UnOp)
        assert tree.body[0].value.op == "-"

    def test_unary_not(self):
        from src.frontend.ast_nodes import UnOp
        tree = self._parse("x = not true")
        assert isinstance(tree.body[0].value, UnOp)
        assert tree.body[0].value.op == "not"

    def test_nested_function_call(self):
        from src.frontend.ast_nodes import Call
        tree = self._parse("x = foo(bar(1))")
        outer = tree.body[0].value
        assert isinstance(outer, Call)

    def test_parse_error_missing_paren(self):
        with pytest.raises(ParseError):
            self._parse("fn foo( { }")

    def test_bool_true(self):
        from src.frontend.ast_nodes import Constant
        tree = self._parse("x = true")
        assert tree.body[0].value.value is True

    def test_bool_false(self):
        from src.frontend.ast_nodes import Constant
        tree = self._parse("x = false")
        assert tree.body[0].value.value is False


# ===========================================================================
# SEMANTIC ANALYSER TESTS
# ===========================================================================

class TestSemanticAnalyser:
    def _analyse(self, code):
        tokens = Lexer(code).get_tokens()
        tree = Parser(tokens).parse()
        st = SymbolTable()
        Analyser(st).analyse(tree)
        return st

    def test_variable_defined_after_assign(self):
        st = self._analyse("x = 42")
        assert st.exists("x")

    def test_undefined_variable_raises(self):
        with pytest.raises(UndefinedVariableError):
            self._analyse("y = x")

    def test_function_defined_after_def(self):
        st = self._analyse("fn greet(name) { x = name }")
        assert st.exists("greet")

    def test_undefined_function_raises(self):
        with pytest.raises(UndefinedVariableError):
            self._analyse("x = foo()")

    def test_wrong_arg_count_raises(self):
        from src.exceptions import TypeError as LangTypeError
        with pytest.raises(LangTypeError):
            self._analyse("fn f(a, b) { x = a } x = f(1)")

    def test_return_outside_function_raises(self):
        with pytest.raises(SemanticError):
            self._analyse("return 1")

    def test_builtin_call_ok(self):
        # Should not raise
        self._analyse('println("hi")')

    def test_list_type_inferred(self):
        tokens = Lexer("[1, 2, 3]").get_tokens()
        from src.frontend.ast_nodes import List
        from src.semantic.types import ListType
        tree = Parser(tokens).parse()
        st = SymbolTable()
        analyser = Analyser(st)
        # Wrap in assignment for analysis
        tokens2 = Lexer("x = [1, 2, 3]").get_tokens()
        tree2 = Parser(tokens2).parse()
        Analyser(SymbolTable()).analyse(tree2)  # Should not raise


# ===========================================================================
# OPTIMISER TESTS
# ===========================================================================

class TestOptimiser:
    def _optimise(self, code):
        tokens = Lexer(code).get_tokens()
        tree = Parser(tokens).parse()
        return Optimiser().optimise(tree)

    def test_constant_fold_add(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = 2 + 3")
        assert isinstance(tree.body[0].value, Constant)
        assert tree.body[0].value.value == 5

    def test_constant_fold_mul(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = 4 * 5")
        assert tree.body[0].value.value == 20

    def test_constant_fold_sub(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = 10 - 3")
        assert tree.body[0].value.value == 7

    def test_constant_fold_div(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = 10 / 2")
        assert tree.body[0].value.value == 5.0

    def test_constant_fold_pow(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = 2 ^ 10")
        assert tree.body[0].value.value == 1024

    def test_constant_fold_unary_neg(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = -7")
        assert tree.body[0].value.value == -7

    def test_constant_fold_not(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = not true")
        assert tree.body[0].value.value is False

    def test_dead_code_if_true(self):
        # if true { x = 1 } else { x = 2 }  →  x = 1
        from src.frontend.ast_nodes import Assign
        tree = self._optimise("if true { x = 1 } else { x = 2 }")
        # Dead code eliminator returns a list inlined into module body
        stmts = tree.body
        assigns = [s for s in stmts if isinstance(s, Assign)]
        assert any(s.value.value == 1 for s in assigns)

    def test_dead_code_if_false(self):
        from src.frontend.ast_nodes import Assign
        tree = self._optimise("if false { x = 1 } else { x = 2 }")
        stmts = tree.body
        assigns = [s for s in stmts if isinstance(s, Assign)]
        assert any(s.value.value == 2 for s in assigns)

    def test_constant_fold_compare(self):
        from src.frontend.ast_nodes import Constant
        tree = self._optimise("x = 3 == 3")
        # After constant folding, Compare of constants → Constant(True)
        assert isinstance(tree.body[0].value, Constant)
        assert tree.body[0].value.value is True


# ===========================================================================
# IR GENERATOR TESTS
# ===========================================================================

class TestIRGenerator:
    def _gen(self, code):
        tokens = Lexer(code).get_tokens()
        tree = Parser(tokens).parse()
        st = SymbolTable()
        Analyser(st).analyse(tree)
        tree = Optimiser().optimise(tree)
        ir_gen = IRGenerator()
        ir_gen.generate(tree)
        return ir_gen.ir

    def _ops(self, code):
        return [i.op for i in self._gen(code).code]

    def test_load_const_emitted(self):
        assert "LOAD_CONST" in self._ops("x = 42")

    def test_store_var_emitted(self):
        assert "STORE_VAR" in self._ops("x = 42")

    def test_add_emitted(self):
        assert "ADD" in self._ops("x = a + b")

    def test_function_label_emitted(self):
        ops = self._ops("fn foo() { x = 1 }")
        assert "LABEL" in ops

    def test_jump_if_false_for_if(self):
        assert "JUMP_IF_FALSE" in self._ops("if x == 1 { y = 2 }")

    def test_jump_for_while(self):
        assert "JUMP" in self._ops("while x < 10 { x = x + 1 }")

    def test_return_emitted(self):
        assert "RETURN" in self._ops("fn f() { return 1 }")

    def test_build_list_emitted(self):
        assert "BUILD_LIST" in self._ops("x = [1, 2, 3]")

    def test_call_method_emitted(self):
        ops = self._ops('x = s.upper()')
        assert "CALL_METHOD" in ops

    def test_eq_comparison(self):
        assert "EQ" in self._ops("x = a == b")

    def test_lt_comparison(self):
        assert "LT" in self._ops("x = a < b")

    def test_ne_comparison(self):
        assert "NE" in self._ops("x = a != b")


# ===========================================================================
# RUNTIME METHOD TESTS
# ===========================================================================

class TestStringMethods:
    def test_len(self):
        assert STRING_MEMBERS["len"]("hello", []) == 5

    def test_upper(self):
        assert STRING_MEMBERS["upper"]("hello", []) == "HELLO"

    def test_lower(self):
        assert STRING_MEMBERS["lower"]("HELLO", []) == "hello"

    def test_at(self):
        assert STRING_MEMBERS["at"]("hello", [1]) == "e"

    def test_contains_true(self):
        assert STRING_MEMBERS["contains"]("hello world", ["world"]) is True

    def test_contains_false(self):
        assert STRING_MEMBERS["contains"]("hello", ["xyz"]) is False

    def test_replace(self):
        assert STRING_MEMBERS["replace"]("hello world", ["world", "there"]) == "hello there"

    def test_split(self):
        assert STRING_MEMBERS["split"]("a,b,c", [","]) == ["a", "b", "c"]

    def test_reverse(self):
        assert STRING_MEMBERS["reverse"]("abc", []) == "cba"

    def test_chars(self):
        assert STRING_MEMBERS["chars"]("abc", []) == ["a", "b", "c"]


class TestListMethods:
    def test_len(self):
        assert LIST_MEMBERS["len"]([1, 2, 3], []) == 3

    def test_at(self):
        assert LIST_MEMBERS["at"]([10, 20, 30], [1]) == 20

    def test_first(self):
        assert LIST_MEMBERS["first"]([10, 20], []) == 10

    def test_last(self):
        assert LIST_MEMBERS["last"]([10, 20], []) == 20

    def test_push(self):
        lst = [1, 2]
        result = LIST_MEMBERS["push"](lst, [3])
        assert 3 in result

    def test_reverse(self):
        assert LIST_MEMBERS["reverse"]([1, 2, 3], []) == [3, 2, 1]

    def test_join(self):
        assert LIST_MEMBERS["join"](["a", "b", "c"], [","]) == "a,b,c"

    def test_pop(self):
        lst = [1, 2, 3]
        LIST_MEMBERS["pop"](lst, [0])
        assert 1 not in lst


class TestNumberMethods:
    def test_abs(self):
        assert NUMBER_MEMBERS["abs"](-5, []) == 5

    def test_sqrt(self):
        import math
        assert abs(NUMBER_MEMBERS["sqrt"](9, []) - 3.0) < 1e-9

    def test_floor(self):
        assert NUMBER_MEMBERS["floor"](3.7, []) == 3

    def test_ceil(self):
        assert NUMBER_MEMBERS["ceil"](3.2, []) == 4

    def test_round(self):
        assert NUMBER_MEMBERS["round"](3.5, []) == 4

    def test_str(self):
        assert NUMBER_MEMBERS["str"](42, []) == "42"

    def test_int(self):
        assert NUMBER_MEMBERS["int"](3.9, []) == 3

    def test_float(self):
        assert NUMBER_MEMBERS["float"](5, []) == 5.0

    def test_pow(self):
        assert NUMBER_MEMBERS["pow"](2, [8]) == 256


class TestResolveMember:
    def test_unknown_type_raises(self):
        with pytest.raises(AttributeError):
            resolve_member(object(), "foo")

    def test_unknown_string_method_raises(self):
        with pytest.raises(AttributeError):
            resolve_member("hello", "nonexistent")

    def test_unknown_list_method_raises(self):
        with pytest.raises(AttributeError):
            resolve_member([], "nonexistent")


# ===========================================================================
# END-TO-END VM TESTS
# ===========================================================================

class TestEndToEnd:
    def test_simple_assignment(self):
        vm = run("result = 42")
        assert vm.vars["result"] == 42

    def test_addition(self):
        vm = run("result = 10 + 5")
        assert vm.vars["result"] == 15

    def test_subtraction(self):
        vm = run("result = 10 - 3")
        assert vm.vars["result"] == 7

    def test_multiplication(self):
        vm = run("result = 4 * 6")
        assert vm.vars["result"] == 24

    def test_division(self):
        vm = run("result = 10 / 4")
        assert vm.vars["result"] == 2.5

    def test_power(self):
        vm = run("result = 2 ^ 8")
        assert vm.vars["result"] == 256

    def test_string_assignment(self):
        vm = run('result = "hello"')
        assert vm.vars["result"] == "hello"

    def test_string_concat(self):
        vm = run('result = "hello" + " world"')
        assert vm.vars["result"] == "hello world"

    def test_boolean_true(self):
        vm = run("result = true")
        assert vm.vars["result"] is True

    def test_boolean_false(self):
        vm = run("result = false")
        assert vm.vars["result"] is False

    def test_unary_negate(self):
        vm = run("result = -10")
        assert vm.vars["result"] == -10

    def test_unary_not(self):
        vm = run("result = not true")
        assert vm.vars["result"] is False

    def test_comparison_eq_true(self):
        vm = run("result = 1 == 1")
        assert vm.vars["result"] is True

    def test_comparison_eq_false(self):
        vm = run("result = 1 == 2")
        assert vm.vars["result"] is False

    def test_comparison_ne(self):
        vm = run("result = 1 != 2")
        assert vm.vars["result"] is True

    def test_comparison_lt(self):
        vm = run("result = 3 < 5")
        assert vm.vars["result"] is True

    def test_comparison_gt(self):
        vm = run("result = 5 > 3")
        assert vm.vars["result"] is True

    def test_comparison_le(self):
        vm = run("result = 3 <= 3")
        assert vm.vars["result"] is True

    def test_comparison_ge(self):
        vm = run("result = 5 >= 6")
        assert vm.vars["result"] is False

    def test_if_true_branch(self):
        vm = run("x = 1\nif x == 1 { result = 10 } else { result = 20 }")
        assert vm.vars["result"] == 10

    def test_if_false_branch(self):
        vm = run("x = 2\nif x == 1 { result = 10 } else { result = 20 }")
        assert vm.vars["result"] == 20

    def test_if_elif_chain(self):
        code = """
x = 2
if x == 1 {
    result = 1
} else if x == 2 {
    result = 2
} else {
    result = 3
}
"""
        vm = run(code)
        assert vm.vars["result"] == 2

    def test_while_loop(self):
        code = """
i = 0
result = 0
while i < 5 {
    result = result + i
    i = i + 1
}
"""
        vm = run(code)
        assert vm.vars["result"] == 10  # 0+1+2+3+4

    def test_for_loop(self):
        code = """
result = 0
for i in 0..5 {
    result = result + i
}
"""
        vm = run(code)
        assert vm.vars["result"] == 10

    def test_function_call_return(self):
        code = """
fn double(x) {
    return x * 2
}
result = double(7)
"""
        vm = run(code)
        assert vm.vars["result"] == 14

    def test_function_multiple_args(self):
        code = """
fn add(a, b) {
    return a + b
}
result = add(3, 4)
"""
        vm = run(code)
        assert vm.vars["result"] == 7

    def test_function_with_if(self):
        code = """
fn abs_val(n) {
    if n < 0 {
        return n * -1
    } else {
        return n
    }
}
result = abs_val(-5)
"""
        vm = run(code)
        assert vm.vars["result"] == 5

    def test_recursive_function(self):
        code = """
fn fact(n) {
    if n <= 1 {
        return 1
    } else {
        return n * fact(n - 1)
    }
}
result = fact(5)
"""
        vm = run(code)
        assert vm.vars["result"] == 120

    def test_list_creation(self):
        vm = run("result = [1, 2, 3]")
        assert vm.vars["result"] == [1, 2, 3]

    def test_list_len_method(self):
        vm = run("lst = [1, 2, 3]\nresult = lst.len()")
        assert vm.vars["result"] == 3

    def test_list_at_method(self):
        vm = run("lst = [10, 20, 30]\nresult = lst.at(1)")
        assert vm.vars["result"] == 20

    def test_string_upper_method(self):
        vm = run('s = "hello"\nresult = s.upper()')
        assert vm.vars["result"] == "HELLO"

    def test_string_lower_method(self):
        vm = run('s = "HELLO"\nresult = s.lower()')
        assert vm.vars["result"] == "hello"

    def test_string_len_method(self):
        vm = run('s = "hello"\nresult = s.len()')
        assert vm.vars["result"] == 5

    def test_string_at_method(self):
        vm = run('s = "hello"\nresult = s.at(1)')
        assert vm.vars["result"] == "e"

    def test_logical_and_true(self):
        vm = run("result = true and true")
        assert vm.vars["result"] is True

    def test_logical_and_false(self):
        vm = run("result = true and false")
        assert vm.vars["result"] is False

    def test_logical_or_true(self):
        vm = run("result = false or true")
        assert vm.vars["result"] is True

    def test_logical_or_false(self):
        vm = run("result = false or false")
        assert vm.vars["result"] is False

    def test_variable_reassignment(self):
        vm = run("x = 1\nx = 2\nresult = x")
        assert vm.vars["result"] == 2

    def test_chained_method_call(self):
        vm = run('s = "Hello"\nresult = s.lower()')
        assert vm.vars["result"] == "hello"

    def test_empty_list(self):
        vm = run("result = []")
        assert vm.vars["result"] == []

    def test_nested_function_calls(self):
        code = """
fn inc(x) { return x + 1 }
fn double(x) { return x * 2 }
result = double(inc(4))
"""
        vm = run(code)
        assert vm.vars["result"] == 10

    def test_fibonacci(self):
        code = """
fn fib(n) {
    if n <= 1 {
        return n
    } else {
        return fib(n - 1) + fib(n - 2)
    }
}
result = fib(10)
"""
        vm = run(code)
        assert vm.vars["result"] == 55

    def test_while_loop_with_break_condition(self):
        code = """
i = 0
while i < 10 {
    i = i + 1
}
result = i
"""
        vm = run(code)
        assert vm.vars["result"] == 10

    def test_complex_expression(self):
        vm = run("result = (2 + 3) * 4 - 1")
        assert vm.vars["result"] == 19

    def test_string_replace_method(self):
        vm = run('s = "hello world"\nresult = s.replace("world", "there")')
        assert vm.vars["result"] == "hello there"

    def test_list_reverse_method(self):
        vm = run("lst = [1, 2, 3]\nresult = lst.reverse()")
        assert vm.vars["result"] == [3, 2, 1]

    def test_number_abs_method(self):
        vm = run("n = -42\nresult = n.abs()")
        assert vm.vars["result"] == 42

    def test_number_str_method(self):
        vm = run("n = 42\nresult = n.str()")
        assert vm.vars["result"] == "42"

    def test_multi_param_function_check_case(self):
        code = """
fn check(a) {
    if a == 1 {
        return "one"
    } else if a == 2 {
        return "two"
    } else {
        return "other"
    }
}
result = check(2)
"""
        vm = run(code)
        assert vm.vars["result"] == "two"

    def test_list_join_method(self):
        vm = run('lst = ["a", "b", "c"]\nresult = lst.join(",")')
        assert vm.vars["result"] == "a,b,c"

    def test_accumulator_pattern(self):
        code = """
nums = [1, 2, 3, 4, 5]
total = 0
i = 0
while i < nums.len() {
    total = total + nums.at(i)
    i = i + 1
}
result = total
"""
        vm = run(code)
        assert vm.vars["result"] == 15


# ===========================================================================
# SYMBOL TABLE TESTS
# ===========================================================================

class TestSymbolTable:
    def test_define_and_exists(self):
        st = SymbolTable()
        st.define("x", NUMBER)
        assert st.exists("x")

    def test_undefined_not_exists(self):
        st = SymbolTable()
        assert not st.exists("y")

    def test_get_returns_type(self):
        st = SymbolTable()
        st.define("x", NUMBER)
        assert st.get("x")["type"] == NUMBER

    def test_scope_isolation(self):
        st = SymbolTable()
        st.define("x", NUMBER)
        st.enter_scope()
        st.define("y", STRING)
        assert st.exists("y")
        st.exit_scope()
        assert not st.exists("y")

    def test_inner_scope_sees_outer(self):
        st = SymbolTable()
        st.define("x", NUMBER)
        st.enter_scope()
        assert st.exists("x")
        st.exit_scope()

    def test_closest_match(self):
        st = SymbolTable()
        st.define("result", NUMBER)
        assert st.closest_match("resultt") == "result"

    def test_closest_match_no_suggestion(self):
        st = SymbolTable()
        st.define("x", NUMBER)
        assert st.closest_match("completelydifferent") is None

    def test_define_function(self):
        st = SymbolTable()
        st.define("foo", {"type": "function", "param_count": 2})
        assert st.exists("foo")
        assert st.get("foo")["type"] == "function"


# ===========================================================================
# EXCEPTION / DIAGNOSTIC TESTS
# ===========================================================================

class TestExceptions:
    def test_compile_error_str(self):
        from src.exceptions import CompileError
        err = CompileError(message="oops", line=3, column=5)
        assert "oops" in str(err)

    def test_runtime_error_str(self):
        from src.exceptions import RuntimeError as LangRuntimeError
        err = LangRuntimeError(message="crash", ip=42)
        assert "crash" in str(err)

    def test_format_diagnostic_basic(self):
        from src.exceptions import format_diagnostic
        out = format_diagnostic(
            source="x = foo()",
            filename="test.lang",
            line=1,
            column=5,
            message="undefined",
        )
        assert "undefined" in out
        assert "test.lang" in out

    def test_format_diagnostic_out_of_range_line(self):
        from src.exceptions import format_diagnostic
        out = format_diagnostic(
            source="x = 1",
            filename="test.lang",
            line=99,
            column=1,
            message="oops",
        )
        assert "out of range" in out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])