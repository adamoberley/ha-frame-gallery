"""Pluggable face embedders: turn an aligned face into an L2-normalized vector.

Two backends share one interface so the rest of the app doesn't care which is in
use - they only see a normalized embedding (cosine similarity = dot product) plus
a thumbnail of the aligned crop:

- SFaceEmbedder: OpenCV's bundled SFace (FaceRecognizerSF) - does its own
  alignment and embedding, no extra runtime. 128-D. The Apache-2.0 default.
- OnnxArcFaceEmbedder: any ArcFace-style ONNX model (e.g. w600k MobileFaceNet)
  via onnxruntime, with our own 5-point alignment. Typically 512-D.

Embeddings from different models aren't comparable, so FaceDB namespaces enrolled
people by model id.
"""
from __future__ import annotations

import logging

import cv2
import numpy as np
from align import align_112

log = logging.getLogger("local-faces.embedders")


def encode_thumb(aligned: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", aligned, [cv2.IMWRITE_JPEG_QUALITY, 85])
    return buf.tobytes() if ok else b""


def _normalize(vec: np.ndarray) -> np.ndarray:
    vec = vec.flatten().astype("float32")
    norm = float(np.linalg.norm(vec))
    return vec / norm if norm > 0 else vec


class SFaceEmbedder:
    model_id = "sface"
    dim = 128

    def __init__(self, model_path: str) -> None:
        self._rec = cv2.FaceRecognizerSF.create(model_path, "")

    def embed(self, frame: np.ndarray, row: np.ndarray) -> tuple[np.ndarray, bytes]:
        aligned = self._rec.alignCrop(frame, row)
        feat = self._rec.feature(aligned)
        return _normalize(feat), encode_thumb(aligned)


class OnnxArcFaceEmbedder:
    def __init__(self, model_id: str, model_path: str) -> None:
        import onnxruntime as ort

        self.model_id = model_id
        self._sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        self._input = self._sess.get_inputs()[0].name
        out_shape = self._sess.get_outputs()[0].shape
        self.dim = int(out_shape[-1]) if isinstance(out_shape[-1], int) else 512

    def embed(self, frame: np.ndarray, row: np.ndarray) -> tuple[np.ndarray, bytes]:
        aligned = align_112(frame, row[4:14])
        # ArcFace preprocessing: RGB, (x - 127.5) / 127.5, NCHW.
        blob = cv2.dnn.blobFromImage(aligned, 1.0 / 127.5, (112, 112),
                                     (127.5, 127.5, 127.5), swapRB=True)
        feat = self._sess.run(None, {self._input: blob})[0]
        return _normalize(feat), encode_thumb(aligned)


def build_embedder(model_id: str, model_path: str):
    if model_id == "sface":
        emb = SFaceEmbedder(model_path)
    else:
        emb = OnnxArcFaceEmbedder(model_id, model_path)
    log.info("recognition model: %s (%d-D embeddings)", emb.model_id, emb.dim)
    return emb
