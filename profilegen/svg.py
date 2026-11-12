"""Shared SVG helpers. Web fonts don't load in SVG-as-<img>: use these stacks or outlines."""
from __future__ import annotations

import base64
from collections.abc import Sequence
from pathlib import Path

SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Consolas,'Liberation Mono',monospace"
EMOJI = "'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif"


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}"


def stepped(attr: str, steps: Sequence[object], start: float, step: float, final: object) -> str:
    """Discrete animation: hold steps[0] until `start`, advance every `step` s, end on `final`."""
    dur = start + step * len(steps)
    values = [steps[0], *steps, final]
    times = [0.0] + [(start + i * step) / dur for i in range(len(steps))] + [1.0]
    return (f'<animate attributeName="{attr}" calcMode="discrete" dur="{dur:.2f}s" fill="freeze" '
            f'values="{";".join(str(v) for v in values)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}"/>')


def fade_in(at: float, length: float = 0.6) -> str:
    dur = at + length
    return (f'<animate attributeName="opacity" values="0;0;1" keyTimes="0;{at / dur:.4f};1" '
            f'dur="{dur:.2f}s" fill="freeze"/>')
