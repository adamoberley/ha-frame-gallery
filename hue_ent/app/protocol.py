"""Hue Entertainment Zigbee frame construction (reverse-engineered, cluster 0xFC01).

Wire format verified against live bulbs 2026-07-01/02 (see the project plan):
every command is a manufacturer-specific cluster-specific ZCL command published
through zigbee2mqtt's generic ``zclcommand`` passthrough on
``zigbee2mqtt/<friendly_name>/set``.

- arm     = write manufacturer attribute 0x0005 = 0xFE, then SYNC (cmd 3)
- stream  = cmd 1 to ONE proxy bulb; it re-broadcasts (non-repeating MAC
            broadcast) to every bulb in direct RF range
- stop    = cmd 3 to each bulb (doubles as the sequence-sync command)

The per-frame ``smoothing`` field is a fade time (0xFFFF = 2.56 s); deriving it
from the frame interval is what makes 20-25 fps look continuous. At 25 fps it
computes to 0x0400 - the constant real Hue bridges hardcode.
"""

from __future__ import annotations

import json
import struct

CLUSTER = 0xFC01
MANUFACTURER = 0x100B  # Signify
CMD_STREAM = 1
CMD_SYNC = 3  # sync/stop ("reset" in Bifrost)
SMOOTHING_MAX_US = 2_560_000.0
# Bottom 5 bits of the brightness field: LightRecordMode.Device (0b01011).
# Gradient-strip segments would use mode 0; we only address whole bulbs.
MODE_DEVICE = 0b01011
# Hard protocol limit: 6-byte frame header + 7 bytes/light + 5-byte ZCL header
# hits the ~82-byte single-APS-frame ceiling at exactly 10 lights.
MAX_LIGHTS_PER_FRAME = 10


def zclcommand(cmd: int, data: bytes) -> str:
    """JSON payload for zigbee2mqtt/<name>/set carrying one raw FC01 command."""
    return json.dumps(
        {
            "zclcommand": {
                "cluster": CLUSTER,
                "command": cmd,
                "payload": {"data": list(data)},
                "frametype": 1,
                "options": {
                    "manufacturerCode": MANUFACTURER,
                    "disableDefaultResponse": True,
                },
            }
        }
    )


def arm_write_payload() -> str:
    """Attribute write that precedes the sync when arming a bulb."""
    return json.dumps(
        {
            "write": {
                "cluster": CLUSTER,
                "payload": {
                    "5": {"manufacturerCode": MANUFACTURER, "type": 0x20, "value": 0xFE}
                },
            }
        }
    )


def sync_payload(counter: int) -> str:
    """cmd 3 - arms the sequence counter; also the clean-stop command."""
    return zclcommand(CMD_SYNC, bytes([0, 1]) + struct.pack("<I", counter & 0xFFFFFFFF))


def smoothing_for_fps(fps: float) -> int:
    interval_us = 1_000_000.0 / fps
    return min(0xFFFF, round(interval_us / SMOOTHING_MAX_US * 0xFFFF))


def light_record(nwk_addr: int, bri11: int, x12: int, y12: int) -> bytes:
    """One 7-byte per-bulb record: nwk addr, brightness+mode, packed 12-bit xy."""
    packed = ((bri11 & 0x7FF) << 5) | MODE_DEVICE
    return struct.pack("<HH", nwk_addr, packed) + bytes(
        [x12 & 0xFF, ((x12 >> 8) & 0x0F) | ((y12 & 0x0F) << 4), (y12 >> 4) & 0xFF]
    )


def stream_frame_payload(counter: int, smoothing: int, records: list[bytes]) -> str:
    """cmd 1 - one frame for the whole zone, sent only to the proxy bulb."""
    if len(records) > MAX_LIGHTS_PER_FRAME:
        raise ValueError(
            f"{len(records)} lights exceeds the {MAX_LIGHTS_PER_FRAME}-light frame limit"
        )
    data = struct.pack("<IH", counter & 0xFFFFFFFF, smoothing) + b"".join(records)
    return zclcommand(CMD_STREAM, data)
