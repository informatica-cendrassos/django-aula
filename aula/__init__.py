# This Python file uses the following encoding: utf-8

# amorilla@xtec.cat
# Configura l'idioma correcte per les dates

import locale
from copy import copy
from copyreg import _slotnames
from itertools import chain

from django.conf import settings
from django.template.context import BaseContext, Context


def _patched_base_context_copy(self):
    duplicate = self.__class__.__new__(self.__class__)
    if hasattr(self, "__dict__"):
        duplicate.__dict__.update(self.__dict__)

    slot_names = chain.from_iterable(
        _slotnames(cls) for cls in self.__class__.mro() if _slotnames(cls)
    )
    for slot_name in slot_names:
        if slot_name in {"dicts", "__dict__", "__weakref__"}:
            continue
        if hasattr(self, slot_name):
            setattr(duplicate, slot_name, copy(getattr(self, slot_name)))

    duplicate.dicts = self.dicts[:]
    return duplicate


def _apply_base_context_copy_patch_if_needed():
    try:
        copy(Context())
    except AttributeError as exc:
        if "super" in str(exc) and "dicts" in str(exc):
            BaseContext.__copy__ = _patched_base_context_copy

try:
    locale.setlocale(locale.LC_TIME, settings.CUSTOM_LC_TIME)
except (AttributeError, locale.Error):
    pass

_apply_base_context_copy_patch_if_needed()
