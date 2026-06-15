"""Auto-discover the Frame TV's IP so the user types nothing.

Reads the Samsung TV integration's own stored connection info from Home
Assistant's config (mounted read-only) - the same host the core `samsungtv`
integration uses. Returns every Samsung TV entry, so multiple Frames are found
automatically; non-Art-Mode TVs are filtered out later at push time. Read-only.
"""
from __future__ import annotations

import json
import logging
import os

log = logging.getLogger("frame-gallery.discover")

CONFIG_ENTRIES_PATHS = (
    "/homeassistant/.storage/core.config_entries",
    "/config/.storage/core.config_entries",
)


def discover_tv_hosts(explicit: str) -> list[str]:
    """Comma-separated `explicit` wins; else read every samsungtv host from HA's
    config entries (read-only). Returns [] if none found."""
    if explicit.strip():
        return [h.strip() for h in explicit.split(",") if h.strip()]

    for path in CONFIG_ENTRIES_PATHS:
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, ValueError) as exc:
            log.warning("could not read %s: %s", path, exc)
            continue
        entries = (data.get("data") or {}).get("entries") or []
        hosts = []
        for entry in entries:
            if entry.get("domain") != "samsungtv":
                continue
            host = (entry.get("data") or {}).get("host")
            if host:
                model = (entry.get("data") or {}).get("model", "")
                hosts.append(host)
                log.info("found Samsung TV in HA config: %s (%s)", host, model or "?")
        if hosts:
            return hosts
        log.warning("no samsungtv entries in %s", path)
        return []
    log.warning("HA config not readable for TV discovery - set tv_ip manually "
                "(check the homeassistant_config map)")
    return []
