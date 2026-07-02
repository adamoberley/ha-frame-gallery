# Changelog

## 0.1.0 — 2026-07-02

Initial release.

- Streams LedFX DDP output to Philips Hue bulbs on zigbee2mqtt at 20–25 fps via
  the reverse-engineered Hue Entertainment Zigbee protocol (cluster 0xFC01
  through Z2M's `zclcommand` passthrough — stock Z2M ≥ 2.1.1, no Hue Bridge).
- Per-zone configuration (up to 10 bulbs/zone), one DDP listener per zone,
  proxy-bulb fan-out, per-zone fps with matched smoothing.
- One `Entertainment: <zone>` switch per zone via MQTT discovery; arming
  captures bulb states and pauses configured entities (e.g. Adaptive
  Lighting), disarming restores everything.
- Auto-start on incoming DDP, idle auto-stop, automatic re-arm after gaps,
  keep-alive frames during static scenes.
