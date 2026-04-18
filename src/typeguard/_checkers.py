from __future__ import annotations

import collections.abc
import inspect
import sys
import types
import typing
import warnings
from collections.abc import Mapping, MutableMapping, Sequence
from enum import Enum
from inspect import Parameter, isclass, isfunction
from io import BufferedIOBase, IOBase, RawIOBase, TextIOBase
from itertools import zip_longest
from textwrap import indent
from typing import (
    IO,
    AbstractSet,
    Annotated,
    Any,
    BinaryIO,
    Callable,
    Dict,
    ForwardRef,
    List,
    NewType,
    Optional,
    Set,
    TextIO,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from unittest.mock import Mock

import typing_extensions

# Must use this because typing.is_typeddict does not recognize
# TypedDict from typing_extensions, and as of version 4.12.0
# typing_extensions.TypedDict is different from typing.TypedDict
# on all versions.
from typing_extensions import is_typeddict

from ._config import ForwardRefPolicy
from ._exceptions import TypeCheckError, TypeHintWarning
from ._memo import TypeCheckMemo
from ._utils import evaluate_forwardref, get_stacklevel, get_type_name, qualified_name

if sys.version_info >= (3, 15):
    from typing import NoExtraItems
else:
    from typing_extensions import NoExtraItems

if sys.version_info >= (3, 11):
    from typing import (
        NotRequired,
        Required,
        TypeAlias,
        get_args,
        get_origin,
    )

    SubclassableAny = Any
else:
    from typing_extensions import Any as SubclassableAny
    from typing_extensions import (
        NotRequired,
        Required,
        TypeAlias,
        get_args,
        get_origin,
    )

if sys.version_info >= (3, 10):
    from importlib.metadata import entry_points
    from typing import ParamSpec
else:
    from importlib_metadata import entry_points
    from typing_extensions import ParamSpec

TypeCheckerCallable: TypeAlias = Callable[
    [Any, Any, Tuple[Any, ...], TypeCheckMemo], Any
]
TypeCheckLookupCallback: TypeAlias = Callable[
    [Any, Tuple[Any, ...], Tuple[Any, ...]], Optional[TypeCheckerCallable]
]

checker_lookup_functions: list[TypeCheckLookupCallback] = []
generic_alias_types: tuple[type, ...] = (
    type(List),
    type(List[Any]),
    types.GenericAlias,
)

# Sentinel
_missing = object()

# Lifted from mypy.sharedparse
BINARY_MAGIC_METHODS = {
    "__add__",
    "__and__",
    "__cmp__",
    "__divmod__",
    "__div__",
    "__eq__",
    "__floordiv__",
    "__ge__",
    "__gt__",
    "__iadd__",
    "__iand__",
    "__idiv__",
    "__ifloordiv__",
    "__ilshift__",
    "__imatmul__",
    "__imod__",
    "__imul__",
    "__ior__",
    "__ipow__",
    "__irshift__",
    "__isub__",
    "__itruediv__",
    "__ixor__",
    "__le__",
    "__lshift__",
    "__lt__",
    "__matmul__",
    "__mod__",
    "__mul__",
    "__ne__",
    "__or__",
    "__pow__",
    "__radd__",
    "__rand__",
    "__rdiv__",
    "__rfloordiv__",
    "__rlshift__",
    "__rmatmul__",
    "__rmod__",
    "__rmul__",
    "__ror__",
    "__rpow__",
    "__rrshift__",
    "__rshift__",
    "__rsub__",
    "__rtruediv__",
    "__rxor__",
    "__sub__",
    "__truediv__",
    "__xor__",
}


def check_callable(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_mapping(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_typed_dict(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_list(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_sequence(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_set(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_tuple(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    # Specialized check for NamedTuples
    pass


def check_union(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_uniontype(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_class(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_newtype(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_instance(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_typevar(
    value: Any,
    origin_type: TypeVar,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
    *,
    subclass_check: bool = False,
) -> None:
    pass


def _is_literal_type(typ: object) -> bool:
    pass


def check_literal(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_literal_string(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_typeguard(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_none(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_number(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_io(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_signature_compatible(subject: type, protocol: type, attrname: str) -> None:
    pass


def check_protocol(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_byteslike(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_self(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass


def check_paramspec(
    value: Any,
    origin_type: Any,
    args: tuple[Any, ...],
    memo: TypeCheckMemo,
) -> None:
    pass  # No-op for now


def check_type_internal(
    value: Any,
    annotation: Any,
    memo: TypeCheckMemo,
) -> None:
    """
    Check that the given object is compatible with the given type annotation.

    This function should only be used by type checker callables. Applications should use
    :func:`~.check_type` instead.

    :param value: the value to check
    :param annotation: the type annotation to check against
    :param memo: a memo object containing configuration and information necessary for
        looking up forward references
    """

    if isinstance(annotation, ForwardRef):
        try:
            annotation = evaluate_forwardref(annotation, memo)
        except NameError:
            if memo.config.forward_ref_policy is ForwardRefPolicy.ERROR:
                raise
            elif memo.config.forward_ref_policy is ForwardRefPolicy.WARN:
                warnings.warn(
                    f"Cannot resolve forward reference {annotation.__forward_arg__!r}",
                    TypeHintWarning,
                    stacklevel=get_stacklevel(),
                )

            return

    if type(annotation) in type_alias_types:
        annotation = annotation.__value__

    if annotation is Any or annotation is SubclassableAny or isinstance(value, Mock):
        return

    # Skip type checks if value is an instance of a class that inherits from Any
    if not isclass(value) and SubclassableAny in type(value).__bases__:
        return

    extras: tuple[Any, ...]
    origin_type = get_origin(annotation)
    if origin_type is Annotated:
        annotation, *extras_ = get_args(annotation)
        extras = tuple(extras_)
        origin_type = get_origin(annotation)
    else:
        extras = ()

    if origin_type is not None:
        args = get_args(annotation)

        # Compatibility hack to distinguish between unparametrized and empty tuple
        # (tuple[()]), necessary due to https://github.com/python/cpython/issues/91137
        if origin_type in (tuple, Tuple) and annotation is not Tuple and not args:
            args = ((),)
    else:
        origin_type = annotation
        args = ()

    for lookup_func in checker_lookup_functions:
        checker = lookup_func(origin_type, args, extras)
        if checker:
            checker(value, origin_type, args, memo)
            return

    if isclass(origin_type):
        if not isinstance(value, origin_type):
            raise TypeCheckError(f"is not an instance of {qualified_name(origin_type)}")
    elif type(origin_type) is str:  # noqa: E721
        warnings.warn(
            f"Skipping type check against {origin_type!r}; this looks like a "
            f"string-form forward reference imported from another module",
            TypeHintWarning,
            stacklevel=get_stacklevel(),
        )


# Equality checks are applied to these
origin_type_checkers: dict[
    Any, Callable[[Any, Any, tuple[Any, ...], TypeCheckMemo], None]
] = {
    bytes: check_byteslike,
    AbstractSet: check_set,
    BinaryIO: check_io,
    Callable: check_callable,
    collections.abc.Callable: check_callable,
    complex: check_number,
    dict: check_mapping,
    Dict: check_mapping,
    float: check_number,
    frozenset: check_set,
    IO: check_io,
    list: check_list,
    List: check_list,
    typing.Literal: check_literal,
    Mapping: check_mapping,
    MutableMapping: check_mapping,
    None: check_none,
    collections.abc.Mapping: check_mapping,
    collections.abc.MutableMapping: check_mapping,
    Sequence: check_sequence,
    collections.abc.Sequence: check_sequence,
    collections.abc.Set: check_set,
    set: check_set,
    Set: check_set,
    TextIO: check_io,
    tuple: check_tuple,
    Tuple: check_tuple,
    type: check_class,
    Type: check_class,
    Union: check_union,
    # On some versions of Python, these may simply be re-exports from "typing",
    # but exactly which Python versions is subject to change.
    # It's best to err on the safe side and just always specify these.
    typing_extensions.Literal: check_literal,
    typing_extensions.LiteralString: check_literal_string,
    typing_extensions.Self: check_self,
    typing_extensions.TypeGuard: check_typeguard,
}
if sys.version_info >= (3, 10):
    origin_type_checkers[types.UnionType] = check_uniontype
    origin_type_checkers[typing.TypeGuard] = check_typeguard

if sys.version_info >= (3, 11):
    origin_type_checkers.update(
        {typing.LiteralString: check_literal_string, typing.Self: check_self}
    )

if sys.version_info >= (3, 12):
    type_alias_types = (typing_extensions.TypeAliasType, typing.TypeAliasType)
else:
    type_alias_types = (typing_extensions.TypeAliasType,)


def builtin_checker_lookup(
    origin_type: Any, args: tuple[Any, ...], extras: tuple[Any, ...]
) -> TypeCheckerCallable | None:
    pass


checker_lookup_functions.append(builtin_checker_lookup)


def load_plugins() -> None:
    """
    Load all type checker lookup functions from entry points.

    All entry points from the ``typeguard.checker_lookup`` group are loaded, and the
    returned lookup functions are added to :data:`typeguard.checker_lookup_functions`.

    .. note:: This function is called implicitly on import, unless the
        ``TYPEGUARD_DISABLE_PLUGIN_AUTOLOAD`` environment variable is present.
    """

    for ep in entry_points(group="typeguard.checker_lookup"):
        try:
            plugin = ep.load()
        except Exception as exc:
            warnings.warn(
                f"Failed to load plugin {ep.name!r}: {qualified_name(exc)}: {exc}",
                stacklevel=2,
            )
            continue

        if not callable(plugin):
            warnings.warn(
                f"Plugin {ep} returned a non-callable object: {plugin!r}", stacklevel=2
            )
            continue

        checker_lookup_functions.insert(0, plugin)
