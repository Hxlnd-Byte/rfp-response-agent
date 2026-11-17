"""Small charts drawn as SVG by plain code. No chart library, nothing loaded from the internet."""
from __future__ import annotations

import html
import math

E = html.escape


def _wrap(label: str, width: int = 15) -> list[str]:
    lines, cur = [], ""
    for word in label.split():
        if cur and len(cur) + len(word) + 1 > width:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    return lines + [cur] if cur else lines


def donut(parts: list[tuple[str, int, str]], centre: str, sub: str, size: int = 190) -> str:
    total = sum(v for _, v, _ in parts) or 1
    r, c, w = size / 2 - 16, size / 2, 26
    circ, off, out = 2 * math.pi * r, 0.0, []
    for _, v, col in parts:
        if v:
            out.append(f'<circle cx="{c}" cy="{c}" r="{r}" fill="none" stroke="{col}" stroke-width="{w}" stroke-dasharray="{v / total * circ:.2f} {circ:.2f}" '
                       f'stroke-dashoffset="{-off:.2f}" transform="rotate(-90 {c} {c})"/>')
            off += v / total * circ
    return (f'<svg viewBox="0 0 {size} {size}" width="{size}" height="{size}" role="img" aria-label="{E(sub)}">{"".join(out)}'
            f'<text x="{c}" y="{c + 4}" text-anchor="middle" font-size="34" font-weight="700" fill="#1b1f3b">{E(centre)}</text>'
            f'<text x="{c}" y="{c + 24}" text-anchor="middle" font-size="12" fill="#6b7190">{E(sub)}</text></svg>')


def radar(axes: list[str], series: list[tuple[str, str, list[float]]], top: float = 3, size: int = 330) -> str:
    """One shape per series. Only use axes where every series has a real value."""
    n, c, r = len(axes), size / 2, size / 2 - 70
    pt = lambda i, v: (c + r * v / top * math.sin(2 * math.pi * i / n), c - r * v / top * math.cos(2 * math.pi * i / n))
    out = []
    for level in (1, 2, 3):
        ring = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, level) for i in range(n)))
        out.append(f'<polygon points="{ring}" fill="none" stroke="#e3e6f3" stroke-width="1"/>')
    for i, label in enumerate(axes):
        x, y = pt(i, top)
        out.append(f'<line x1="{c}" y1="{c}" x2="{x:.1f}" y2="{y:.1f}" stroke="#e3e6f3"/>')
        lx, ly = pt(i, top * 1.2)
        anchor = "middle" if abs(lx - c) < 12 else ("start" if lx > c else "end")
        lines = _wrap(label)
        spans = "".join(f'<tspan x="{lx:.1f}" dy="{0 if k == 0 else 12}">{E(t)}</tspan>' for k, t in enumerate(lines))
        out.append(f'<text x="{lx:.1f}" y="{ly - 6 * (len(lines) - 1):.1f}" text-anchor="{anchor}" font-size="10.5" fill="#4a5073">{spans}</text>')
    for name, col, vals in series:
        pts = [pt(i, v) for i, v in enumerate(vals)]
        out.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{col}" fill-opacity="0.18" stroke="{col}" stroke-width="2.5" stroke-linejoin="round"/>')
        out += [f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{col}"/>' for x, y in pts]
    return f'<svg viewBox="-50 0 {size + 100} {size}" width="100%" style="max-width:{size + 100}px" role="img" aria-label="Comparison on topics with evidence">{"".join(out)}</svg>'


def bars(rows: list[tuple[str, float, str, str]], unit: str = "") -> str:
    """Horizontal bars: (label, value 0..1, colour, text at the end)."""
    out, y = [], 0
    for label, v, col, end in rows:
        out.append(f'<text x="0" y="{y + 15}" font-size="12.5" fill="#1b1f3b">{E(label)}</text>'
                   f'<rect x="210" y="{y + 3}" width="260" height="14" rx="7" fill="#eef0fa"/>'
                   f'<rect x="210" y="{y + 3}" width="{max(4, 260 * v):.0f}" height="14" rx="7" fill="{col}"/>'
                   f'<text x="480" y="{y + 15}" font-size="12.5" fill="#4a5073">{E(end)}</text>')
        y += 28
    return f'<svg viewBox="0 0 560 {max(y, 28)}" width="100%" style="max-width:560px" role="img">{"".join(out)}</svg>'
