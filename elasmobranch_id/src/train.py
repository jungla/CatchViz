"""
Training Pipeline for Elasmobranch Species Identification.

Features:
- Group-Aware UUID Train/Val split (Zero data leakage).
- Class-balanced weighting & label smoothing.
- Two-stage progressive fine-tuning (Head warmup -> full fine-tuning).
- Automatic MPS (Apple Silicon GPU) or CPU device selection.
- Checkpoint and metadata serialization for standalone export.
"""

import os
from pathlib import Path
os.environ["TORCH_HOME"] = str(Path(__file__).parent.parent / ".torch_cache")

import json
import sys
import time
from pathlib import Path
from typing import Dict, Tuple, List, Optional

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import yaml

sys.path.insert(0, str(Path(__file__).parent))
from dataset import (
    parse_dataset_directory,
    get_group_train_val_split,
    balance_training_species,
    get_transforms,
    ElasmobranchDataset
)
from model import ElasmobranchClassifier

def select_device(prefer_mps: bool = True) -> torch.device:
    """Select best available compute device."""
    if prefer_mps and torch.backends.mps.is_available():
        device = torch.device("mps")
        print("Using Apple Silicon GPU (MPS)")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
        print(f"Using NVIDIA GPU: {torch.cuda.get_device_name(0)}")
    else:
        device = torch.device("cpu")
        print("Using CPU")
    return device

def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device
) -> Tuple[float, float]:
    """Train for a single epoch."""
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for batch in dataloader:
        images = batch["image"].to(device)
        labels = batch["label"].to(device)

        optimizer.zero_grad()
        logits, _ = model(images)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        _, preds = torch.max(logits, 1)
        correct += torch.sum(preds == labels).item()
        total += labels.size(0)

    epoch_loss = total_loss / total if total > 0 else 0.0
    epoch_acc = correct / total if total > 0 else 0.0
    return epoch_loss, epoch_acc

def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device
) -> Tuple[float, float, float]:
    """Evaluate model on validation set."""
    model.eval()
    total_loss = 0.0
    correct = 0
    top3_correct = 0
    total = 0

    with torch.no_grad():
        for batch in dataloader:
            images = batch["image"].to(device)
            labels = batch["label"].to(device)

            logits, _ = model(images)
            loss = criterion(logits, labels)

            total_loss += loss.item() * images.size(0)
            probs = torch.softmax(logits, dim=1)
            
            # Top-1 accuracy
            _, preds = torch.max(probs, 1)
            correct += torch.sum(preds == labels).item()

            # Top-3 accuracy
            if logits.size(1) >= 3:
                _, top3_preds = torch.topk(probs, 3, dim=1)
                top3_correct += torch.sum(top3_preds == labels.unsqueeze(1)).item()
            else:
                top3_correct += torch.sum(preds == labels).item()

            total += labels.size(0)

    val_loss = total_loss / total if total > 0 else 0.0
    val_acc = correct / total if total > 0 else 0.0
    val_top3 = top3_correct / total if total > 0 else 0.0
    return val_loss, val_acc, val_top3

