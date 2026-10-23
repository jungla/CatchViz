# KoboToolbox Automated AI Species Identification Webhook

This service automatically identifies shark and ray species from field survey photos submitted via **KoboCollect / KoboToolbox** and records the results back into your Kobo project.

---

## 🚀 How It Works

1. **Field Enumerator submits form**: KoboCollect syncs survey photos (dorsal, ventral, head, etc.) to KoboToolbox.
2. **Kobo triggers Webhook**: KoboToolbox immediately posts the submission data to your Render web service (`https://your-app.onrender.com/webhook/kobo`).
3. **Background AI Processing**:
   - Downloads the high-resolution photo attachments securely using your `KOBO_API_TOKEN`.
   - Runs on-device multi-angle pooling with your 85.3% accuracy ONNX model (`convnext_tiny`).
4. **Auto-Writeback to Kobo**:
   - Adds an **AI Diagnostic Note** to the submission in KoboToolbox listing the top species, confidence percentage, and recommended actions.
   - Sets the **Validation Status**:
     - `Approved` if Confidence $\ge 80\%$.
     - `Flagged for Review` if Confidence $< 60\%$.

---

## 🛠️ Deploying to Render.com

### Option A: Deploy via GitHub (Recommended)

1. Push this repository to GitHub.
2. In [Render Dashboard](https://dashboard.render.com):
   - Click **New +** $\rightarrow$ **Web Service**.
   - Connect your GitHub repository.
   - Set **Runtime**: `Docker` (or Python).
   - Set **Dockerfile Path**: `kobo_service/Dockerfile`.
   - Set **Instance Type**: Free or Starter (CPU is all that's needed; model uses <300MB RAM).
3. Under **Environment Variables**, set:
   - `KOBO_API_TOKEN`: Your Kobo API token (found in Kobo Account Settings $\rightarrow$ Account Details $\rightarrow$ API Token).
   - `KOBO_SERVER_URL`: `https://kf.kobotoolbox.org` (or `https://eu.kobotoolbox.org` if using the EU server).
4. Click **Deploy Web Service**.

---

## 🔗 Configuring KoboToolbox (2-Minute Setup)

1. Open your project on [KoboToolbox](https://kf.kobotoolbox.org).
2. Go to **Settings** $\rightarrow$ **REST Services** (left sidebar).
3. Click **+ Register a new service**.
4. Configure the service:
   - **Service Name**: `Shark & Ray AI Identifier`
   - **Endpoint URL**: `https://<YOUR-RENDER-APP-NAME>.onrender.com/webhook/kobo`
   - **Send submitted data in body**: ✅ Checked.
5. Click **Save**.

Now, whenever a field enumerator submits a record with shark or ray photos, the AI will classify it automatically within seconds!
