"""Art source plug-in interface.

Add a museum/photo source by subclassing ArtSource and implementing
candidates(): return a batch of Artwork the picker can filter and choose from.
Keeping this tiny is what lets Met / Rijksmuseum / Smithsonian / Wikimedia /
Unsplash slot in later without touching the rest of the app.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Artwork:
    source: str
    id: str
    title: str
    artist: str
    image_url: str
    public_domain: bool = True
    tags: str = ""          # lowercased searchable text, for keyword filtering
    credit: str = ""
    # Optional descriptive metadata, surfaced in the panel + HA (not all sources
    # provide these; they default empty and the UI hides what's blank).
    year: str = ""          # e.g. "1889" or "c. 1500-1510"
    medium: str = ""        # e.g. "Oil on canvas"
    movement: str = ""      # style/movement, e.g. "Post-Impressionism"
    description: str = ""   # short blurb, if the source has one

    @property
    def key(self) -> str:
        return f"{self.source}:{self.id}"


class ArtSource:
    name = "base"

    def candidates(self, opts, count: int = 100) -> list[Artwork]:
        """Return up to `count` candidate works (unfiltered; the picker applies
        public-domain / keyword / recency filters)."""
        raise NotImplementedError