def train_pipeline(config_path: str = "configs/default_config.yaml"):
    """Main training routine."""
    with open(config_path, "r") as f:
        cfg = yaml.safe_load(f)

    print("=" * 60)
    print("ELASMOBRANCH SPECIES CLASSIFIER - TRAINING PIPELINE")
    print("=" * 60)

    # 1. Parse dataset
    data_dir = cfg["data"]["raw_dir"]
    print(f"Scanning data from: {data_dir}")
    df = parse_dataset_directory(data_dir)
    num_classes = df["species"].nunique()
    species_list = sorted(df["species"].unique())
    print(f"Found {len(df)} images across {df['uuid'].nunique()} unique specimens and {num_classes} species.")

    # 2. Group-Aware Split
    full_train_df, val_df = get_group_train_val_split(
        df,
        val_ratio=cfg["data"]["val_ratio"],
        seed=cfg["data"]["random_seed"]
    )
    print(f"\nRaw Train pool: {len(full_train_df)} images ({full_train_df['uuid'].nunique()} specimens)")
    print(f"Validation set: {len(val_df)} images ({val_df['uuid'].nunique()} specimens)")

    # 3. Species-Balanced Training Selection
    max_images_per_species = cfg["data"].get("max_images_per_species", 100)
    min_images_per_species = cfg["data"].get("min_images_per_species", 0)
    resample_each_epoch = cfg["data"].get("resample_each_epoch", True)

    train_df = balance_training_species(
        full_train_df,
        max_images_per_species=max_images_per_species,
        min_images_per_species=min_images_per_species,
        seed=cfg["data"]["random_seed"]
    )

    if max_images_per_species and max_images_per_species > 0:
        sp_counts_before = full_train_df["species"].value_counts()
        sp_counts_after = train_df["species"].value_counts()
        saved_imgs = len(full_train_df) - len(train_df)
        pct_saved = (saved_imgs / len(full_train_df) * 100) if len(full_train_df) > 0 else 0
        print(f"\n" + "-" * 60)
        print("SPECIES-BALANCED TRAINING SELECTION")
        print(f"  Target max images/species: {max_images_per_species}")
        print(f"  Before balancing: {len(full_train_df)} images across {len(sp_counts_before)} species (range: {sp_counts_before.min()} - {sp_counts_before.max()} per species)")
        print(f"  After balancing:  {len(train_df)} images across {len(sp_counts_after)} species (range: {sp_counts_after.min()} - {sp_counts_after.max()} per species)")
        print(f"  Training effort saved: {saved_imgs} redundant photos skipped per epoch ({pct_saved:.1f}% reduction in compute!)")
        print(f"  Dynamic per-epoch rotation: {resample_each_epoch}")
        print("-" * 60)
    else:
        print(f"\nTraining set: {len(train_df)} images (unrestricted, all available images)")

    # 4. DataLoaders
    img_size = cfg["data"]["img_size"]
    train_dataset = ElasmobranchDataset(train_df, transform=get_transforms(img_size, is_train=True))
    val_dataset = ElasmobranchDataset(val_df, transform=get_transforms(img_size, is_train=False))

    batch_size = cfg["training"]["batch_size"]
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    # 5. Compute class weights for balanced data
    class_counts = train_df["label"].value_counts().sort_index()
    total_samples = len(train_df)
    weights = []
    for i in range(num_classes):
        cnt = class_counts.get(i, 1)
        weights.append(total_samples / (num_classes * cnt))
    class_weights = torch.tensor(weights, dtype=torch.float)

    # 6. Model Setup
    device = select_device(cfg["training"]["use_mps"])
    class_weights = class_weights.to(device)

    model = ElasmobranchClassifier(
        num_classes=num_classes,
        backbone_name=cfg["model"]["backbone"],
        embedding_dim=cfg["model"]["embedding_dim"],
        dropout=cfg["model"]["dropout"],
        pretrained=cfg["model"]["pretrained"]
    ).to(device)

    criterion = nn.CrossEntropyLoss(
        weight=class_weights,
        label_smoothing=cfg["training"]["label_smoothing"]
    )

    epochs = cfg["training"]["epochs"]
    lr = float(cfg["training"]["lr"])
    weight_decay = float(cfg["training"]["weight_decay"])

    # Stage 1: Warmup - Freeze backbone features for warmup_epochs
    warmup_epochs = cfg["training"].get("warmup_epochs", 1)
    print(f"\nStage 1: Warming up classification head with frozen backbone ({warmup_epochs} epoch(s))...")
    for param in model.features.parameters():
        param.requires_grad = False

    warmup_optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=lr,
        weight_decay=weight_decay
    )

    for epoch in range(1, warmup_epochs + 1):
        if resample_each_epoch and max_images_per_species and max_images_per_species > 0:
            epoch_train_df = balance_training_species(
                full_train_df,
                max_images_per_species=max_images_per_species,
                min_images_per_species=min_images_per_species,
                seed=cfg["data"]["random_seed"] + epoch
            )
            train_dataset.update_data(epoch_train_df)

        loss, acc = train_one_epoch(model, train_loader, criterion, warmup_optimizer, device)
        v_loss, v_acc, v_top3 = evaluate(model, val_loader, criterion, device)
        print(f"Warmup Epoch [{epoch}/{warmup_epochs}] - Train Loss: {loss:.4f}, Acc: {acc*100:.1f}% | Val Loss: {v_loss:.4f}, Acc: {v_acc*100:.1f}%, Top-3: {v_top3*100:.1f}%")

    # Stage 2: Fine-Tuning - Unfreeze all layers with cosine annealing
    print("\nStage 2: Full backbone fine-tuning...")
    for param in model.features.parameters():
        param.requires_grad = True

    # Differential learning rates: lower for pre-trained backbone, higher for head
    optimizer = torch.optim.AdamW([
        {"params": model.features.parameters(), "lr": lr * 0.2},
        {"params": model.embedding_head.parameters(), "lr": lr},
        {"params": model.classifier.parameters(), "lr": lr}
    ], weight_decay=weight_decay)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=epochs - warmup_epochs,
        eta_min=float(cfg["training"]["min_lr"])
    )

    best_val_acc = 0.0
    best_checkpoint_path = Path("models/best_model.pth")
    best_checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(warmup_epochs + 1, epochs + 1):
        if resample_each_epoch and max_images_per_species and max_images_per_species > 0:
            epoch_train_df = balance_training_species(
                full_train_df,
                max_images_per_species=max_images_per_species,
                min_images_per_species=min_images_per_species,
                seed=cfg["data"]["random_seed"] + epoch
            )
            train_dataset.update_data(epoch_train_df)

        loss, acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        v_loss, v_acc, v_top3 = evaluate(model, val_loader, criterion, device)
        scheduler.step()

        print(f"Epoch [{epoch:02d}/{epochs:02d}] - Train Loss: {loss:.4f}, Acc: {acc*100:.1f}% | Val Loss: {v_loss:.4f}, Acc: {v_acc*100:.1f}%, Top-3: {v_top3*100:.1f}%")

        if v_acc >= best_val_acc:
            best_val_acc = v_acc
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_acc": v_acc,
                "val_top3": v_top3,
                "species_list": species_list,
                "config": cfg
            }, best_checkpoint_path)

    print(f"\nTraining Complete! Best Validation Accuracy: {best_val_acc*100:.1f}%")
    print(f"Saved best model checkpoint to: {best_checkpoint_path}")

    # Save class metadata json for standalone deployment
    meta = {
        "species_list": species_list,
        "num_classes": num_classes,
        "input_size": [3, img_size, img_size],
        "normalization": {
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225]
        },
        "best_val_acc": float(best_val_acc),
        "backbone": cfg["model"]["backbone"],
        "embedding_dim": cfg["model"]["embedding_dim"],
        "max_images_per_species": max_images_per_species,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    with open("models/metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    print("Saved metadata to: models/metadata.json")

if __name__ == "__main__":
    train_pipeline()
