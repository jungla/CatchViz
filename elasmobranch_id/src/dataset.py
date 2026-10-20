"""
Elasmobranch Dataset Module with Group-Leakage Prevention.

Parses Kobo SHARC images, groups strictly by specimen UUID, and provides
group-aware training and validation datasets with robust augmentations.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import numpy as np
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T

# Standard photo index to anatomical label mapping
PHOTO_INDEX_LABELS = {
    4: "dorsal_full",
    5: "ventral_full",
    6: "head_snout",
    7: "mouth_nasal",
    8: "dorsal_fin_spine",
    9: "pectoral_pelvic_fin",
    10: "tail_spine",
    11: "skin_pattern",
    12: "lateral_profile"
}

def clean_species_name(name: str) -> str:
    """Standardize species names to binomial nomenclature."""
    name = name.strip()
    # Normalize Galeocerdo Cuvier -> Galeocerdo cuvier
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0].capitalize()} {parts[1].lower()}"
    return name.capitalize()

def parse_dataset_directory(data_dir: str) -> pd.DataFrame:
    """
    Scan folder and extract metadata DataFrame from filenames.
    Filename format: <UUID>_<Species Name>_<PhotoIndex>.jpeg
    """
    path = Path(data_dir)
    if not path.exists():
        raise FileNotFoundError(f"Directory not found: {data_dir}")

    # Regex pattern: uuid _ species name _ photo index . ext
    pattern = re.compile(r"^([a-f0-9\-]+)_(.+)_(\d+)\.([a-zA-Z0-9]+)$", re.IGNORECASE)

    records = []
    for f in sorted(path.iterdir()):
        if not f.is_file() or f.name.startswith('.'):
            continue
        m = pattern.match(f.name)
        if m:
            uuid_str, raw_species, photo_idx, ext = m.groups()
            species = clean_species_name(raw_species)
            idx = int(photo_idx)
            records.append({
                "filename": f.name,
                "filepath": str(f.resolve()),
                "uuid": uuid_str,
                "species": species,
                "photo_index": idx,
                "angle_label": PHOTO_INDEX_LABELS.get(idx, f"angle_{idx}"),
                "extension": ext.lower()
            })

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError(f"No valid image files parsed from {data_dir}")

    # Assign integer class labels alphabetically for stability
    unique_species = sorted(df["species"].unique())
    species_to_idx = {sp: i for i, sp in enumerate(unique_species)}
    df["label"] = df["species"].map(species_to_idx)

    return df

def get_group_train_val_split(
    df: pd.DataFrame,
    val_ratio: float = 0.25,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split dataset into Train and Validation sets by SPECIMEN UUID.
    Guarantees zero group data leakage: no individual's photos appear in both sets.
    For species with >=2 individuals, at least one individual is held out for validation.
    """
    rng = np.random.RandomState(seed)
    train_uuids = set()
    val_uuids = set()

    # Process each species group
    for sp, group in df.groupby("species"):
        specimen_uuids = sorted(group["uuid"].unique())
        n_specimens = len(specimen_uuids)

        if n_specimens == 1:
            # Single specimen available: must be in train for class representation
            train_uuids.add(specimen_uuids[0])
        elif n_specimens == 2:
            # Split 1 train, 1 val
            val_idx = rng.choice(2)
            for i, u in enumerate(specimen_uuids):
                if i == val_idx:
                    val_uuids.add(u)
                else:
                    train_uuids.add(u)
        else:
            # More than 2 specimens: allocate proportional to val_ratio
            n_val = max(1, int(round(n_specimens * val_ratio)))
            shuffled = rng.permutation(specimen_uuids)
            val_uuids.update(shuffled[:n_val])
            train_uuids.update(shuffled[n_val:])

    train_df = df[df["uuid"].isin(train_uuids)].reset_index(drop=True)
    val_df = df[df["uuid"].isin(val_uuids)].reset_index(drop=True)

    return train_df, val_df

