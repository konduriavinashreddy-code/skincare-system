from io import BytesIO
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

def inspect_image(contents: bytes) -> tuple[dict, Image.Image]:
    try:
        image = Image.open(BytesIO(contents)).convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("The file is not a readable image.") from exc
    width, height = image.size
    warnings: list[str] = []
    score = 1.0
    if min(width, height) < 256:
        warnings.append("Image resolution is too small for a useful observation.")
        score -= 0.4
    array = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(array, cv2.COLOR_BGR2GRAY)
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur < 35:
        warnings.append("The image may be blurry; try holding the camera steady.")
        score -= 0.25
    brightness = float(np.mean(gray))
    if brightness < 45:
        warnings.append("The image looks very dark; try brighter, even lighting.")
        score -= 0.25
    elif brightness > 220:
        warnings.append("The image looks very bright; avoid direct or strong backlighting.")
        score -= 0.2
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        warnings.append("A face was not clearly detected. Center a face in the frame without filters.")
        score -= 0.35
    score = max(0.0, min(1.0, score))
    return {"valid": score >= 0.5 and len(faces) > 0, "quality_score": round(score, 2), "warnings": warnings, "width": width, "height": height}, image

def preprocess(image: Image.Image, size: int = 224) -> np.ndarray:
    image = image.convert("RGB")
    image.thumbnail((size, size), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (size, size), (127, 127, 127))
    canvas.paste(image, ((size - image.width) // 2, (size - image.height) // 2))
    values = np.asarray(canvas, dtype=np.float32) / 255.0
    return (values - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])