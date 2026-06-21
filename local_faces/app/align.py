"""5-point face alignment to a canonical 112x112 crop (ArcFace convention).

OpenCV's SFace recognizer aligns internally (alignCrop); other ONNX embedders
expect this standard alignment, so we reproduce it: a similarity transform that
maps the detected eyes/nose/mouth landmarks onto the fixed reference positions.
"""
from __future__ import annotations

import cv2
import numpy as np

# Canonical landmark positions for a 112x112 aligned face (InsightFace/ArcFace):
# right eye, left eye, nose, right mouth corner, left mouth corner.
_REFERENCE_112 = np.array([
    [38.2946, 51.6963],
    [73.5318, 51.5014],
    [56.0252, 71.7366],
    [41.5493, 92.3655],
    [70.7299, 92.2041],
], dtype=np.float32)


def align_112(image: np.ndarray, landmarks5: np.ndarray) -> np.ndarray:
    """Warp `image` so the 5 landmarks land on the canonical 112x112 positions."""
    src = np.asarray(landmarks5, dtype=np.float32).reshape(5, 2)
    matrix, _ = cv2.estimateAffinePartial2D(src, _REFERENCE_112, method=cv2.LMEDS)
    if matrix is None:  # degenerate landmarks - fall back to a plain resize
        return cv2.resize(image, (112, 112))
    return cv2.warpAffine(image, matrix, (112, 112), borderValue=0)