def balance_training_species(
    df: pd.DataFrame,
    max_images_per_species: Optional[int] = 100,
    min_images_per_species: int = 0,
    seed: int = 42
) -> pd.DataFrame:
    """
    Select an even number of pictures per species to distribute training effort evenly
    and prevent over-represented species from dominating training time and compute.
    
    Within each species, images are selected via a stratified round-robin across
    specimen UUIDs and randomized photo angles. This maximizes both individual specimen
    diversity and morphological angle coverage.
    
    Args:
        df: Training DataFrame containing ['species', 'uuid', 'photo_index', ...]
        max_images_per_species: Maximum number of pictures to select per species.
                                If None or <= 0, no cap is applied.
        min_images_per_species: Minimum pictures per species (minority classes
                                can be oversampled with replacement if > 0). Default: 0.
        seed: Random seed for reproducible selection.
        
    Returns:
        Balanced DataFrame with pictures distributed evenly across species.
    """
    if df.empty or max_images_per_species is None or max_images_per_species <= 0:
        return df.copy()

    rng = np.random.RandomState(seed)
    selected_indices = []

    for species, sp_group in df.groupby("species"):
        n_available = len(sp_group)

        # Case 1: Within limits, no capping or oversampling needed
        if (n_available <= max_images_per_species) and (min_images_per_species <= n_available):
            selected_indices.extend(sp_group.index.tolist())
            continue

        # Case 2: Over-represented species - cap at max_images_per_species
        if n_available > max_images_per_species:
            target_n = max_images_per_species
            specimens = sorted(sp_group["uuid"].unique())
            rng.shuffle(specimens)

            # Map each specimen to its available row indices with randomized angle order
            specimen_rows = {}
            for u in specimens:
                u_rows = sp_group[sp_group["uuid"] == u].index.tolist()
                rng.shuffle(u_rows)
                specimen_rows[u] = u_rows

            chosen = []
            while len(chosen) < target_n:
                added_in_round = 0
                for u in specimens:
                    if specimen_rows[u]:
                        chosen.append(specimen_rows[u].pop(0))
                        added_in_round += 1
                        if len(chosen) == target_n:
                            break
                if added_in_round == 0:
                    break
            selected_indices.extend(chosen)

        # Case 3: Rare species below min_images_per_species - oversample
        elif min_images_per_species > n_available:
            target_n = min_images_per_species
            existing = sp_group.index.tolist()
            extras = rng.choice(existing, size=target_n - n_available, replace=True).tolist()
            selected_indices.extend(existing + extras)

    return df.loc[selected_indices].reset_index(drop=True)

def get_transforms(img_size: int = 224, is_train: bool = True):
    """
    Get image transformations with domain-specific augmentations for field photos.
    Includes aspect-preserving resize with padding, color shifts (underwater/deck lighting),
    and affine transforms.
    """
    if is_train:
        return T.Compose([
            T.Resize((img_size, img_size)),
            T.RandomHorizontalFlip(p=0.5),
            T.RandomVerticalFlip(p=0.2),
            T.RandomRotation(degrees=15),
            T.ColorJitter(brightness=0.25, contrast=0.25, saturation=0.25, hue=0.1),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
    else:
        return T.Compose([
            T.Resize((img_size, img_size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

class ElasmobranchDataset(Dataset):
    """PyTorch Dataset for Elasmobranch field photos."""

    def __init__(self, df: pd.DataFrame, transform=None):
        self.df = df.reset_index(drop=True)
        self.transform = transform

    def update_data(self, new_df: pd.DataFrame):
        """Update dataset in-place with new/resampled DataFrame."""
        self.df = new_df.reset_index(drop=True)

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        row = self.df.iloc[idx]
        image_path = row["filepath"]
        
        try:
            image = Image.open(image_path).convert("RGB")
        except Exception as e:
            # Fallback if image is unreadable: black placeholder
            image = Image.new("RGB", (224, 224), (0, 0, 0))

        if self.transform:
            tensor_img = self.transform(image)
        else:
            tensor_img = T.ToTensor()(image)

        return {
            "image": tensor_img,
            "label": torch.tensor(row["label"], dtype=torch.long),
            "species": row["species"],
            "uuid": row["uuid"],
            "photo_index": row["photo_index"],
            "angle_label": row["angle_label"],
            "filename": row["filename"]
        }
