from __future__ import annotations

import ast
import builtins
import sys
import typing
from ast import (
    AST,
    Add,
    AnnAssign,
    Assign,
    AsyncFunctionDef,
    Attribute,
    AugAssign,
    BinOp,
    BitAnd,
    BitOr,
    BitXor,
    Call,
    ClassDef,
    Constant,
    Dict,
    Div,
    Expr,
    Expression,
    FloorDiv,
    FunctionDef,
    If,
    Import,
    ImportFrom,
    List,
    Load,
    LShift,
    MatMult,
    Mod,
    Module,
    Mult,
    Name,
    NamedExpr,
    NodeTransformer,
    NodeVisitor,
    Pass,
    Pow,
    Return,
    RShift,
    Starred,
    Store,
    Sub,
    Subscript,
    Tuple,
    Yield,
    YieldFrom,
    alias,
    copy_location,
    expr,
    fix_missing_locations,
    keyword,
    walk,
)
from collections import defaultdict
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, ClassVar, cast, overload

PreliminaryNameTypePair: typing.TypeAlias = tuple[Constant, "expr | None"]
NameTypePair: typing.TypeAlias = tuple[Constant, expr]

generator_names = (
    "typing.Generator",
    "collections.abc.Generator",
    "typing.Iterator",
    "collections.abc.Iterator",
    "typing.Iterable",
    "collections.abc.Iterable",
    "typing.AsyncIterator",
    "collections.abc.AsyncIterator",
    "typing.AsyncIterable",
    "collections.abc.AsyncIterable",
    "typing.AsyncGenerator",
    "collections.abc.AsyncGenerator",
)
anytype_names = (
    "typing.Any",
    "typing_extensions.Any",
)
literal_names = (
    "typing.Literal",
    "typing_extensions.Literal",
)
annotated_names = (
    "typing.Annotated",
    "typing_extensions.Annotated",
)
ignore_decorators = (
    "typing.no_type_check",
    "typeguard.typeguard_ignore",
)
aug_assign_functions = {
    Add: "iadd",
    Sub: "isub",
    Mult: "imul",
    MatMult: "imatmul",
    Div: "itruediv",
    FloorDiv: "ifloordiv",
    Mod: "imod",
    Pow: "ipow",
    LShift: "ilshift",
    RShift: "irshift",
    BitAnd: "iand",
    BitXor: "ixor",
    BitOr: "ior",
}


@dataclass
class TransformMemo:
    node: Module | ClassDef | FunctionDef | AsyncFunctionDef | None
    parent: TransformMemo | None
    path: tuple[str, ...]
    joined_path: Constant = field(init=False)
    return_annotation: expr | None = None
    yield_annotation: expr | None = None
    send_annotation: expr | None = None
    is_async: bool = False
    local_names: set[str] = field(init=False, default_factory=set)
    imported_names: dict[str, str] = field(init=False, default_factory=dict)
    ignored_names: set[str] = field(init=False, default_factory=set)
    load_names: defaultdict[str, dict[str, Name]] = field(
        init=False, default_factory=lambda: defaultdict(dict)
    )
    has_yield_expressions: bool = field(init=False, default=False)
    has_return_expressions: bool = field(init=False, default=False)
    memo_var_name: Name | None = field(init=False, default=None)
    should_instrument: bool = field(init=False, default=True)
    variable_annotations: dict[str, expr] = field(init=False, default_factory=dict)
    configuration_overrides: dict[str, Any] = field(init=False, default_factory=dict)
    code_inject_index: int = field(init=False, default=0)

    def __post_init__(self) -> None:
        elements: list[str] = []
        memo = self
        while isinstance(memo.node, (ClassDef, FunctionDef, AsyncFunctionDef)):
            elements.insert(0, memo.node.name)
            if not memo.parent:
                break

            memo = memo.parent
            if isinstance(memo.node, (FunctionDef, AsyncFunctionDef)):
                elements.insert(0, "<locals>")

        self.joined_path = Constant(".".join(elements))

        # Figure out where to insert instrumentation code
        if self.node:
            for index, child in enumerate(self.node.body):
                if isinstance(child, ImportFrom) and child.module == "__future__":
                    # (module only) __future__ imports must come first
                    continue
                elif (
                    isinstance(child, Expr)
                    and isinstance(child.value, Constant)
                    and isinstance(child.value.value, str)
                ):
                    continue  # docstring

                self.code_inject_index = index
                break

    def get_unused_name(self, name: str) -> str:
        pass

    def is_ignored_name(self, expression: expr | Expr | None) -> bool:
        pass

    def get_memo_name(self) -> Name:
        pass

    def get_import(self, module: str, name: str) -> Name:
        pass

    def insert_imports(self, node: Module | FunctionDef | AsyncFunctionDef) -> None:
        """Insert imports needed by injected code."""
        pass

    def name_matches(self, expression: expr | Expr | None, *names: str) -> bool:
        if expression is None:
            return False

        path: list[str] = []
        top_expression = (
            expression.value if isinstance(expression, Expr) else expression
        )

        if isinstance(top_expression, Subscript):
            top_expression = top_expression.value
        elif isinstance(top_expression, Call):
            top_expression = top_expression.func

        while isinstance(top_expression, Attribute):
            path.insert(0, top_expression.attr)
            top_expression = top_expression.value

        if not isinstance(top_expression, Name):
            return False

        if top_expression.id in self.imported_names:
            translated = self.imported_names[top_expression.id]
        elif hasattr(builtins, top_expression.id):
            translated = "builtins." + top_expression.id
        else:
            translated = top_expression.id

        path.insert(0, translated)
        joined_path = ".".join(path)
        if joined_path in names:
            return True
        elif self.parent:
            return self.parent.name_matches(expression, *names)
        else:
            return False

    def get_config_keywords(self) -> list[keyword]:
        pass


