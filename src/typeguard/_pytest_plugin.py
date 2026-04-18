from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING, Any, Literal

from typeguard._config import CollectionCheckStrategy, ForwardRefPolicy, global_config
from typeguard._exceptions import InstrumentationWarning
from typeguard._importhook import install_import_hook
from typeguard._utils import qualified_name, resolve_reference

if TYPE_CHECKING:
    from pytest import Config, Parser


def pytest_addoption(parser: Parser) -> None:
    pass


def pytest_configure(config: Config) -> None:
    pass
