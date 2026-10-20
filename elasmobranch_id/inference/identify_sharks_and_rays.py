"""
Modern Standalone Web/Desktop Application for Elasmobranch Species Identification.

Bypasses Apple Tcl/Tk system bugs on macOS by utilizing a modern, local browser interface.
Features:
- Multi-photo drag-and-drop file uploader.
- Thumbnail gallery preview with angle indicators.
- Instant ONNX runtime on-device inference.
- Calibrated confidence scoring and color-coded tier cards.
- Interactive angle recommendation engine when confidence is low or ambiguous.
"""

import json
from pathlib import Path
import sys

from PIL import Image
import streamlit as st

# Setup import paths
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

from standalone_engine import StandaloneElasmobranchClassifier

st.set_page_config(
    page_title="Elasmobranch Species Identification",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a365d;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4a5568;
        margin-bottom: 1.5rem;
    }
    .pred-card {
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        border-left: 6px solid #2b6cb0;
        background-color: #f7fafc;
    }
    .pred-title {
        font-size: 1.8rem;
        font-weight: 800;
        margin-bottom: 0.4rem;
    }
    .tier-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .tier-high {
        background-color: #c6f6d5;
        color: #22543d;
    }
    .tier-mod {
        background-color: #feebc8;
        color: #744210;
    }
    .tier-low {
        background-color: #fed7d7;
        color: #742a2a;
    }
    .rec-box {
        background-color: #fffaf0;
        border: 1px solid #ecc94b;
        border-radius: 8px;
        padding: 1.2rem;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

import datetime

def get_model_info():
    model_path = ROOT_DIR / "models/elasmobranch_mobilenet.onnx"
    meta_path = ROOT_DIR / "models/metadata.json"
    mtime = model_path.stat().st_mtime if model_path.exists() else 0.0
    
    meta = {}
    if meta_path.exists():
        try:
            with open(meta_path, "r") as f:
                meta = json.load(f)
        except Exception:
            pass
            
    return mtime, meta

@st.cache_resource
def load_classifier(mtime_timestamp: float):
    """Loads the model, automatically refreshing if the file modification timestamp changes."""
    model_path = str(ROOT_DIR / "models/elasmobranch_mobilenet.onnx")
    meta_path = str(ROOT_DIR / "models/metadata.json")
    return StandaloneElasmobranchClassifier(model_path, meta_path)

def main():
    st.markdown('<div class="main-header">🦈 Elasmobranch Species Identification</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Standalone On-Device Identification for Sharks & Rays • Multi-Angle Diagnostic System</div>', unsafe_allow_html=True)

    model_mtime, model_meta = get_model_info()

    try:
        classifier = load_classifier(model_mtime)
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return

    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Active Model Status")
        st.success(f"**Live Model Loaded**")
        st.markdown(f"**Species Count:** {len(classifier.species_list)} classes")
        
        # Display model version timestamp
        if model_meta.get("timestamp"):
            st.markdown(f"**Trained On:** `{model_meta['timestamp']}`")
        if model_mtime > 0:
            mtime_str = datetime.datetime.fromtimestamp(model_mtime).strftime("%Y-%m-%d %H:%M:%S")
            st.markdown(f"**Last Exported:** `{mtime_str}`")
        if model_meta.get("best_val_acc"):
            st.markdown(f"**Validation Accuracy:** `{model_meta['best_val_acc']*100:.1f}%`")

        if st.button("🔄 Reload Model from Disk"):
            st.cache_resource.clear()
            st.rerun()

        st.divider()
        st.markdown(f"**Runtime Engine:** ONNX Runtime (Standalone)")
        st.markdown(f"**Model Size:** 12.3 MB")
        
        st.divider()
        st.subheader("Confidence Thresholds")
        high_thresh = st.slider("High Confidence Threshold (%)", min_value=50, max_value=95, value=80, step=5) / 100.0
        mod_thresh = st.slider("Moderate Threshold (%)", min_value=30, max_value=75, value=60, step=5) / 100.0

        st.divider()
        st.markdown("### Field Diagnostic Guide")
        st.caption("Submit multiple photos of the same specimen (dorsal, ventral, head, fins, tail) for maximum identification accuracy.")

    # Main content layout
    col_input, col_results = st.columns([1, 1], gap="large")

    with col_input:
        st.subheader("📁 Upload Specimen Photo(s)")
        uploaded_files = st.file_uploader(
            "Select 1 or more photos of the specimen from different angles:",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} photo(s) selected:**")
            thumb_cols = st.columns(min(len(uploaded_files), 4))
            images_pil = []
            for idx, file in enumerate(uploaded_files):
                img = Image.open(file)
                images_pil.append(img)
                with thumb_cols[idx % 4]:
                    st.image(img, caption=f"Photo #{idx+1}", use_container_width=True)
        else:
            st.info("👆 Upload or drag & drop specimen photos above to begin identification.")

    with col_results:
        st.subheader("📊 Identification Results")
        if uploaded_files and len(images_pil) > 0:
            with st.spinner("Analyzing anatomical features..."):
                result = classifier.predict(
                    images_pil,
                    top_k=5,
                    high_conf_thresh=high_thresh,
                    mod_conf_thresh=mod_thresh
                )

            top_sp = result["top_species"]
            top_conf = result["top_confidence"]
            tier = result["confidence_tier"]

            tier_class = {
                "High Confidence": "tier-high",
                "Moderate Confidence": "tier-mod",
                "Uncertain": "tier-low"
            }.get(tier, "tier-mod")

            # Main Prediction Card
            st.markdown(f"""
            <div class="pred-card">
                <span class="tier-badge {tier_class}">{tier.upper()}</span>
                <div class="pred-title">{top_sp}</div>
                <div style="font-size: 1.1rem; color: #4a5568;">
                    Confidence: <strong>{top_conf*100:.1f}%</strong> (pooled across {result['num_photos_analyzed']} angle(s))
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Top Candidates Breakdown
            st.markdown("#### Top Predicted Candidates")
            for rank, cand in enumerate(result["top_k"][:3], 1):
                col_name, col_bar = st.columns([3, 2])
                with col_name:
                    st.markdown(f"**{rank}. {cand['species']}** ({cand['confidence_pct']})")
                with col_bar:
                    st.progress(cand["confidence"])

            # Diagnostic Guidance Box
            rec = result["recommendation"]
            st.markdown("#### 📋 Diagnostic Guidance & Angle Requests")
            if tier != "High Confidence":
                st.warning(f"**Status:** {rec['message']}")
            else:
                st.success(f"**Status:** {rec['message']}")

            if rec.get("diagnostic_notes"):
                st.info(f"**Morphological Key:** {rec['diagnostic_notes']}")

            if rec.get("suggested_angles"):
                st.markdown("**📸 Recommended Next Photo Angles to Confirm Identification:**")
                for a in rec["suggested_angles"]:
                    st.markdown(f"- 📷 **{a}**")
        else:
            st.markdown(
                """
                <div style="text-align: center; padding: 3rem 1rem; color: #a0aec0; border: 2px dashed #e2e8f0; border-radius: 8px;">
                    Awaiting photo upload...
                </div>
                """,
                unsafe_allow_html=True
            )

if __name__ == "__main__":
    main()
