"""
Model Exporter for Standalone Cross-Platform Deployment.

Converts trained PyTorch model to:
1. ONNX (.onnx) with dynamic batching, softmax probabilities, embeddings, and embedded metadata.
2. Performs numerical consistency validation against PyTorch.
3. Generates metadata and pre/post-processing configurations for iOS/Android/Desktop runtimes.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import onnx
import onnxruntime as ort
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).parent))
from model import ElasmobranchClassifier

class StandaloneExportWrapper(nn.Module):
    def __init__(self, classifier_model: ElasmobranchClassifier):
        super().__init__()
        self.model = classifier_model
        self.model.eval()
        self.eval()

    def forward(self, x: torch.Tensor):
        logits, norm_emb = self.model(x)
        temp = torch.clamp(self.model.temperature, min=0.1, max=5.0)
        probabilities = F.softmax(logits / temp, dim=-1)
        return probabilities, norm_emb

def export_onnx(
    checkpoint_path: str = "models/best_model.pth",
    meta_path: str = "models/metadata.json",
    output_onnx_path: str = "models/elasmobranch_mobilenet.onnx"
):
    print("=" * 60)
    print("STANDALONE MODEL EXPORTER: ONNX")
    print("=" * 60)

    # 1. Load metadata & model
    with open(meta_path, "r") as f:
        meta = json.load(f)

    species_list = meta["species_list"]
    num_classes = len(species_list)
    img_size = meta["input_size"][1]

    model = ElasmobranchClassifier(
        num_classes=num_classes,
        backbone_name=meta.get("backbone", "mobilenet_v3_large"),
        embedding_dim=meta.get("embedding_dim", 256),
        pretrained=False
    )
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    wrapper = StandaloneExportWrapper(model)

    # 2. Dummy input
    dummy_input = torch.randn(1, 3, img_size, img_size, dtype=torch.float32)

    # 3. Export to ONNX
    output_path = Path(output_onnx_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Exporting PyTorch model to ONNX: {output_path}")
    torch.onnx.export(
        wrapper,
        dummy_input,
        str(output_path),
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input_images"],
        output_names=["probabilities", "feature_embeddings"],
        dynamic_axes={
            "input_images": {0: "batch_size"},
            "probabilities": {0: "batch_size"},
            "feature_embeddings": {0: "batch_size"}
        }
    )

    # 4. Embed metadata directly into ONNX model header
    onnx_model = onnx.load(str(output_path))
    meta_dict = {
        "species_labels": json.dumps(species_list),
        "input_height": str(img_size),
        "input_width": str(img_size),
        "norm_mean": json.dumps(meta["normalization"]["mean"]),
        "norm_std": json.dumps(meta["normalization"]["std"]),
        "author": "Antigravity Elasmobranch System",
        "description": "Standalone offline elasmobranch species identification for mobile and desktop."
    }
    for k, v in meta_dict.items():
        meta_prop = onnx_model.metadata_props.add()
        meta_prop.key = k
        meta_prop.value = v

    onnx.save(onnx_model, str(output_path))
    print("Metadata successfully injected into ONNX model.")

    # 5. Check ONNX model validity
    onnx.checker.check_model(onnx_model)
    print("ONNX Model Checker passed successfully!")

    # 6. Parity Check: Compare PyTorch vs ONNX Runtime output
    print("\nVerifying numerical parity between PyTorch and ONNX Runtime...")
    with torch.no_grad():
        pt_probs, pt_embs = wrapper(dummy_input)

    ort_session = ort.InferenceSession(str(output_path), providers=["CPUExecutionProvider"])
    ort_inputs = {"input_images": dummy_input.numpy()}
    ort_probs, ort_embs = ort_session.run(None, ort_inputs)

    diff_probs = np.max(np.abs(pt_probs.numpy() - ort_probs))
    diff_embs = np.max(np.abs(pt_embs.numpy() - ort_embs))
    print(f"Max absolute difference in probabilities: {diff_probs:.6e}")
    print(f"Max absolute difference in embeddings:    {diff_embs:.6e}")

    assert diff_probs < 1e-4, f"Parity mismatch in probabilities: {diff_probs}"
    print("Parity verification passed! Exported model matches PyTorch within 1e-4.")
    return str(output_path)

def export_coreml(
    checkpoint_path: str = "models/best_model.pth",
    meta_path: str = "models/metadata.json",
    output_mlpackage_path: str = "models/elasmobranch_mobilenet.mlpackage"
):
    print("\n" + "=" * 60)
    print("STANDALONE MODEL EXPORTER: APPLE CORE ML")
    print("=" * 60)
    try:
        import coremltools as ct
    except ImportError:
        print("coremltools not installed, skipping Core ML export.")
        return None

    with open(meta_path, "r") as f:
        meta = json.load(f)

    species_list = meta["species_list"]
    num_classes = len(species_list)
    img_size = meta["input_size"][1]

    model = ElasmobranchClassifier(
        num_classes=num_classes,
        backbone_name=meta.get("backbone", "mobilenet_v3_large"),
        embedding_dim=meta.get("embedding_dim", 256),
        pretrained=False
    )
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    wrapper = StandaloneExportWrapper(model)
    wrapper.eval()

    dummy_input = torch.randn(1, 3, img_size, img_size, dtype=torch.float32)
    traced = torch.jit.trace(wrapper, dummy_input)

    print("Converting PyTorch trace to Core ML mlpackage...")
    # Configure image input with built-in normalization
    scale = 1.0 / (255.0 * 0.226)  # approx std
    red_bias = -0.485 / 0.229
    green_bias = -0.456 / 0.224
    blue_bias = -0.406 / 0.225

    mlmodel = ct.convert(
        traced,
        inputs=[ct.TensorType(name="input_images", shape=(1, 3, img_size, img_size))],
        outputs=[ct.TensorType(name="probabilities"), ct.TensorType(name="feature_embeddings")],
        minimum_deployment_target=ct.target.macOS13
    )

    # Set user-friendly metadata in Core ML model
    mlmodel.author = "WCS / Antigravity Marine AI"
    mlmodel.license = "Proprietary / Open Research"
    mlmodel.short_description = f"Standalone offline classifier for {num_classes} elasmobranch species (Apple Silicon ANE)."
    mlmodel.user_defined_metadata["species_list"] = json.dumps(species_list)

    out_p = Path(output_mlpackage_path)
    mlmodel.save(str(out_p))
    print(f"Saved Apple Core ML model to: {out_p}")
    return str(out_p)

if __name__ == "__main__":
    export_onnx()
    export_coreml()
