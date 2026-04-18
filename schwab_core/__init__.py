"""
Stable import path `schwab_core.*` for subpackages installed at repo top level.

The setuptools layout exposes `calculations`, `transformers`, etc. as top-level
packages. This module aliases them under `schwab_core` for consistent imports.
"""
import importlib
import sys

# calculations.pnl imports schwab_core.utils.constants — register utils first
_utils = importlib.import_module("utils")
sys.modules["schwab_core.utils"] = _utils
_constants = importlib.import_module("utils.constants")
sys.modules["schwab_core.utils.constants"] = _constants

for _name in ("calculations", "transformers", "position", "strategy", "symbol"):
    _mod = importlib.import_module(_name)
    sys.modules[f"schwab_core.{_name}"] = _mod

__all__ = ["calculations", "transformers", "position", "strategy", "symbol", "utils"]