class NameCollector(NodeVisitor):
    def __init__(self) -> None:
        self.names: set[str] = set()

    def visit_Import(self, node: Import) -> None:
        pass

    def visit_ImportFrom(self, node: ImportFrom) -> None:
        pass

    def visit_Assign(self, node: Assign) -> None:
        pass

    def visit_NamedExpr(self, node: NamedExpr) -> Any:
        pass

    def visit_FunctionDef(self, node: FunctionDef) -> None:
        pass

    def visit_ClassDef(self, node: ClassDef) -> None:
        pass


class GeneratorDetector(NodeVisitor):
    """Detects if a function node is a generator function."""

    contains_yields: bool = False
    in_root_function: bool = False

    def visit_Yield(self, node: Yield) -> Any:
        pass

    def visit_YieldFrom(self, node: YieldFrom) -> Any:
        pass

    def visit_ClassDef(self, node: ClassDef) -> Any:
        pass

    def visit_FunctionDef(self, node: FunctionDef | AsyncFunctionDef) -> Any:
        pass

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> Any:
        pass


class AnnotationTransformer(NodeTransformer):
    type_substitutions: ClassVar[dict[str, tuple[str, str]]] = {
        "builtins.dict": ("typing", "Dict"),
        "builtins.list": ("typing", "List"),
        "builtins.tuple": ("typing", "Tuple"),
        "builtins.set": ("typing", "Set"),
        "builtins.frozenset": ("typing", "FrozenSet"),
    }

    def __init__(self, transformer: TypeguardTransformer):
        self.transformer = transformer
        self._memo = transformer._memo
        self._level = 0

    def visit(self, node: AST) -> Any:
        # Don't process Literals
        if isinstance(node, expr) and self._memo.name_matches(node, *literal_names):
            return node

        self._level += 1
        new_node = super().visit(node)
        self._level -= 1

        if isinstance(new_node, Expression) and not hasattr(new_node, "body"):
            return None

        # Return None if this new node matches a variation of typing.Any
        if (
            self._level == 0
            and isinstance(new_node, expr)
            and self._memo.name_matches(new_node, *anytype_names)
        ):
            return None

        return new_node

    def visit_BinOp(self, node: BinOp) -> Any:
        pass

    def visit_Attribute(self, node: Attribute) -> Any:
        pass

    def visit_Subscript(self, node: Subscript) -> Any:
        pass

    def visit_Name(self, node: Name) -> Any:
        pass

    def visit_Call(self, node: Call) -> Any:
        # Don't recurse into calls
        pass

    def visit_Constant(self, node: Constant) -> Any:
        pass


class TypeguardTransformer(NodeTransformer):
    def __init__(
        self, target_path: Sequence[str] | None = None, target_lineno: int | None = None
    ) -> None:
        self._target_path = tuple(target_path) if target_path else None
        self._memo = self._module_memo = TransformMemo(None, None, ())
        self.names_used_in_annotations: set[str] = set()
        self.target_node: FunctionDef | AsyncFunctionDef | None = None
        self.target_lineno = target_lineno

    def generic_visit(self, node: AST) -> AST:
        pass

    @contextmanager
    def _use_memo(
        self, node: ClassDef | FunctionDef | AsyncFunctionDef
    ) -> Generator[None, Any, None]:
        pass

    def _get_import(self, module: str, name: str) -> Name:
        pass

    @overload
    def _convert_annotation(self, annotation: None) -> None: ...

    @overload
    def _convert_annotation(self, annotation: expr) -> expr: ...

    def _convert_annotation(self, annotation: expr | None) -> expr | None:
        pass

    def visit_Name(self, node: Name) -> Name:
        pass

    def visit_Module(self, node: Module) -> Module:
        pass

    def visit_Import(self, node: Import) -> Import:
        pass

    def visit_ImportFrom(self, node: ImportFrom) -> ImportFrom:
        pass

    def visit_ClassDef(self, node: ClassDef) -> ClassDef | None:
        pass

    def visit_FunctionDef(
        self, node: FunctionDef | AsyncFunctionDef
    ) -> FunctionDef | AsyncFunctionDef | None:
        """
        Injects type checks for function arguments, and for a return of None if the
        function is annotated to return something else than Any or None, and the body
        ends without an explicit "return".

        """
        pass

    def visit_AsyncFunctionDef(
        self, node: AsyncFunctionDef
    ) -> FunctionDef | AsyncFunctionDef | None:
        pass

    def visit_Return(self, node: Return) -> Return:
        """This injects type checks into "return" statements."""
        pass

    def visit_Yield(self, node: Yield) -> Yield | Call:
        """
        This injects type checks into "yield" expressions, checking both the yielded
        value and the value sent back to the generator, when appropriate.

        """
        pass

    def visit_AnnAssign(self, node: AnnAssign) -> Any:
        """
        This injects a type check into a local variable annotation-assignment within a
        function body.

        """
        pass

    def visit_Assign(self, node: Assign) -> Any:
        """
        This injects a type check into a local variable assignment within a function
        body. The variable must have been annotated earlier in the function body.

        """
        pass

    def visit_NamedExpr(self, node: NamedExpr) -> Any:
        """This injects a type check into an assignment expression (a := foo())."""
        pass

    def visit_AugAssign(self, node: AugAssign) -> Any:
        """
        This injects a type check into an augmented assignment expression (a += 1).

        """
        pass

    def visit_If(self, node: If) -> Any:
        """
        This blocks names from being collected from a module-level
        "if typing.TYPE_CHECKING:" block, so that they won't be type checked.

        """
        pass
