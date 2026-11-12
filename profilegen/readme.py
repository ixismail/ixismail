"""Rewrites README blocks between `<!-- name:start -->` and `<!-- name:end -->`."""
from __future__ import annotations

import re

from profilegen.config import README


def replace_block(text: str, name: str, block: str) -> str:
    pattern = re.compile(rf"(<!-- {re.escape(name)}:start -->).*?(<!-- {re.escape(name)}:end -->)", re.S)
    if not pattern.search(text):
        raise ValueError(f"README.md has no <!-- {name}:start --> / <!-- {name}:end --> block.")
    inner = f"\n{block}\n" if block else "\n"
    return pattern.sub(lambda m: f"{m.group(1)}{inner}{m.group(2)}", text)


def update_block(name: str, block: str) -> bool:
    """True if README.md changed."""
    text = README.read_text(encoding="utf-8")
    updated = replace_block(text, name, block)
    if updated == text:
        return False
    README.write_text(updated, encoding="utf-8", newline="\n")
    return True
