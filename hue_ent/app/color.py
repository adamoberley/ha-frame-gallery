"""sRGB pixel -> Hue Entertainment (12-bit CIE xy + 11-bit brightness).

Uses the direct 12-bit quantization with Bifrost's experimentally determined
wide-gamut divisors (x/0.7347, y/0.8264) rather than BambiHeavy's lossier
10-bit intermediate step. Brightness is the max linear channel, clamped to a
floor of 1 (0 has undefined behavior on some firmware).
"""

from __future__ import annotations

WIDE_GAMUT_MAX_X = 0.7347
WIDE_GAMUT_MAX_Y = 0.8264
D65 = (0.3127, 0.3290)


def rgb8_to_entertainment(
    r: int, g: int, b: int, gamma: float = 2.2, brightness_scale: float = 1.0
) -> tuple[int, int, int]:
    """Return (bri11, x12, y12) for one 8-bit-per-channel sRGB pixel."""
    rl = (r / 255.0) ** gamma
    gl = (g / 255.0) ** gamma
    bl = (b / 255.0) ** gamma

    # sRGB (D65) -> XYZ, IEC 61966-2-1
    big_x = 0.4124 * rl + 0.3576 * gl + 0.1805 * bl
    big_y = 0.2126 * rl + 0.7152 * gl + 0.0722 * bl
    big_z = 0.0193 * rl + 0.1192 * gl + 0.9505 * bl
    total = big_x + big_y + big_z
    x, y = (big_x / total, big_y / total) if total > 0 else D65

    bri = max(1, min(2047, round(max(rl, gl, bl) * 2047 * brightness_scale)))
    x12 = max(0, min(4095, round(x / WIDE_GAMUT_MAX_X * 4095)))
    y12 = max(0, min(4095, round(y / WIDE_GAMUT_MAX_Y * 4095)))
    return bri, x12, y12
