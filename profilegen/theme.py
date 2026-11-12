"""The README's shared light and dark palettes."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    card: str
    line: str
    text: str
    muted: str
    accent: str
    ember: str
    link: str
    tagline: str
    site: str
    bar: str
    bar_strong: str
    tile: str
    tile_line: str
    rule: str
    trace: str
    series: tuple[str, str, str]  # LANGUAGE_SLOTS colours, CVD-validated against `card`
    other: str


THEMES: dict[str, Palette] = {
    "dark": Palette(
        card="#0d1117", line="#30363d", text="#e6edf3", muted="#9198a1",
        accent="#f59f1a", ember="#f0703c", link="#58a6ff", tagline="#ffffff", site="#1f6feb",
        bar="#6e7681", bar_strong="#e6edf3",
        tile="rgba(255,255,255,0.02)", tile_line="rgba(255,255,255,0.1)",
        rule="rgba(255,255,255,0.08)", trace="rgba(255,255,255,0.07)",
        series=("#3987e5", "#d95926", "#199e70"), other="#6e7681",
    ),
    "light": Palette(
        card="#ffffff", line="#d0d7de", text="#1f2328", muted="#59636e",
        accent="#b4400c", ember="#c43d0e", link="#0969da", tagline="#1f2328", site="#0550ae",
        bar="#818b98", bar_strong="#1f2328",
        tile="#ffffff", tile_line="rgba(0,0,0,0.1)",
        rule="rgba(0,0,0,0.08)", trace="rgba(0,0,0,0.07)",
        series=("#2a78d6", "#eb6834", "#1baf7a"), other="#818b98",
    ),
}
