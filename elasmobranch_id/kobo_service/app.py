"""
KoboToolbox Automated AI Species Identification Webhook Server.
Deployable to Render.com as a FastAPI web service.

Workflow:
1. KoboToolbox triggers POST /webhook/kobo when a field form is submitted.
2. Server immediately responds with HTTP 200 (preventing Kobo timeout).
3. Background worker extracts photo attachments from the submission.
4. Downloads photos securely via Kobo API Token.
5. Runs multi-angle elasmobranch species classification via ONNX Runtime (~50ms).
6. Writes results back to KoboToolbox:
   - Adds an AI Diagnostic Note to the submission.
   - Sets validation status (Approved for high confidence, Flagged for low/uncertain).
   - Updates form fields (if configured).
"""

import io
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.parse

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse
import numpy as np
import onnxruntime as ort
from PIL import Image
import requests

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("kobo_ai_service")

# Environment configuration
KOBO_API_TOKEN = os.getenv("KOBO_API_TOKEN", "")
KOBO_SERVER_URL = os.getenv("KOBO_SERVER_URL", "https://kf.kobotoolbox.org").rstrip("/")
HIGH_CONF_THRESH = float(os.getenv("CONFIDENCE_THRESHOLD_HIGH", "0.80"))
MOD_CONF_THRESH = float(os.getenv("CONFIDENCE_THRESHOLD_MOD", "0.60"))
MODEL_PATH = os.getenv("MODEL_PATH", "models/elasmobranch_mobilenet.onnx")
META_PATH = os.getenv("META_PATH", "models/metadata.json")

