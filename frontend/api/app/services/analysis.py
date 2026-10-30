import base64
import hashlib
import json
import os
import urllib.error
import urllib.request

OBSERVATION_LABELS = {
    "acne_like_features": "Acne-like features", "redness": "Visible redness",
    "dark_spots": "Dark-spot-like pigmentation", "oiliness": "Visible oiliness",
    "dryness": "Visible dryness", "uneven_tone": "Uneven-looking skin tone",
    "texture": "Texture irregularities", "fine_lines": "Fine-line appearance",
}

def analyze_image(image_bytes: bytes) -> dict:
    mode = os.getenv("AI_MODE", "mock").lower()
    if mode == "model":
        endpoint = os.getenv("ML_SERVICE_URL", "http://localhost:8001") + "/infer"
        request = urllib.request.Request(endpoint, data=json.dumps({"image_base64": base64.b64encode(image_bytes).decode("ascii")}).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError("Model inference service is unavailable or has no trained checkpoint.") from exc
        if not isinstance(result.get("observations"), dict) or "confidence" not in result:
            raise RuntimeError("Model inference service returned an invalid response.")
        return {**result, "model_mode": "model", "disclaimer": "Model output is a cautious image-based observation, not a diagnosis."}
    if mode != "mock":
        raise RuntimeError("AI_MODE must be either 'mock' or 'model'.")
    # Stable demo-only variation; this is not a trained model or a real skin assessment.
    digest = hashlib.sha256(image_bytes).digest()
    observations = {}
    for index, key in enumerate(OBSERVATION_LABELS):
        score = round(0.2 + (digest[index] / 255) * 0.62, 2)
        observations[key] = {"score": score, "severity": "low" if score < 0.4 else "mild" if score < 0.6 else "moderate"}
    return {"skin_type_estimate": "unable_to_determine", "confidence": 0.38, "observations": observations,
            "model_mode": "mock", "disclaimer": "Simulated demo output only. No AI model has assessed this image."}