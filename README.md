# Frame Gallery — a Home Assistant app for Samsung Frame TVs

Curated **public-domain art** on your Frame TV, changed on its own interval.
A ground-up replacement for the older Google/Bing art-changers, fixing their
real annoyances:

- 🎨 **Open museum art, not Google/Bing** — Art Institute of Chicago to start
  (CC0, high-res), with a plug-in source layer for more.
- 🚫 **Family-safe** — public-domain only + a keyword blocklist, and a search to
  shape the collection. No more stray nudes.
- 🔁 **No repeats** — remembers recent pieces; cycles instead of re-rolling.
- 🧹 **No pile-up** — each new piece *replaces* the last (upload → select →
  delete), so the TV's art library stays clean.
- ⏱ **Runs itself** — a long-running service on an interval; no automation.
- 🖼 **Fits the Frame** — mattes any aspect like a framed print, or crops to fill.

> Requires *The Frame* (Art Mode), Home Assistant **OS / Supervised**, and the
> Samsung TV integration set up (or the TV's IP).

## Install

1. **Settings → Add-ons → Add-on Store → ⋮ (top-right) → Repositories**, paste:

   ```
   https://github.com/adamoberley/ha-frame-gallery
   ```
2. Install **Frame Gallery**, **Start** it, and accept the prompts on the TV.

Usually no configuration is needed — it auto-discovers your Frame. See
[`frame_gallery/DOCS.md`](frame_gallery/DOCS.md) for options.

## Status

v0.1 — Art Institute of Chicago source. Roadmap: more sources (Met, Rijksmuseum,
Smithsonian, Wikimedia, Unsplash), department/collection pickers, and a circadian
mat. Built on lessons from the [Bird Frame](https://github.com/adamoberley/HABirdDashboard)
add-on (the `samsungtvws` upload→select→delete path, art-mode-aware push,
auto-discovery).

## License

MIT (the code). Artwork is the respective source's; public-domain works are CC0.
