"""Read a Home Assistant weather entity, for weather-aware art curation.

Reads the current condition of a `weather.*` entity through the Supervisor's
Home Assistant API proxy (needs `homeassistant_api: true` in config.yaml). No
LLM, no external weather API, no key - just the condition string HA already has.
Best-effort: any failure returns None and the caller falls back to seasonal art.
"""
from __future__ import annotations

import logging
import os

import requests

log = logging.getLogger("frame-gallery.weather")

CORE_STATE = "http://supervisor/core/api/states/{}"


def current_condition(entity_id: str) -> str | None:
    """The weather entity's condition (e.g. "rainy", "sunny"), or None.

    HA stores the condition as the entity's state for `weather.*` entities."""
    entity_id = (entity_id or "").strip()
    if not entity_id:
        return None
    token = os.environ.get("SUPERVISOR_TOKEN")
    if not token:
        log.debug("no SUPERVISOR_TOKEN - cannot read %s", entity_id)
        return None
    try:
        r = requests.get(CORE_STATE.format(entity_id),
                         headers={"Authorization": f"Bearer {token}"}, timeout=10)
        r.raise_for_status()
        state = str((r.json() or {}).get("state") or "").strip().lower()
        if not state or state in ("unknown", "unavailable", "none"):
            return None
        return state
    except (requests.RequestException, ValueError) as exc:
        log.warning("could not read weather entity %s: %s", entity_id, exc)
        return None
