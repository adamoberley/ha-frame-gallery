"""Art Institute of Chicago source (api.artic.edu).

No API key. Public-domain works are CC0 with high-res IIIF images, and each
carries department / classification / subject tags we use for the family-safe
keyword filter. A free-text `query` shapes the collection (e.g. "landscape",
"ukiyo-e", "impressionism"); blank pulls from the whole public-domain catalogue.
A random page each cycle gives variety; the picker's history prevents repeats.
"""
from __future__ import annotations

import logging
import random
import time

import requests

from sources.base import ArtSource, Artwork

log = logging.getLogger("frame-gallery.artic")

BASE = "https://api.artic.edu/api/v1/artworks"
DEFAULT_IIIF = "https://www.artic.edu/iiif/2"
IMG_WIDTH = 1920          # IIIF width; matted/scaled to the panel by imaging.py
MAX_PAGE = 100            # offset cap (page*limit <= ~10000 per the AIC API)
FIELDS = ("id,title,artist_title,image_id,is_public_domain,"
          "department_title,classification_titles,term_titles")
HEADERS = {
    "User-Agent": "ha-frame-gallery/0.1 (+https://github.com/adamoberley/ha-frame-gallery)",
    "AIC-User-Agent": "ha-frame-gallery (adamoberley@damascus.net)",
}


class ArticSource(ArtSource):
    name = "artic"

    def __init__(self) -> None:
        # Remember each query's page count so we can jump to a random page in
        # ONE request (no probe), and never repeatedly hammer the API.
        self._total_pages: dict[str, int] = {}

    def _get(self, url, params):
        """GET with a short backoff on 403/429 (AIC's Cloudflare rate-limits
        bursts). Returns parsed JSON, or None on persistent failure."""
        for attempt in range(3):
            try:
                r = requests.get(url, params=params, headers=HEADERS, timeout=20)
                if r.status_code in (403, 429) and attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                r.raise_for_status()
                return r.json()
            except (requests.RequestException, ValueError) as exc:
                if attempt < 2:
                    time.sleep(2)
                    continue
                log.warning("Art Institute request failed: %s", exc)
        return None

    def candidates(self, opts, count: int = 100) -> list[Artwork]:
        url = (BASE + "/search") if opts.query else BASE
        params = {"fields": FIELDS, "limit": count}
        if opts.query:
            params["q"] = opts.query

        key = opts.query or "*"
        # First time for this query we don't know the page count, so take
        # page 1 (and learn it); afterwards jump straight to a random page.
        known = self._total_pages.get(key)
        page = random.randint(1, max(1, min(known, MAX_PAGE))) if known else 1
        j = self._get(url, {**params, "page": page})
        if j is None:
            return []
        total = int((j.get("pagination") or {}).get("total_pages", 1) or 1)
        self._total_pages[key] = total

        iiif = ((j.get("config") or {}).get("iiif_url") or DEFAULT_IIIF).rstrip("/")
        out = []
        for it in (j.get("data") or []):
            image_id = it.get("image_id")
            if not image_id:
                continue
            tags = " ".join(filter(None, [
                it.get("title") or "",
                it.get("artist_title") or "",
                it.get("department_title") or "",
                " ".join(it.get("classification_titles") or []),
                " ".join(it.get("term_titles") or []),
            ])).lower()
            out.append(Artwork(
                source=self.name,
                id=str(it.get("id")),
                title=it.get("title") or "Untitled",
                artist=it.get("artist_title") or "Unknown",
                image_url=f"{iiif}/{image_id}/full/{IMG_WIDTH},/0/default.jpg",
                public_domain=bool(it.get("is_public_domain")),
                tags=tags,
                credit="Art Institute of Chicago",
            ))
        return out
