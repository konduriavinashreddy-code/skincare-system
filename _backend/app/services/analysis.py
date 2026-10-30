import base64
import json
import os
import urllib.error
import urllib.request

import cv2
import numpy as np
from PIL import Image

OBSERVATION_LABELS = {
    "acne_like_features": "Acne-like features", "redness": "Visible redness",
    "dark_spots": "Dark-spot-like pigmentation", "oiliness": "Visible oiliness",
    "dryness": "Visible dryness", "uneven_tone": "Uneven-looking skin tone",
    "texture": "Texture irregularities", "fine_lines": "Fine-line appearance",
}


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def _to_dict_score(value: float) -> dict:
    score = _clamp(float(value))
    if score < 0.35:
        severity = "low"
    elif score < 0.6:
        severity = "mild"
    elif score < 0.8:
        severity = "moderate"
    else:
        severity = "high"
    return {"score": round(score, 2), "severity": severity}


def _estimate_skin_type(oiliness: float, dryness: float, redness: float) -> str:
    if oiliness > 0.62 and dryness < 0.48:
        return "oily"
    if dryness > 0.62 and oiliness < 0.48:
        return "dry"
    if oiliness > 0.52 and dryness > 0.48:
        return "combination"
    if redness > 0.7:
        return "sensitive"
    return "normal"


def analyze_image(image_bytes: bytes) -> dict:
    mode = os.getenv("AI_MODE", "mock").lower()
    if mode == "model":
        endpoint = os.getenv("ML_SERVICE_URL", "http://localhost:8001") + "/infer"
        request = urllib.request.Request(
            endpoint,
            data=json.dumps({"image_base64": base64.b64encode(image_bytes).decode("ascii")}).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Model inference service is unavailable or has no trained checkpoint.") from exc
        if not isinstance(result.get("observations"), dict) or "confidence" not in result:
            raise RuntimeError("Model inference service returned an invalid response.")
        return {**result, "model_mode": "model", "disclaimer": "Model output is a cautious image-based observation, not a diagnosis."}

    if mode not in {"mock", "real-time", "realtime"}:
        raise RuntimeError("AI_MODE must be either 'mock', 'real-time', or 'model'.")

    image = Image.open(__import__('io').BytesIO(image_bytes)).convert("RGB")
    arr = np.asarray(image)
    if arr.size == 0:
        raise ValueError("Image is empty.")
    if arr.ndim != 3:
        raise ValueError("Unable to read image data.")

    rgb = arr.astype(np.float32)
    r = rgb[:, :, 0]
    g = rgb[:, :, 1]
    b = rgb[:, :, 2]

    brightness = np.mean((r + g + b) / 3.0) / 255.0
    redness = np.mean(np.clip((r - (g + b) / 2.0) / 255.0, 0.0, 1.0))
    saturation = np.mean(np.maximum(0.0, np.sqrt(((r - g) ** 2 + (r - b) ** 2) / 2.0)) / 255.0)
    contrast = np.std(rgb) / 255.0

    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    texture = np.mean(edges > 0) / 255.0

    dark_mask = ((r + g + b) / 3.0) < 90
    dark_spots = float(np.mean(dark_mask))
    oiliness = _clamp((saturation * 0.7 + brightness * 0.3) * 1.15)
    dryness = _clamp((1.0 - brightness) * 0.8 + (1.0 - saturation) * 0.2)
    uneven_tone = _clamp((contrast * 0.55) + (abs(np.mean(r) - np.mean(g)) / 255.0) * 0.45)
    acne_like_features = _clamp((texture * 0.7) + (redness * 0.5) + (dark_spots * 0.2))
    fine_lines = _clamp((texture * 0.6) + (1.0 - brightness) * 0.4)

    observations = {
        "acne_like_features": _to_dict_score(acne_like_features),
        "redness": _to_dict_score(redness * 2.0),
        "dark_spots": _to_dict_score(dark_spots * 1.4),
        "oiliness": _to_dict_score(oiliness),
        "dryness": _to_dict_score(dryness),
        "uneven_tone": _to_dict_score(uneven_tone),
        "texture": _to_dict_score(texture * 1.8),
        "fine_lines": _to_dict_score(fine_lines),
    }

    skin_type = _estimate_skin_type(oiliness, dryness, redness)
    confidence = _clamp(0.72 + (1.0 - abs(oiliness - dryness)) * 0.18 + (contrast * 0.12))

    return {
        "skin_type_estimate": skin_type,
        "confidence": round(confidence, 2),
        "observations": observations,
        "model_mode": "real-time",
        "disclaimer": "Live image analysis based on the uploaded photo. It is not a diagnosis and should be reviewed with caution.",
    }