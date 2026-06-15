# Frame Gallery

Curated **public-domain art on your Samsung Frame TV**, changed on its own
interval — no Google/Bing, no automation, no pile-up, no repeats, and content
you can filter.

Built after a real round of getting Frame TV art-pushing right. It fixes the
common annoyances of the older art-changers:

| Old art-changer problem | Frame Gallery |
| --- | --- |
| Random **nudes** from Google Art | Public-domain museum art + a keyword blocklist (and a search to shape the collection). |
| The **same pieces** over and over | Remembers the last N shown; never repeats until the pool is exhausted. |
| Uploads **pile up** in the art library | Upload → select → **delete the previous one**. One image, swapped in place. |
| Needed an **automation** to run | A long-running service with its own interval. |

## How it works

Each interval (or when you press **Show next** on the panel) it asks an open
museum API for a batch of works, filters them (public-domain, keyword blocklist,
not shown recently), downloads one, fits it to your panel (matted like a framed
print, or cropped to fill), and pushes it to the Frame — deleting the piece it
replaces. Source for v0.1: the **Art Institute of Chicago** (no key, CC0 IIIF
images). The source layer is a plug-in, so more museums can be added.

## Setup

1. **Install** this app (you added the repo under *Settings → Add-ons → ⋮ →
   Repositories*).
2. Usually **no config needed** — it auto-discovers your Frame from the Samsung
   TV integration. Optionally set **Art search** to taste (e.g. `landscape`).
3. **Start** it, with the TV **on** and the remote handy: accept the
   *"Allow connection?"* (and, first time, the TV's **Art Store terms**) prompts.
4. Put the TV in **Art Mode**. A new piece appears each interval.

## Options

| Option | What it does |
| --- | --- |
| `query` | Free-text search to shape the collection (blank = all public domain). |
| `public_domain_only` | Only CC0 works (recommended). |
| `exclude_keywords` | Family-safe blocklist (default: nude, naked, …). |
| `interval_minutes` | How often the art changes. |
| `fit` | `matte` (framed, nothing cropped) or `crop` (fill, trim edges). |
| `mat_color` | Mat colour behind matted art (hex). |
| `avoid_repeat_count` | How many recent pieces to never repeat. |
| `active_hours` | e.g. `07:00-23:00`; blank = 24/7. |
| `tv_ip` | Blank = auto-discover; or comma-separated IPs. |

The sidebar **Frame Gallery** panel shows the current piece and a **Show next
now** button for instant changes.

## Troubleshooting

- **`ms.channel.timeOut` / first upload fails** — accept the **Allow** and the
  **Art Store terms** prompts on the TV (it blocks uploads until you do).
- **"no artwork found"** — your `query` is too narrow, or excluded by keywords;
  broaden it or clear `query`.
- **TV not found** — set `tv_ip` manually (the Samsung TV integration must be
  set up, or pass the IP).

## Credits

Talks to the TV with [`samsungtvws`](https://github.com/NickWaterton/samsung-tv-ws-api).
Art via the [Art Institute of Chicago API](https://api.artic.edu/docs/) (public
domain / CC0). Not affiliated with the museum.
