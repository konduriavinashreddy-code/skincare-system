import base64
import binascii
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from inference.predict import Predictor

app = FastAPI(title="DermaCare ML Inference", version="1.0.0")
predictor = Predictor(os.getenv("MODEL_PATH", "models/skin_model.pt"))

class InferenceRequest(BaseModel):
    image_base64: str

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": predictor.model is not None}

@app.post("/infer")
def infer(payload: InferenceRequest):
    try:
        image = base64.b64decode(payload.image_base64, validate=True)
        result = predictor.predict(image)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(422, "A valid encoded image is required.") from exc
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    except OSError as exc:
        raise HTTPException(422, "The image could not be read.") from exc
    return result