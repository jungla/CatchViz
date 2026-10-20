"""
One-Step Retraining & Re-Export Pipeline for Elasmobranch Identification.

Usage:
  .venv/bin/python retrain.py
"""

import subprocess
import sys
import time
from pathlib import Path

def run_step(step_name: str, script_path: str):
    print("\n" + "=" * 65)
    print(f"  STEP: {step_name.upper()}")
    print("=" * 65)
    
    start_time = time.time()
    python_bin = sys.executable
    cmd = [python_bin, str(script_path)]
    
    result = subprocess.run(cmd)
    elapsed = time.time() - start_time
    
    if result.returncode != 0:
        print(f"\n❌ Error during {step_name} (Exit code {result.returncode}). Aborting pipeline.", file=sys.stderr)
        sys.exit(result.returncode)
    
    print(f"✓ {step_name} completed successfully in {elapsed:.1f}s.")

def main():
    root = Path(__file__).parent
    
    print("\n" + "#" * 65)
    print("  🦈 ELASMOBRANCH FULL RETRAINING & EXPORT PIPELINE")
    print("#" * 65)
    
    # 1. Train Model
    run_step("Model Retraining (Progressive Fine-Tuning)", root / "src/train.py")
    
    # 2. Export to Standalone ONNX
    run_step("Standalone Model Export (ONNX & Metadata)", root / "src/export.py")
    
    # 3. Evaluate & Update Confusion Matrix
    run_step("Comprehensive Evaluation & Confusion Matrix", root / "src/evaluate.py")
    
    print("\n" + "#" * 65)
    print("  🎉 RETRAINING COMPLETE!")
    print("  • Updated checkpoint : models/best_model.pth")
    print("  • Updated ONNX model : models/elasmobranch_mobilenet.onnx")
    print("  • Updated metadata   : models/metadata.json")
    print("  • Updated plot       : models/confusion_matrix.png")
    print("  The Desktop GUI and CLI will automatically use the updated model!")
    print("#" * 65 + "\n")

if __name__ == "__main__":
    main()
