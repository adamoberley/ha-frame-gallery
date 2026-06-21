"""Enrolled people: name -> one or more face embeddings, persisted in /data.

Embeddings from different recognition models aren't comparable (different spaces,
even different dimensions), so enrollments are namespaced by model id: switching
models shows that model's own people, and switching back keeps the originals -
no re-enroll needed once you've done each model once.

Matching is the max cosine similarity over a person's samples (vectors are
L2-normalized, so the dot product is the cosine); the best person wins if it
clears the threshold, else the face is "unknown". Everything stays on disk in
/data/faces.json - it never leaves the box.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import threading

import numpy as np

log = logging.getLogger("local-faces.facedb")

DB_PATH = "/data/faces.json"


class FaceDB:
    def __init__(self, threshold: float, model_id: str) -> None:
        self.threshold = threshold
        self.model_id = model_id
        self._lock = threading.Lock()
        self._all: dict = {"version": 2, "models": {}}
        self._emb: dict[str, np.ndarray] = {}   # name -> (k, dim) normalized
        self._thumb: dict[str, str] = {}         # name -> base64 jpeg
        self._load()

    def _load(self) -> None:
        if os.path.exists(DB_PATH):
            try:
                with open(DB_PATH, encoding="utf-8") as fh:
                    data = json.load(fh)
            except (OSError, ValueError) as exc:
                log.warning("could not read %s: %s", DB_PATH, exc)
                data = {}
            if "models" in data:
                self._all = data
                self._all.setdefault("models", {})
            elif "people" in data:  # migrate v1 (SFace-only) layout
                self._all = {"version": 2, "models": {"sface": {"people": data["people"]}}}
                log.info("migrated existing enrollments to the 'sface' namespace")

        people = (self._all["models"].get(self.model_id) or {}).get("people", {})
        for name, person in people.items():
            vecs = np.array(person.get("embeddings", []), dtype="float32")
            if vecs.size:
                self._emb[name] = vecs.reshape(-1, vecs.shape[-1])
                self._thumb[name] = person.get("thumb", "")
        log.info("loaded %d enrolled %s for model '%s'", len(self._emb),
                 "person" if len(self._emb) == 1 else "people", self.model_id)

    def _save(self) -> None:
        self._all.setdefault("models", {})[self.model_id] = {
            "people": {
                name: {"embeddings": self._emb[name].tolist(), "thumb": self._thumb.get(name, "")}
                for name in self._emb
            }
        }
        tmp = DB_PATH + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(self._all, fh)
            os.replace(tmp, DB_PATH)
        except OSError as exc:
            log.warning("could not persist faces: %s", exc)

    def add(self, name: str, embedding: np.ndarray, thumb: bytes) -> int:
        vec = embedding.reshape(1, -1).astype("float32")
        with self._lock:
            if name in self._emb:
                self._emb[name] = np.vstack([self._emb[name], vec])
            else:
                self._emb[name] = vec
            if thumb:
                self._thumb[name] = base64.b64encode(thumb).decode("ascii")
            samples = int(self._emb[name].shape[0])
            self._save()
        return samples

    def delete(self, name: str) -> bool:
        with self._lock:
            existed = self._emb.pop(name, None) is not None
            self._thumb.pop(name, None)
            if existed:
                self._save()
        return existed

    def people(self) -> list[dict]:
        with self._lock:
            return [
                {"name": name, "samples": int(self._emb[name].shape[0]),
                 "thumb": self._thumb.get(name, "")}
                for name in sorted(self._emb)
            ]

    def match(self, embedding: np.ndarray) -> tuple[str | None, float]:
        """Return (name, score) for the best enrolled match, or (None, best_score)."""
        best_name, best = None, -1.0
        with self._lock:
            for name, vecs in self._emb.items():
                if vecs.shape[-1] != embedding.shape[-1]:
                    continue  # guard against any stale, wrong-dimension samples
                score = float((vecs @ embedding).max())
                if score > best:
                    best, best_name = score, name
        return (best_name, best) if best >= self.threshold else (None, best)
