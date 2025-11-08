#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utility: Request data validators
"""

from typing import Iterable, Mapping


def validate_request_data(data: Mapping, required_fields: Iterable[str]) -> bool:
    """Validasi bahwa semua required_fields ada dan tidak None/empty string.

    Args:
        data: Mapping request (dict-like)
        required_fields: daftar field wajib

    Returns:
        bool: True jika valid, False jika tidak
    """
    if not isinstance(data, Mapping):
        return False

    for field in required_fields:
        if field not in data:
            return False
        value = data.get(field)
        if value is None:
            return False
        if isinstance(value, str) and value.strip() == "":
            return False
    return True


