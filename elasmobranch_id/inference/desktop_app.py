"""
Standalone Python Desktop GUI for Elasmobranch Species Identification.

Native Tkinter application:
- Works 100% locally and offline.
- Supports multi-angle photo uploads for the same specimen.
- Displays real-time top-3 prediction probabilities and confidence meter.
- Prompts data collectors for specific diagnostic angles when identification is uncertain.
"""

import os
from pathlib import Path
import sys

# Ensure module path resolution works across all macOS launch methods
APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(ROOT_DIR / "src"))

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List

from PIL import Image, ImageTk

# Import standalone inference engine
from standalone_engine import StandaloneElasmobranchClassifier

class ElasmobranchDesktopApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Elasmobranch Species Identification System (WCS Field Tool)")
        self.root.geometry("1050x780")
        self.root.minsize(950, 700)

        # macOS window focus & keybindings
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after_idle(self.root.attributes, "-topmost", False)
        except Exception:
            pass

        self.root.bind("<Command-o>", lambda e: self.select_photos())
        self.root.bind("<Command-q>", lambda e: self.root.quit())

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # State
        self.selected_image_paths: List[str] = []
        self.thumbnails: List[ImageTk.PhotoImage] = []

        # Find model path
        self.model_path = str(ROOT_DIR / "models/elasmobranch_mobilenet.onnx")
        self.meta_path = str(ROOT_DIR / "models/metadata.json")

        self.classifier = None
        self._init_classifier()
        self._build_ui()

    def _init_classifier(self):
        try:
            if Path(self.model_path).exists():
                self.classifier = StandaloneElasmobranchClassifier(self.model_path, self.meta_path)
            else:
                self.classifier = None
        except Exception as e:
            self.classifier = None
            print(f"Warning: Could not initialize classifier: {e}")

    def _build_ui(self):
        # 1. Header Frame
        header_frame = tk.Frame(self.root, bg="#1a365d", pady=15)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame,
            text="🦈 Elasmobranch Species Identification Field Assistant",
            font=("Helvetica", 18, "bold"),
            fg="white",
            bg="#1a365d"
        )
        title_label.pack()

        subtitle_label = tk.Label(
            header_frame,
            text="Standalone On-Device Identification for Sharks & Rays • Multi-Angle Diagnostic System",
            font=("Helvetica", 11),
            fg="#cbd5e0",
            bg="#1a365d"
        )
        subtitle_label.pack(pady=2)

        # 2. Main Content (Left: Photos & Input, Right: Prediction & Diagnostics)
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#e2e8f0", sashwidth=4)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Left Frame: Photo Management
        left_frame = tk.Frame(main_paned, bg="#ffffff", padx=15, pady=15, relief=tk.GROOVE, bd=1)
        main_paned.add(left_frame, minsize=420)

        tk.Label(
            left_frame,
            text="Specimen Photographs",
            font=("Helvetica", 14, "bold"),
            bg="#ffffff",
            fg="#2d3748"
        ).pack(anchor="w")

        tk.Label(
            left_frame,
            text="Select 1 or more photos of the same specimen (e.g. dorsal, ventral, head, tail):",
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#718096"
        ).pack(anchor="w", pady=(2, 10))

        # Action Buttons
        btn_box = tk.Frame(left_frame, bg="#ffffff")
        btn_box.pack(fill=tk.X, pady=5)

        self.btn_add_photos = tk.Button(
            btn_box,
            text="📁 Select Photo(s)",
            font=("Helvetica", 11, "bold"),
            bg="#2b6cb0",
            fg="black",
            padx=12,
            pady=6,
            command=self.select_photos
        )
        self.btn_add_photos.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_clear = tk.Button(
            btn_box,
            text="🗑️ Clear",
            font=("Helvetica", 10),
            bg="#edf2f7",
            padx=10,
            pady=6,
            command=self.clear_selection
        )
        self.btn_clear.pack(side=tk.LEFT)

        # Photo Gallery (Scrollable Frame)
        gallery_container = tk.Frame(left_frame, bg="#f7fafc", relief=tk.SUNKEN, bd=1)
        gallery_container.pack(fill=tk.BOTH, expand=True, pady=10)

        self.canvas = tk.Canvas(gallery_container, bg="#f7fafc", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(gallery_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#f7fafc")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.empty_label = tk.Label(
            self.scrollable_frame,
            text="No photos selected yet.\nClick 'Select Photo(s)' above.",
            font=("Helvetica", 11),
            fg="#a0aec0",
            bg="#f7fafc",
            pady=80
        )
        self.empty_label.pack(fill=tk.BOTH, expand=True)

        # Run Button
        self.btn_run = tk.Button(
            left_frame,
            text="🔍 Identify Species",
            font=("Helvetica", 12, "bold"),
            bg="#38a169",
            fg="black",
            pady=10,
            command=self.run_identification
        )
        self.btn_run.pack(fill=tk.X, pady=(5, 0))

        # Right Frame: Prediction Results & Diagnostic Guidance
        right_frame = tk.Frame(main_paned, bg="#ffffff", padx=15, pady=15, relief=tk.GROOVE, bd=1)
        main_paned.add(right_frame, minsize=480)

        tk.Label(
            right_frame,
            text="Identification Results",
            font=("Helvetica", 14, "bold"),
            bg="#ffffff",
            fg="#2d3748"
        ).pack(anchor="w")

        # Primary Result Card
        self.res_card = tk.Frame(right_frame, bg="#ebf8ff", relief=tk.RIDGE, bd=2, padx=15, pady=12)
        self.res_card.pack(fill=tk.X, pady=10)

        self.lbl_species_name = tk.Label(
            self.res_card,
            text="Awaiting Photo Submission",
            font=("Helvetica", 17, "bold"),
            bg="#ebf8ff",
            fg="#2b6cb0"
        )
        self.lbl_species_name.pack(anchor="w")

        self.lbl_confidence = tk.Label(
            self.res_card,
            text="Confidence: --",
            font=("Helvetica", 12),
            bg="#ebf8ff",
            fg="#4a5568"
        )
        self.lbl_confidence.pack(anchor="w", pady=(3, 0))

        # Top 3 Candidates
        tk.Label(
            right_frame,
            text="Top Predicted Candidates",
            font=("Helvetica", 12, "bold"),
            bg="#ffffff",
            fg="#2d3748"
        ).pack(anchor="w", pady=(10, 4))

        self.candidates_box = tk.Frame(right_frame, bg="#ffffff")
        self.candidates_box.pack(fill=tk.X, pady=2)

        self.cand_labels = []
        for i in range(3):
            lbl = tk.Label(
                self.candidates_box,
                text=f"{i+1}. --",
                font=("Helvetica", 10),
                bg="#ffffff",
                fg="#4a5568",
                anchor="w"
            )
            lbl.pack(fill=tk.X, pady=2)
            self.cand_labels.append(lbl)

        # Diagnostic Guidance & Recommended Angles Box
        self.diag_frame = tk.LabelFrame(
            right_frame,
            text="📋 Interactive Diagnostic Guidance & Angle Requests",
            font=("Helvetica", 11, "bold"),
            bg="#fffaf0",
            fg="#c05621",
            padx=12,
            pady=10
        )
        self.diag_frame.pack(fill=tk.BOTH, expand=True, pady=(15, 0))

        self.diag_msg = tk.Label(
            self.diag_frame,
            text="Upload specimen photos to begin.",
            font=("Helvetica", 10),
            bg="#fffaf0",
            fg="#2d3748",
            wraplength=420,
            justify=tk.LEFT
        )
        self.diag_msg.pack(anchor="w", pady=(2, 6))

        self.lbl_angles_header = tk.Label(
            self.diag_frame,
            text="Recommended Next Photo Angles:",
            font=("Helvetica", 10, "bold"),
            bg="#fffaf0",
            fg="#742a2a"
        )
        self.lbl_angles_header.pack(anchor="w", pady=(6, 2))

        self.angles_listbox = tk.Listbox(
            self.diag_frame,
            height=4,
            font=("Helvetica", 9),
            bg="#ffffff",
            relief=tk.SUNKEN,
            bd=1
        )
        self.angles_listbox.pack(fill=tk.X, pady=2)

        self.diag_notes = tk.Label(
            self.diag_frame,
            text="",
            font=("Helvetica", 9, "italic"),
            bg="#fffaf0",
            fg="#4a5568",
            wraplength=420,
            justify=tk.LEFT
        )
        self.diag_notes.pack(anchor="w", pady=(6, 0))

    def select_photos(self):
        files = filedialog.askopenfilenames(
            title="Select Elasmobranch Photos",
            filetypes=[("Image Files", "*.jpeg *.jpg *.png *.bmp *.webp")]
        )
        if files:
            self.empty_label.pack_forget()
            for f in files:
                if f not in self.selected_image_paths:
                    self.selected_image_paths.append(f)
            self.render_thumbnails()

    def clear_selection(self):
        self.selected_image_paths.clear()
        self.thumbnails.clear()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.empty_label = tk.Label(
            self.scrollable_frame,
            text="No photos selected yet.\nClick 'Select Photo(s)' above.",
            font=("Helvetica", 11),
            fg="#a0aec0",
            bg="#f7fafc",
            pady=80
        )
        self.empty_label.pack(fill=tk.BOTH, expand=True)

        self.lbl_species_name.config(text="Awaiting Photo Submission", fg="#2b6cb0")
        self.lbl_confidence.config(text="Confidence: --")
        for i, lbl in enumerate(self.cand_labels):
            lbl.config(text=f"{i+1}. --")
        self.diag_msg.config(text="Upload specimen photos to begin.")
        self.angles_listbox.delete(0, tk.END)
        self.diag_notes.config(text="")

    def render_thumbnails(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.thumbnails.clear()

        for idx, img_path in enumerate(self.selected_image_paths, 1):
            item_frame = tk.Frame(self.scrollable_frame, bg="#ffffff", relief=tk.GROOVE, bd=1, padx=6, pady=6)
            item_frame.pack(fill=tk.X, pady=4, padx=4)

            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail((70, 70))
                tk_img = ImageTk.PhotoImage(pil_img)
                self.thumbnails.append(tk_img)

                img_lbl = tk.Label(item_frame, image=tk_img, bg="#ffffff")
                img_lbl.pack(side=tk.LEFT, padx=(0, 10))
            except Exception as e:
                pass

            info_text = f"Photo #{idx}: {Path(img_path).name}"
            lbl_name = tk.Label(item_frame, text=info_text, font=("Helvetica", 10, "bold"), bg="#ffffff", fg="#2d3748")
            lbl_name.pack(side=tk.LEFT)

    def run_identification(self):
        if not self.selected_image_paths:
            messagebox.showwarning("No Photos", "Please select at least one photo first.")
            return

        if not self.classifier:
            self._init_classifier()
            if not self.classifier:
                messagebox.showerror(
                    "Model Missing",
                    "The ONNX model was not found at 'models/elasmobranch_mobilenet.onnx'.\nPlease train/export the model first."
                )
                return

        # Perform inference across all selected photos
        result = self.classifier.predict(self.selected_image_paths)

        top_sp = result["top_species"]
        top_conf = result["top_confidence"]
        tier = result["confidence_tier"]

        # Color-coded tier styling
        tier_colors = {
            "High Confidence": "#22543d",      # dark green
            "Moderate Confidence": "#744210",  # dark orange
            "Uncertain": "#742a2a"             # dark red
        }
        card_bg = {
            "High Confidence": "#f0fff4",
            "Moderate Confidence": "#fffaf0",
            "Uncertain": "#fff5f5"
        }.get(tier, "#ebf8ff")

        self.res_card.config(bg=card_bg)
        self.lbl_species_name.config(text=f"{top_sp}", fg=tier_colors.get(tier, "#2b6cb0"), bg=card_bg)
        self.lbl_confidence.config(
            text=f"Confidence: {top_conf*100:.1f}%  [{tier.upper()}]  ({result['num_photos_analyzed']} angle(s) pooled)",
            bg=card_bg
        )

        # Update Top 3 list
        for i, cand in enumerate(result["top_k"]):
            if i < len(self.cand_labels):
                self.cand_labels[i].config(
                    text=f"{i+1}. {cand['species']} — {cand['confidence_pct']}"
                )

        # Update Diagnostic Guidance & Angle Requests
        rec = result["recommendation"]
        self.diag_msg.config(text=rec["message"])

        self.angles_listbox.delete(0, tk.END)
        if rec.get("suggested_angles"):
            self.lbl_angles_header.pack(anchor="w", pady=(6, 2))
            self.angles_listbox.pack(fill=tk.X, pady=2)
            for a in rec["suggested_angles"]:
                self.angles_listbox.insert(tk.END, f"  📸 {a}")
        else:
            self.lbl_angles_header.pack_forget()
            self.angles_listbox.pack_forget()

        self.diag_notes.config(text=rec.get("diagnostic_notes", ""))

def launch_app():
    root = tk.Tk()
    app = ElasmobranchDesktopApp(root)
    root.mainloop()

if __name__ == "__main__":
    launch_app()
