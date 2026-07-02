"""Auto-discover entertainment zones from Home Assistant's area registry.

Talks to the HA Core WebSocket API (via the Supervisor proxy) to learn which
area each zigbee2mqtt device sits in, then groups the color-capable Philips
lights by room: one candidate zone per area. Also spots each area's Adaptive
Lighting master switch (``switch.adaptive_lighting_<area>``) so the zone can
pause it automatically while streaming.

The Zigbee side of the picture (friendly names, vendor, color capability)
comes from ``zigbee2mqtt/bridge/devices``, which the bridge already consumes;
this module only adds the HA-side room mapping.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os

import aiohttp

LOG = logging.getLogger("hue_ent.registry")

WS_URL = os.environ.get("HA_WS_URL", "ws://supervisor/core/websocket")


def _slug(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.lower()).strip("_")


async def fetch_area_map() -> dict[str, dict]:
    """Return {ieee: {"area": <name>}} plus {"_al_switches": {area_slug: entity_id}}.

    Raises on any transport/auth error - callers decide how to degrade.
    """
    fixture = os.environ.get("HA_REGISTRY_FIXTURE")
    if fixture:  # dev/test hook: run outside the Supervisor with a canned registry
        with open(fixture, encoding="utf-8") as handle:
            return json.load(handle)

    token = os.environ.get("SUPERVISOR_TOKEN") or os.environ.get("HA_TOKEN")
    if not token:
        raise RuntimeError("no SUPERVISOR_TOKEN/HA_TOKEN for the HA WebSocket API")

    async with aiohttp.ClientSession() as session, session.ws_connect(WS_URL, timeout=15) as ws:
        msg = await ws.receive_json()  # auth_required
        if msg.get("type") != "auth_required":
            raise RuntimeError(f"unexpected WS greeting: {msg.get('type')}")
        await ws.send_json({"type": "auth", "access_token": token})
        msg = await ws.receive_json()
        if msg.get("type") != "auth_ok":
            raise RuntimeError("HA WebSocket auth failed")

        async def command(msg_id: int, cmd: str):
            await ws.send_json({"id": msg_id, "type": cmd})
            while True:
                reply = await ws.receive_json()
                if reply.get("id") == msg_id:
                    if not reply.get("success"):
                        raise RuntimeError(f"{cmd} failed: {reply}")
                    return reply["result"]

        areas = await command(1, "config/area_registry/list")
        devices = await command(2, "config/device_registry/list")
        entities = await command(3, "config/entity_registry/list")

    area_names = {a["area_id"]: a["name"] for a in areas}

    ieee_to_area: dict[str, dict] = {}
    for dev in devices:
        area_id = dev.get("area_id")
        if not area_id or area_id not in area_names:
            continue
        # Z2M devices carry their IEEE in identifiers like
        # ["mqtt", "zigbee2mqtt_0x001788010d94e5db"] and/or a zigbee connection.
        for kind, value in (dev.get("identifiers") or []):
            if kind == "mqtt" and "0x" in str(value):
                ieee = "0x" + str(value).split("0x", 1)[1][:16]
                ieee_to_area[ieee.lower()] = {"area": area_names[area_id]}
        for kind, value in (dev.get("connections") or []):
            if kind == "zigbee":
                ieee_to_area[str(value).lower()] = {"area": area_names[area_id]}

    # Adaptive Lighting master switches, matched by slugified area name.
    al_by_area_slug: dict[str, str] = {}
    slugs = {_slug(name): name for name in area_names.values()}
    for ent in entities:
        entity_id = ent.get("entity_id", "")
        if not entity_id.startswith("switch.adaptive_lighting_"):
            continue
        suffix = entity_id.removeprefix("switch.adaptive_lighting_")
        if suffix in slugs:
            al_by_area_slug[suffix] = entity_id

    ieee_to_area["_al_switches"] = al_by_area_slug
    return ieee_to_area


def synthesize_rooms(z2m_lights: dict[str, dict], area_map: dict[str, dict]) -> list[dict]:
    """Group color-capable Philips lights by area into candidate zones.

    ``z2m_lights``: {friendly_name: {"ieee": str, "color": bool}} (from the
    bridge's view of zigbee2mqtt/bridge/devices).

    Returns a list of room dicts sorted by name:
      {"name", "lights" (sorted), "pause_entities", "skipped" (non-color or >10)}
    """
    al_switches = area_map.get("_al_switches", {})
    rooms: dict[str, dict] = {}
    for friendly_name, info in sorted(z2m_lights.items()):
        entry = area_map.get(str(info.get("ieee", "")).lower())
        if not entry:
            continue
        area = entry["area"]
        room = rooms.setdefault(area, {"name": area, "lights": [], "skipped": []})
        if info.get("color"):
            room["lights"].append(friendly_name)
        else:
            room["skipped"].append(f"{friendly_name} (no color)")

    result = []
    for room in sorted(rooms.values(), key=lambda r: r["name"]):
        if len(room["lights"]) > 10:
            room["skipped"] += [f"{fn} (zone full)" for fn in room["lights"][10:]]
            room["lights"] = room["lights"][:10]
        if not room["lights"]:
            continue
        al = al_switches.get(_slug(room["name"]))
        room["pause_entities"] = [al] if al else []
        result.append(room)
    return result


async def discover_rooms(z2m_lights: dict[str, dict], retries: int = 3) -> list[dict]:
    """Fetch the HA registries (with retries) and synthesize candidate rooms."""
    for attempt in range(retries):
        try:
            area_map = await fetch_area_map()
            rooms = synthesize_rooms(z2m_lights, area_map)
            LOG.info(
                "discovered %d room(s) with color Hue lights: %s",
                len(rooms), ", ".join(r["name"] for r in rooms) or "-",
            )
            return rooms
        except Exception as exc:
            LOG.warning("area discovery failed (%s); attempt %d/%d", exc, attempt + 1, retries)
            await asyncio.sleep(5 * (attempt + 1))
    return []
