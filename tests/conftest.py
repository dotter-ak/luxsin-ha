"""Pytest configuration: make api.py and const.py importable without
needing the full `homeassistant` package installed.

Neither module depends on `homeassistant` itself (api.py only needs
`aiohttp` plus the standard library; const.py has no dependencies at
all), so their pure logic can be unit-tested in isolation - but a plain
`import custom_components.luxsin.api` would first execute
`custom_components/luxsin/__init__.py`, which *does* import
`homeassistant`. So both modules are loaded directly by file path
instead, bypassing the package `__init__.py` entirely.
"""
import importlib.util
import sys
from pathlib import Path

_LUXSIN_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "luxsin"


def _load(module_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(module_name, _LUXSIN_DIR / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_load("luxsin_api", "api.py")
_load("luxsin_const", "const.py")
