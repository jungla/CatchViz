"""
Standalone Command-Line Interface for Elasmobranch Species Identification.

Usage:
  # Single photo:
  python inference/cli.py --image /path/to/shark.jpeg

  # Multiple photos of same specimen:
  python inference/cli.py --images /path/to/photo4.jpeg /path/to/photo5.jpeg

  # Specify custom model:
  python inference/cli.py --image /path/to/ray.jpeg --model models/elasmobranch_mobilenet.onnx
"""

import argparse
from pathlib import Path
import sys

from standalone_engine import StandaloneElasmobranchClassifier

def render_bar(pct: float, width: int = 25) -> str:
    """Render ASCII confidence bar."""
    filled = int(round(pct * width))
    empty = width - filled
    return "█" * filled + "░" * empty

def main():
    parser = argparse.ArgumentParser(
        description="Standalone Elasmobranch Species Identification System"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=str, help="Path to a single specimen image")
    group.add_argument("--images", nargs="+", type=str, help="Paths to multiple angle images of the same specimen")

    parser.add_argument(
        "--model",
        type=str,
        default="models/elasmobranch_mobilenet.onnx",
        help="Path to standalone ONNX model file"
    )
    parser.add_argument(
        "--meta",
        type=str,
        default="models/metadata.json",
        help="Path to metadata.json"
    )
    args = parser.parse_args()

    # Determine input list
    images = [args.image] if args.image else args.images

    # Validate image paths
    for p in images:
        if not Path(p).exists():
            print(f"Error: Image not found: {p}", file=sys.stderr)
            sys.exit(1)

    print("\n" + "=" * 65)
    print("  ELASMOBRANCH ON-DEVICE SPECIES IDENTIFICATION")
    print("=" * 65)
    print(f"Loading standalone model: {args.model}")

    try:
        classifier = StandaloneElasmobranchClassifier(args.model, args.meta)
    except Exception as e:
        print(f"Error loading model: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing {len(images)} photo(s)...")
    for i, p in enumerate(images, 1):
        print(f"  [{i}] {Path(p).name}")

    result = classifier.predict(images)

    top_sp = result["top_species"]
    top_conf = result["top_confidence"]
    tier = result["confidence_tier"]

    # Formatting colors / styles
    tier_tag = {
        "High Confidence": "[HIGH CONFIDENCE]",
        "Moderate Confidence": "[MODERATE CONFIDENCE]",
        "Uncertain": "[UNCERTAIN / AMBIGUOUS]"
    }.get(tier, f"[{tier.upper()}]")

    print("\n" + "-" * 65)
    print(f"PRIMARY PREDICTION : {top_sp}")
    print(f"CONFIDENCE         : {top_conf*100:.1f}%  {render_bar(top_conf)}  {tier_tag}")
    print("-" * 65)

    print("\nTOP-3 SPECIES CANDIDATES:")
    for rank, cand in enumerate(result["top_k"], 1):
        bar = render_bar(cand["confidence"], width=15)
        print(f"  {rank}. {cand['species']:<30} {cand['confidence_pct']:>6}  {bar}")

    rec = result["recommendation"]
    print("\n" + "=" * 65)
    print(f"DIAGNOSTIC GUIDANCE & NEXT STEPS:")
    print(f"Status Note: {rec['message']}")
    if rec.get("diagnostic_notes"):
        print(f"\nMorphological Key:\n  {rec['diagnostic_notes']}")

    if rec.get("suggested_angles"):
        print("\nRECOMMENDED NEXT PHOTO ANGLES TO CONFIRM IDENTIFICATION:")
        for idx, angle in enumerate(rec["suggested_angles"], 1):
            print(f"  -> [{idx}] {angle}")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    main()
