# Frame Gallery

Curated **public-domain art on your Samsung Frame TV**, changed on its own
interval — no Google/Bing, no automation, no pile-up, no repeats, and content
you control.

## Why this instead of the older art-changers

| Old art-changer | Frame Gallery |
| --- | --- |
| **Unpredictable, sometimes mature** images from Google Art | Public-domain museum art + a keyword content filter + a search to shape the collection |
| The **same pieces** over and over | Remembers the last *N* shown; never repeats until the pool is exhausted |
| Uploads **pile up** in the art library | Upload → select → **delete the previous one**; one image, swapped in place |
| Needed an **automation** to run | A long-running service with its own interval |

## How it works

Each interval — or when you press **Show next** on the panel — it:

1. asks an open museum API for a batch of works;
2. filters them (public-domain, keyword blocklist, not shown recently);
3. downloads one and fits it to your panel (matted like a framed print, or
   cropped to fill);
4. pushes it to the Frame, **deleting** the piece it replaces.

The push is Art-Mode-aware: if you're watching TV it just sets the next art
without interrupting; switch to Art Mode to see it. Source for v0.1: the **Art
Institute of Chicago** (no key, CC0 IIIF images). More can be added — the source
layer is a plug-in.

## Setup

1. **Install** this app (you added the repo under *Settings → Apps → ⋮ →
   Repositories*).
2. Usually **nothing to configure** — it auto-discovers your Frame from the
   Samsung TV integration. Optionally set **Art search** (e.g. `landscape`).
3. **Start** it with the TV **on** and the remote handy, and accept on the TV:
   - the one-time *"Allow this device to connect?"* pairing prompt, and
   - the **Art Store / terms** prompt the first time (the TV blocks uploads
     until these are accepted — the usual cause of a first upload failing).
4. Put the TV in **Art Mode**. A new piece appears each interval.

## Options

| Option | Default | What it does |
| --- | --- | --- |
| **Art source** (`source`) | `reframed` | `reframed` = reframed.gallery's curated, Frame-ready public-domain set (recommended); `artic` = the Art Institute of Chicago's full CC0 catalogue. |
| **Collection** (`collection`) | `seasonal` | reframed only. `seasonal` auto-tracks the date; `weather` tracks the weather entity below; `all` = whole catalogue; or a slug like `by-the-sea`, `golden-hour`, `nocturnes-moonlight`. |
| **Hemisphere** | `north` | Flips the `seasonal` calendar for the Southern hemisphere. |
| **Weather entity** (`weather_entity`) | *(blank)* | For the `weather` collection — an HA `weather.*` entity (e.g. `weather.home`). Its condition picks a matching collection; unknown conditions fall back to the season. |
| **Art search** (`query`) | *(blank)* | Free-text search that shapes the collection: `landscape`, `impressionism`, `ukiyo-e`, `Monet`… Blank = the whole collection. |
| **Public domain only** | on | Only show CC0 works (recommended — clean licensing). |
| **Excluded keywords** | *(mature-content terms)* | Comma-separated; any work whose title/artist/tags match a listed term is skipped. Blank to disable. |
| **Change interval** | 1440 | Minutes between pieces (used when Daily switch time is blank). |
| **Daily switch time** | `04:00` | Switch once a day at this local `HH:MM`. Blank = use the interval. |
| **Fit** | `crop` | `crop` fills the panel and trims the edges; `matte` frames the whole work on a mat (nothing cropped). |
| **Mat color** | `#141414` | Background behind matted art (hex). Dark avoids glare at night. |
| **TV matte** (`tv_matte`) | `none` | `none` keeps the in-image fit; or a Samsung matte id (e.g. `modern_apricot`, `shadowbox_polar`) to have the **TV render a real mat** (art sent full-bleed). Unsupported ids fall back to none. |
| **No-repeat memory** | 2000 | Don't repeat the last *N* pieces (0 = allow repeats). |
| **Active hours** | *(blank)* | Blank = 24/7, or a local-time window like `07:00-23:00`. |
| **Panel resolution** | 3840x2160 | Match your panel (1920x1080 for 32"/pre-2021). |
| **Frame TV IP(s)** | *(blank)* | Blank = auto-discover; or comma-separated IPs to override. |
| **Frame TV MAC(s)** (`tv_mac`) | *(blank)* | Optional. MAC(s) for a **Wake-on-LAN** nudge before a push retry, so a sleeping TV still updates. Comma-separated, paired with the IPs by position. |

The sidebar **REFRAMED Gallery** panel shows the current piece with its full
details (title · artist · year · medium · movement, with Wikipedia links), a
status pill with how many TVs were reached and when art last changed, and two
buttons: **Show next** (pick a new piece) and **Re-push to TV** (re-send the
current one, handy if a TV was off or got switched away).

## Home Assistant entities (MQTT)

With the Mosquitto broker app installed (auto-detected), REFRAMED Gallery
exposes these over MQTT discovery:

- **Current Art** sensor — the title, with `artist`, `year`, `medium`,
  `movement`, `description`, `collection`, `matte`, `credit`, and `source`
  attributes (great for a dashboard card or TTS).
- **Next** button — change to a fresh piece now.
- **Collection** select — switch collection (incl. `seasonal` / `weather`) live.
- **Matte** select — switch the TV-rendered matte live.

## TV-rendered mattes

Set **TV matte** (or the HA Matte select) to a Samsung matte id and the Frame
draws a real museum mat around the art instead of the flat in-image border — the
image is sent full-bleed so it isn't double-framed. Matte ids look like
`<style>_<color>` (e.g. `shadowbox_polar`, `modern_apricot`). Which ones a TV
supports varies by model/year; if the Frame rejects an id, the push automatically
falls back to no matte rather than failing.

## Weather-aware art

Set **Collection** to `weather` and pick a **Weather entity**, and each change
maps the current condition to a fitting reframed collection — rain → nocturnes,
snow → winter, sun → summer, fog → mountains, and so on — falling back to the
season for conditions it doesn't recognise. No LLM, no weather API, no key; it
just reads the condition Home Assistant already has.

## Content safety

Three layers, all under your control:

- **Public-domain only** keeps the pool to CC0 works.
- **Art search** lets you pick benign themes (landscapes, still lifes, a specific
  movement or artist) so the whole collection fits your room.
- **Excluded keywords** vetoes anything whose museum metadata (title, artist,
  department, classification, subject) matches a word you list.

This is metadata-based, not a content rating, so it isn't infallible on its own —
but combining a focused `query` with the keyword filter makes mature imagery
extremely unlikely. Tighten `query` if you want a guaranteed-tame collection.

## Troubleshooting

- **First upload fails / `ms.channel.timeOut` / `send_image error -2`** — accept
  the **Allow** and **Art Store terms** prompts on the TV (it blocks uploads
  until you do), then restart.
- **Image is set but the TV doesn't switch to it** — it uses Art-Mode-aware
  pushing; switch the TV to Art Mode to see it.
- **"no artwork found"** — your `query` is too narrow or everything matched a
  blocked keyword; broaden or clear `query`.
- **TV not found** — set **Frame TV IP(s)** manually (the Samsung TV integration
  must be configured, or pass the IP).
- **Rate-limited source** — transient; it backs off and retries next cycle. Set
  **Log level** to `debug` to see source and TV steps.

## Credits

Talks to the TV with [`samsungtvws`](https://github.com/NickWaterton/samsung-tv-ws-api).
Art via the [Art Institute of Chicago API](https://api.artic.edu/docs/)
(public domain / CC0). Not affiliated with the museum.
