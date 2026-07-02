"""Auto-provision matching DDP devices in LedFX.

The bridge already knows everything LedFX needs per zone (port, pixel count,
frame rate), so instead of making the user mirror each zone by hand in the
LedFX UI, we create the devices through LedFX's REST API: one DDP device named
``Hue <zone>`` per zone (LedFX auto-creates a matching virtual). Idempotent -
an existing device with the right settings is left completely alone (including
whatever effect the user put on it); a device whose settings drifted from the
zone config is deleted and recreated (which resets its effect - logged).

LedFX may boot after us, so provisioning retries until the API answers.
"""

from __future__ import annotations

import asyncio
import json
import logging
import urllib.error
import urllib.request

LOG = logging.getLogger("hue_ent.ledfx")

RETRY_S = 30.0


def _request(url: str, method: str = "GET", body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def desired_config(zone, target_ip: str) -> dict:
    return {
        "name": f"Hue {zone.name}",
        "ip_address": target_ip,
        "port": zone.ddp_port,
        "pixel_count": len(zone.lights),
        "refresh_rate": int(zone.fps),
    }


def _matches(existing: dict, want: dict) -> bool:
    return all(existing.get(key) == value for key, value in want.items())


def _provision_once(base_url: str, target_ip: str, zones) -> None:
    """One synchronous pass; raises on API errors so the caller can retry."""
    listing = _request(f"{base_url}/api/devices")
    devices = listing.get("devices", listing) or {}

    by_name: dict[str, tuple[str, dict]] = {}
    for dev_id, dev in devices.items():
        if isinstance(dev, dict):
            cfg = dev.get("config", dev)
            if isinstance(cfg, dict) and cfg.get("name"):
                by_name[cfg["name"]] = (dev_id, cfg)

    for zone in zones:
        want = desired_config(zone, target_ip)
        existing = by_name.get(want["name"])
        if existing is not None:
            dev_id, cfg = existing
            if _matches(cfg, want):
                LOG.debug("[%s] LedFX device '%s' already in sync", zone.name, want["name"])
                continue
            LOG.warning(
                "[%s] LedFX device '%s' drifted from zone config - recreating "
                "(its effect selection resets)", zone.name, want["name"],
            )
            _request(f"{base_url}/api/devices/{dev_id}", method="DELETE")
        _request(f"{base_url}/api/devices", method="POST", body={"type": "ddp", "config": want})
        LOG.info(
            "[%s] created LedFX DDP device '%s' (%s:%d, %d px, %d fps)",
            zone.name, want["name"], target_ip, want["port"],
            want["pixel_count"], want["refresh_rate"],
        )


async def provision_forever(base_url: str, target_ip: str, zones) -> None:
    """Retry until one full pass succeeds (LedFX may still be booting)."""
    base_url = base_url.rstrip("/")
    while True:
        try:
            await asyncio.to_thread(_provision_once, base_url, target_ip, zones)
            LOG.info("LedFX provisioning complete (%s)", base_url)
            return
        except (urllib.error.URLError, OSError, json.JSONDecodeError, KeyError) as exc:
            LOG.info(
                "LedFX not reachable yet at %s (%s) - retrying in %.0fs", base_url, exc, RETRY_S
            )
        except Exception:
            LOG.exception("LedFX provisioning failed - retrying in %.0fs", RETRY_S)
        await asyncio.sleep(RETRY_S)