app = FastAPI(
    title="KoboToolbox Elasmobranch Species Identification API",
    description="Automated AI classifier for shark and ray field survey photos submitted via KoboCollect / KoboToolbox.",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# ONNX Classifier Engine (Lightweight CPU)
# -----------------------------------------------------------------------------
class KoboElasmobranchClassifier:
    def __init__(self, model_path: str, meta_path: str):
        self.model_path = Path(model_path)
        self.meta_path = Path(meta_path)
        
        if not self.model_path.exists():
            raise FileNotFoundError(f"ONNX model file not found at: {self.model_path}")
        if not self.meta_path.exists():
            raise FileNotFoundError(f"Metadata file not found at: {self.meta_path}")

        with open(self.meta_path, "r") as f:
            self.meta = json.load(f)

        self.species_list = self.meta["species_list"]
        self.img_size = self.meta["input_size"][1]
        self.mean = np.array(self.meta["normalization"]["mean"], dtype=np.float32)
        self.std = np.array(self.meta["normalization"]["std"], dtype=np.float32)

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        self.session = ort.InferenceSession(str(self.model_path), opts, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        logger.info(f"Loaded ONNX model: {self.model_path.name} ({len(self.species_list)} species classes, {self.img_size}x{self.img_size})")

    def preprocess_image(self, img: Image.Image) -> np.ndarray:
        img_rgb = img.convert("RGB").resize((self.img_size, self.img_size), Image.BILINEAR)
        arr = np.array(img_rgb, dtype=np.float32) / 255.0
        norm = (arr - self.mean) / self.std
        chw = np.transpose(norm, (2, 0, 1))
        return np.expand_dims(chw, axis=0)

    def predict(self, images: List[Image.Image], top_k: int = 3) -> Dict[str, Any]:
        if not images:
            raise ValueError("No images provided for prediction.")

        batch = np.concatenate([self.preprocess_image(im) for im in images], axis=0).astype(np.float32)
        outputs = self.session.run(None, {self.input_name: batch})
        probs_batch = outputs[0]

        # Multi-angle pooling
        mean_probs = np.mean(probs_batch, axis=0) if probs_batch.shape[0] > 1 else probs_batch[0]
        sorted_indices = np.argsort(mean_probs)[::-1]

        top_candidates = []
        for idx in sorted_indices[:top_k]:
            conf = float(mean_probs[idx])
            top_candidates.append({
                "species": self.species_list[idx],
                "confidence": conf,
                "confidence_pct": f"{conf * 100:.1f}%"
            })

        top1 = top_candidates[0]
        top1_conf = top1["confidence"]

        if top1_conf >= HIGH_CONF_THRESH:
            tier = "High Confidence"
            action = "Approve / Auto-Verified"
        elif top1_conf >= MOD_CONF_THRESH:
            tier = "Moderate Confidence"
            action = "Review Recommended"
        else:
            tier = "Uncertain"
            action = "Flagged for Expert Identification"

        return {
            "top_species": top1["species"],
            "top_confidence": top1_conf,
            "confidence_pct": top1["confidence_pct"],
            "confidence_tier": tier,
            "suggested_action": action,
            "top_candidates": top_candidates,
            "num_photos_analyzed": len(images)
        }

# Initialize engine globally
try:
    classifier = KoboElasmobranchClassifier(MODEL_PATH, META_PATH)
except Exception as e:
    logger.error(f"Failed to load ONNX classifier: {e}")
    classifier = None

# -----------------------------------------------------------------------------
# KoboToolbox Helper Functions
# -----------------------------------------------------------------------------
def get_kobo_headers() -> Dict[str, str]:
    if not KOBO_API_TOKEN:
        raise ValueError("KOBO_API_TOKEN environment variable is not configured.")
    return {"Authorization": f"Token {KOBO_API_TOKEN}"}

def extract_image_urls(submission_data: Dict[str, Any]) -> List[str]:
    """Extract all downloadable photo URLs from a KoboToolbox submission payload."""
    urls = []
    
    # 1. Check standard _attachments list
    attachments = submission_data.get("_attachments", [])
    for att in attachments:
        mimetype = att.get("mimetype", "")
        if "image" in mimetype.lower() or any(att.get("filename", "").lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            # Prefer download_large_url for high resolution without original massive file size
            url = att.get("download_large_url") or att.get("download_url") or att.get("download_medium_url")
            if url:
                urls.append(url)

    # 2. If attachments list is empty, scan form field values for image endpoints
    if not urls:
        for k, v in submission_data.items():
            if isinstance(v, str) and (v.startswith("http://") or v.startswith("https://")) and any(v.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                urls.append(v)

    return urls

def download_image(url: str) -> Optional[Image.Image]:
    """Download single image from Kobo using API Token."""
    headers = get_kobo_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            return Image.open(io.BytesIO(resp.content))
        else:
            logger.warning(f"Failed to download image from {url}: HTTP {resp.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading image from {url}: {e}")
        return None

def add_kobo_note(asset_uid: str, submission_id: int, note_text: str):
    """Add a supervisor/diagnostic note to the Kobo submission."""
    url = f"{KOBO_SERVER_URL}/api/v2/assets/{asset_uid}/data/{submission_id}/notes/"
    headers = get_kobo_headers()
    headers["Content-Type"] = "application/json"
    payload = {"content": note_text}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            logger.info(f"Added diagnostic note to Kobo submission {submission_id}")
        else:
            logger.warning(f"Failed to add note to Kobo submission {submission_id}: HTTP {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.error(f"Error posting note to Kobo: {e}")

def set_kobo_validation_status(asset_uid: str, submission_id: int, status_uid: str):
    """Set Kobo validation status (e.g. validation_status_approved, validation_status_flagged_for_review)."""
    url = f"{KOBO_SERVER_URL}/api/v2/assets/{asset_uid}/data/{submission_id}/validation_status/"
    headers = get_kobo_headers()
    headers["Content-Type"] = "application/json"
    payload = {"validation_status.uid": status_uid}
    try:
        resp = requests.patch(url, headers=headers, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            logger.info(f"Updated validation status for Kobo submission {submission_id} -> {status_uid}")
        else:
            logger.warning(f"Failed to set validation status for submission {submission_id}: HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Error updating validation status: {e}")

# -----------------------------------------------------------------------------
# Background Webhook Processing Task
# -----------------------------------------------------------------------------
def process_kobo_submission(payload: Dict[str, Any]):
    """Background pipeline to fetch photos, classify, and update Kobo."""
    if not classifier:
        logger.error("Classifier is not loaded. Skipping submission.")
        return

    submission_id = payload.get("_id")
    submission_uuid = payload.get("_uuid")
    asset_uid = payload.get("_xform_id_string") or payload.get("formhub/uuid") or payload.get("_asset_uid")

    logger.info(f"Processing submission: ID={submission_id}, UUID={submission_uuid}")

    # 1. Extract photo URLs
    photo_urls = extract_image_urls(payload)
    if not photo_urls:
        logger.info(f"No photo attachments found in submission {submission_id}. Nothing to classify.")
        return

    logger.info(f"Found {len(photo_urls)} photo attachment(s) in submission {submission_id}. Downloading...")

    # 2. Download photos
    images = []
    for url in photo_urls:
        img = download_image(url)
        if img:
            images.append(img)

    if not images:
        logger.warning(f"Could not load any valid images for submission {submission_id}.")
        return

    # 3. Run multi-angle ONNX inference
    pred = classifier.predict(images)
    top_sp = pred["top_species"]
    conf_pct = pred["confidence_pct"]
    tier = pred["confidence_tier"]
    num_photos = pred["num_photos_analyzed"]

    logger.info(f"Submission {submission_id} Classified: {top_sp} ({conf_pct}, {tier}, {num_photos} photo(s))")

    # 4. Construct AI Report Note
    candidates_text = "\n".join([f"  • {c['species']}: {c['confidence_pct']}" for c in pred["top_candidates"]])
    note_content = (
        f"🦈 [AI Automated Identification]\n"
        f"Predicted Species: {top_sp}\n"
        f"Confidence: {conf_pct} ({tier})\n"
        f"Photos Analyzed: {num_photos} angle(s)\n\n"
        f"Top Candidates:\n{candidates_text}\n\n"
        f"Recommendation: {pred['suggested_action']}"
    )

    # 5. Send back to KoboToolbox
    if asset_uid and submission_id and KOBO_API_TOKEN:
        # Add supervisor note
        add_kobo_note(asset_uid, submission_id, note_content)

        # Set validation status accordingly
        if tier == "High Confidence":
            set_kobo_validation_status(asset_uid, submission_id, "validation_status_approved")
        elif tier == "Uncertain":
            set_kobo_validation_status(asset_uid, submission_id, "validation_status_flagged_for_review")
    else:
        logger.info("KOBO_API_TOKEN or asset_uid missing; skipping Kobo note writeback.")

# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------
@app.get("/")
def health_check():
    """Health check endpoint for Render."""
    return {
        "status": "online",
        "service": "KoboToolbox Elasmobranch ID Webhook",
        "model_loaded": classifier is not None,
        "classes_count": len(classifier.species_list) if classifier else 0,
        "kobo_token_configured": bool(KOBO_API_TOKEN)
    }

@app.post("/webhook/kobo")
async def kobo_webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    KoboToolbox REST Service Webhook.
    Receives JSON payload, schedules async processing, and returns 200 immediately.
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Failed to parse JSON body from webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    # Enqueue background task so Kobo gets an instant 200 OK
    background_tasks.add_task(process_kobo_submission, payload)

    return JSONResponse(
        status_code=200,
        content={"status": "received", "submission_id": payload.get("_id")}
    )
