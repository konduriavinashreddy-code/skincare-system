import io
import os

import torch
from PIL import Image
from torchvision import transforms

from models.network import OBSERVATIONS, SKIN_TYPES, SkinObservationNet

PREPROCESS = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])

class Predictor:
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path or os.getenv("MODEL_PATH", "models/skin_model.pt")
        self.model = None
        if os.path.isfile(self.model_path):
            checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=True)
            self.model = SkinObservationNet()
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model.eval()

    def predict(self, image_bytes: bytes) -> dict:
        if self.model is None:
            raise RuntimeError("No trained model checkpoint is configured.")
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        with torch.inference_mode():
            observations, skin_type = self.model(PREPROCESS(image).unsqueeze(0))
            scores = observations.sigmoid()[0].tolist()
            type_scores = skin_type.softmax(dim=1)[0]
            confidence, index = type_scores.max(dim=0)
        result_observations = {}
        for key, score in zip(OBSERVATIONS, scores):
            severity = "low" if score < 0.4 else "mild" if score < 0.6 else "moderate"
            result_observations[key] = {"score": round(score, 3), "severity": severity}
        confidence_value = round(float(confidence), 3)
        estimate = SKIN_TYPES[int(index)] if confidence_value >= 0.55 else "unable_to_determine"
        return {"skin_type_estimate": estimate, "confidence": confidence_value, "observations": result_observations}