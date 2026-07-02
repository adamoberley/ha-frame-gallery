# Hue Entertainment

Streams LedFX effects to Philips Hue Zigbee bulbs paired to **zigbee2mqtt** (no
Hue Bridge) at 20–25 fps. The naive path — one MQTT `set` per bulb per frame —
tops out around 6 fps and floods the Zigbee queue. This app instead speaks the
reverse-engineered **Hue Entertainment** protocol: one compact Zigbee frame per
zone per tick, unicast to a single *proxy* bulb that re-broadcasts to the rest.
Bulbs interpolate between targets, so 20–25 fps looks continuous.

## Requirements

- zigbee2mqtt **2.1.1 or newer** (for the `zclcommand` passthrough; any recent
  version qualifies).
- Color-capable Philips Hue bulbs on recent firmware, paired to zigbee2mqtt.
- The LedFX app (or any DDP sender) running on the same host network.

## Zones

A zone is a group of up to **10** bulbs driven together (a hard limit of the
Zigbee frame format). Configure one zone per room:

```yaml
zones:
  - name: Living Room
    lights:
      - hue_living_room_bulb_1
      - hue_living_room_bulb_2
      - hue_living_room_floor_lamp
    proxy: hue_living_room_bulb_1
    fps: 20
    ddp_port: 4048
    auto_start: true
    idle_timeout_s: 30
    pause_entities:
      - switch.adaptive_lighting_living_room
```

- **lights** — zigbee2mqtt *friendly names*, in pixel order. Arrange them along
  the room so LedFX's one-dimensional effects sweep spatially.
- **proxy** — the bulb that receives the stream and re-broadcasts it. Every
  other bulb in the zone must be in direct radio range of it. Pick a central,
  always-powered bulb. Defaults to the first light.
- **fps** — 20 is a good default; 25 is the practical ceiling (it is also the
  rate a real Hue Bridge streams at). Lower values still look smooth.
- **ddp_port** — the UDP port this zone listens on for DDP. Each zone needs its
  own. Defaults to 4048 + zone index.
- **auto_start** — arm automatically when DDP frames arrive (default on). The
  zone always disarms itself after `idle_timeout_s` without frames.
- **pause_entities** — entities turned **off** while the zone streams and back
  **on** afterwards. Put your room's Adaptive Lighting switch here, otherwise
  it will fight the stream.
- **brightness_scale** — global dimmer for the streamed output (0.05–1.0).

## LedFX setup

For each zone, add a **DDP** device in LedFX:

- *IP address*: the Home Assistant host address (both apps use host networking,
  so `127.0.0.1` works when LedFX runs on the same box).
- *Port*: the zone's `ddp_port`.
- *Pixel count*: the zone's number of lights.
- *Refresh rate*: match the zone's `fps`.

Then play any effect on that device. With `auto_start` on, the zone arms as
soon as frames flow and releases the lights after `idle_timeout_s` (default
30 s) once they stop.

## Home Assistant control

Each zone appears as a switch — named after the zone, so it shows up as
**Hue Entertainment \<zone\>** (e.g. *Hue Entertainment Living Room*) — via MQTT
discovery. Turning it on arms the zone (captures each bulb's current state,
pauses `pause_entities`, starts streaming); turning it off stops streaming and
**restores every bulb to its pre-session state**. Only one zone streams at a
time; arming a second zone stops the first.

**Off means off.** If you switch a zone off by hand while LedFX is still
sending, it stays off — it won't immediately re-arm from the live stream. It
arms again automatically only once that stream stops and a *new* one begins (or
when you turn the switch back on). So you can silence a room mid-song without
fighting the auto-start.

Stopping or restarting the app disarms every zone cleanly first, restoring the
bulbs — they won't get stranded mid-effect.

Automation ideas: turn the switch on when your media player starts and off when
it stops, or expose it on a dashboard next to your LedFX panel.

## How it works / limits

- Uses zigbee2mqtt as a dumb relay (`zclcommand` on `<friendly_name>/set`) —
  cluster 0xFC01, manufacturer 0x100B (Signify). No custom Z2M fork, no special
  coordinator firmware; verified on a TI CC2652 (Z-Stack 3).
- ~25 updates/sec is the protocol's practical ceiling — coarser than a WLED
  strip but plenty for music-reactive room lighting.
- While a zone streams, normal commands to those bulbs still get through and
  will fight the stream — hence `pause_entities` and the state restore.
- White-ambiance-only bulbs cannot render color streams; leave them out.
