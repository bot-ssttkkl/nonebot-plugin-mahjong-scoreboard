from typing import Type

from injector import Injector, Module

_modules = []
_inj = None


def add_module(module: Type[Module]):
    if _inj is not None:
        raise RuntimeError("cannot add module after injector was initialized")
    _modules.append(module)
    return module


def inj():
    global _inj
    if _inj is None:
        _inj = Injector(_modules)
    return _inj


__all__ = ("inj", "add_module")
