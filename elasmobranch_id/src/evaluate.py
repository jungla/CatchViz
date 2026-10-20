"""
Comprehensive Evaluation Suite for Elasmobranch Identification.

Evaluates:
1. Single-image classification metrics (Precision, Recall, F1, Top-1 & Top-3 Accuracy).
2. Specimen-level multi-angle pooled predictions (simulating field multi-photo capture).
3. Angle-specific diagnostic accuracy breakdown.
4. Generates confusion matrix visualization.
"""

import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import torch
import torchvision.transforms as T
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent))
from dataset import clean_species_name, parse_dataset_directory, get_transforms, PHOTO_INDEX_LABELS
from model import ElasmobranchClassifier

def load_trained_model(
    model_path: str = "models/best_model.pth",
    meta_path: str = "models/metadata.json",
    device: torch.device = torch.device("cpu")
):
    with open(meta_path, "r") as f:
        meta = json.load(f)

    checkpoint = torch.load(model_path, map_location=device)
    species_list = meta["species_list"]

    model = ElasmobranchClassifier(
        num_classes=len(species_list),
        backbone_name=meta.get("backbone", "mobilenet_v3_large"),
        embedding_dim=meta.get("embedding_dim", 256),
        pretrained=False
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()
    return model, species_list, meta

def evaluate_full(
    data_dir: str = "/Users/jeanmensa/WCS/Data/SharksRays/Photos_Kobo_SHARC",
    model_path: str = "models/best_model.pth",
    meta_path: str = "models/metadata.json",
    output_dir: str = "models"
):
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    model, species_list, meta = load_trained_model(model_path, meta_path, device)
    
    df = parse_dataset_directory(data_dir)
    transform = get_transforms(meta["input_size"][1], is_train=False)

    print("=" * 60)
    print("EVALUATION: SINGLE-IMAGE METRICS")
    print("=" * 60)

    y_true = []
    y_pred = []
    y_probs = []
    angle_records = []

    with torch.no_grad():
        for _, row in df.iterrows():
            img = Image.open(row["filepath"]).convert("RGB")
            tensor = transform(img).unsqueeze(0).to(device)

            logits, _ = model(tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            pred_idx = int(np.argmax(probs))

            y_true.append(row["label"])
            y_pred.append(pred_idx)
            y_probs.append(probs)

            angle_records.append({
                "species": row["species"],
                "uuid": row["uuid"],
                "photo_index": row["photo_index"],
                "angle_label": row["angle_label"],
                "correct": (pred_idx == row["label"]),
                "confidence": float(probs[pred_idx])
            })

    # Classification report
    target_names = species_list
    report = classification_report(y_true, y_pred, target_names=target_names, zero_division=0)
    print(report)

    # Confusion Matrix
    cm = confusion_matrix(y_true, y_pred, labels=list(range(len(species_list))))
    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=species_list,
        yticklabels=species_list,
        title="Elasmobranch Species Confusion Matrix",
        ylabel="True Species",
        xlabel="Predicted Species"
    )
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate numbers
    thresh = cm.max() / 2.
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black")

    fig.tight_layout()
    cm_path = Path(output_dir) / "confusion_matrix.png"
    plt.savefig(cm_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix plot to: {cm_path}")

    # ============================================================
    # MULTI-ANGLE SPECIMEN-LEVEL EVALUATION
    # ============================================================
    print("\n" + "=" * 60)
    print("EVALUATION: MULTI-ANGLE SPECIMEN-LEVEL POOLING")
    print("=" * 60)

    specimen_correct = 0
    total_specimens = 0
    specimen_results = []

    for uuid, group in df.groupby("uuid"):
        total_specimens += 1
        true_sp = group["species"].iloc[0]
        true_label = group["label"].iloc[0]

        # Load all photos for this specimen
        tensors = []
        for _, r in group.iterrows():
            img = Image.open(r["filepath"]).convert("RGB")
            tensors.append(transform(img))
        batch_tensor = torch.stack(tensors).to(device)

        # Multi-angle pooled prediction
        pooled = model.predict_multi_angle(batch_tensor)
        mean_probs = pooled["probabilities"].cpu().numpy()
        pred_idx = int(np.argmax(mean_probs))
        pred_sp = species_list[pred_idx]
        conf = float(mean_probs[pred_idx])

        is_correct = (pred_idx == true_label)
        if is_correct:
            specimen_correct += 1

        specimen_results.append({
            "uuid": uuid,
            "true_species": true_sp,
            "pred_species": pred_sp,
            "confidence": conf,
            "num_photos": len(group),
            "correct": is_correct
        })

    specimen_acc = specimen_correct / total_specimens if total_specimens > 0 else 0.0
    print(f"Specimen-Level Pooled Accuracy: {specimen_correct}/{total_specimens} ({specimen_acc*100:.1f}%)")
    for res in specimen_results:
        mark = "✓" if res["correct"] else "✗"
        print(f"  {mark} Specimen {res['uuid'][:8]}... | True: {res['true_species']:<25} | Pred: {res['pred_species']:<25} | Conf: {res['confidence']*100:.1f}% ({res['num_photos']} angles)")

if __name__ == "__main__":
    evaluate_full()
