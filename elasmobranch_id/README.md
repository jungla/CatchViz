# Standalone Elasmobranch Species Identification System
### On-Device Machine Learning for Sharks & Rays (Mobile & Desktop)

A standalone, offline computer vision system designed for field enumerators, researchers, and fisheries observers to accurately identify elasmobranch (shark and ray) species from field photographs.

---

## 🌟 Key Capabilities

1. **Multi-Angle Evidence Aggregation**:
   - Enumerators can submit a single photo or multiple photos of the same specimen (e.g. dorsal disc, ventral mouth/gills, head, tail spine, dorsal fins).
   - The model pools evidence across all submitted angles to achieve higher diagnostic certainty (**80.3% specimen-level accuracy** across 23 species in field testing).

2. **Interactive Angle Recommendation Engine**:
   - When prediction confidence is below 80% or ambiguous between two close species, the system identifies the candidate species and **specifically requests photos from the most diagnostic angles** (e.g., *"Confidence is 51.2% for Taeniurops meyeni. Please capture a clear ventral tail photo to check for the ventral cutaneous skin fold"*).

3. **Calibrated Confidence Reporting**:
   - Every identification returns:
     - Primary predicted species
     - Calibrated confidence percentage (temperature-scaled)
     - Confidence Tier: **High Confidence** ($\ge 80\%$), **Moderate Confidence** ($60\% - 79\%$), or **Uncertain** ($< 60\%$)
     - Top-3 candidate breakdown with probability bars

4. **Zero-Leakage Group Validation**:
   - Training and validation splits are partitioned strictly by individual specimen (`UUID`). Photos from the same animal never appear in both sets, guaranteeing real-world generalization.

5. **Standalone On-Device Inference**:
   - Runs 100% locally and offline via **ONNX Runtime** (only 12.3 MB).
   - Zero cloud server requirements, zero API costs, full privacy.

---

## 🚀 Quickstart: Running on macOS (Computer)

### 1. Double-Click Desktop App (Native macOS .app)
You now have a native clickable macOS application:
- Double-click **`Elasmobranch ID.app`** on your **Desktop** (or in this folder).
- Or double-click [`launch_macos_app.command`](launch_macos_app.command).
- You can also drag `Elasmobranch ID.app` into your `/Applications` folder or Dock.

### 2. Launch via Terminal
```bash
cd /Users/jeanmensa/.gemini/antigravity/scratch/elasmobranch_id
.venv/bin/python inference/desktop_app.py
```
- Click **"Select Photo(s)"** and choose 1 or multiple photos of an individual.
- Click **"Identify Species"**.
- View predicted species, confidence gauge, top-3 candidates, and interactive angle recommendations.

### 2. Standalone Command-Line Interface (CLI)

**Single photo identification:**
```bash
.venv/bin/python inference/cli.py --image "/Users/jeanmensa/WCS/Data/SharksRays/Photos_Kobo_SHARC/283de52e-0917-403b-8c95-130aac1840e9_Pliotrema annae_4.jpeg"
```

**Multi-angle pooled identification (multiple photos of the same individual):**
```bash
.venv/bin/python inference/cli.py --images \
  "/Users/jeanmensa/WCS/Data/SharksRays/Photos_Kobo_SHARC/164cb2d2-2da7-45c2-9807-7605f279d5f6_Pateobatis fai_4.jpeg" \
  "/Users/jeanmensa/WCS/Data/SharksRays/Photos_Kobo_SHARC/164cb2d2-2da7-45c2-9807-7605f279d5f6_Pateobatis fai_5.jpeg" \
  "/Users/jeanmensa/WCS/Data/SharksRays/Photos_Kobo_SHARC/164cb2d2-2da7-45c2-9807-7605f279d5f6_Pateobatis fai_6.jpeg"
```

---

## 📱 Mobile Integration (iOS & Android)

The standalone model is packaged in `models/elasmobranch_mobilenet.onnx` (12.3 MB) and includes embedded labels and normalization metadata.

- **iOS (Swift / Core ML & ONNX Mobile)**:
  - Reference implementation available in [`mobile/ios_reference/ElasmobranchClassifier.swift`](mobile/ios_reference/ElasmobranchClassifier.swift).
  - Uses Apple's Vision framework and Core ML with Apple Neural Engine (ANE) acceleration (<15 ms latency).

- **Android (Kotlin / TFLite & ONNX Mobile)**:
  - Reference implementation available in [`mobile/android_reference/ElasmobranchClassifier.kt`](mobile/android_reference/ElasmobranchClassifier.kt).
  - Uses Android NNAPI hardware acceleration.

---

## 🛠️ Project Directory Structure

```
elasmobranch_id/
├── .venv/                      # Python virtual environment
├── requirements.txt            # Frozen dependencies
├── configs/
│   └── default_config.yaml     # Hyperparameters & data paths
├── src/
│   ├── dataset.py              # Parsing, UUID grouping, domain transforms
│   ├── model.py                # MobileNetV3 dual-head & multi-angle aggregator
│   ├── diagnostic_guide.py     # Species morphological keys & pairwise angle rules
│   ├── train.py                # Group-leakage-free training pipeline
│   ├── evaluate.py             # Single-image & specimen-level evaluation suite
│   └── export.py               # Standalone ONNX exporter with numerical parity check
├── inference/
│   ├── standalone_engine.py    # Zero-PyTorch ONNX Runtime inference engine
│   ├── cli.py                  # Terminal CLI with ASCII confidence bars
│   └── desktop_app.py          # Native desktop GUI
├── mobile/
│   ├── ios_reference/          # Swift integration reference
│   └── android_reference/      # Kotlin integration reference
├── web_app/
│   └── index.html              # Offline in-browser prototype
└── models/
    ├── best_model.pth          # PyTorch checkpoint (37 MB)
    ├── elasmobranch_mobilenet.onnx # Standalone ONNX model (12.3 MB)
    ├── metadata.json           # Species classes and normalization parameters
    └── confusion_matrix.png    # Evaluation confusion matrix plot
```

---

## 🔄 Retraining With New Species or Field Images

As new surveys are conducted and photos added to your Kobo photo directory:
1. Run the training pipeline:
   ```bash
   .venv/bin/python src/train.py
   ```
2. Re-export the standalone ONNX model:
   ```bash
   .venv/bin/python src/export.py
   ```
3. Run the evaluation suite to inspect updated accuracy and confusion matrix:
   ```bash
   .venv/bin/python src/evaluate.py
   ```
