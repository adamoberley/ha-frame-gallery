# Changelog

## 0.3.0 — 2026-07-02

- **Auto zones**: color-capable Hue bulbs are grouped by Home Assistant area —
  one zone per room, with the room's Adaptive Lighting switch auto-detected as
  a pause entity. Zero-config first run.
- **Sidebar zone editor** (ingress): reorder lights into pixel order with a
  per-bulb **Blink** identifier, pick the proxy, set fps/brightness, enable or
  disable rooms, and test-stream a zone — changes apply live, no restart.
- DDP ports are allocated once per zone and remembered, so LedFX devices never
  churn when rooms change. New option: `auto_zones` (default on); manual
  `zones:` still supported and win on name collision.

## 0.2.0 — 2026-07-02

- **LedFX auto-provisioning**: the app now creates one matching DDP device per
  zone in LedFX via its API (named `Hue <zone>`, right port/pixel count/fps) —
  configure zones once, pick effects in LedFX, done. Idempotent; devices that
  drift from their zone config are recreated. New options: `ledfx_url`
  (empty = off) and `ledfx_ddp_target` for remote setups.

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
