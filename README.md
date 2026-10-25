# NutriScan — Vercel-ready

## Deploy to Vercel
1. Upload the **contents of this folder** to the root of your GitHub repository (`app.py`, `requirements.txt`, `vercel.json`, etc.).
2. Import or open that repository in Vercel.
3. In **Project Settings → Environment Variables**, add `GROQ_API_KEY` with your Groq API key.
4. Deploy or redeploy the project.
5. Open the deployed HTTPS URL and allow camera access in your browser.

## Camera behavior
The camera runs in the visitor's browser using `getUserMedia()`. This is required for Vercel because the hosted server cannot access a visitor's local webcam. The browser sends captured frames/crops to the `/scan` endpoint.

## OCR note
Groq Vision is the primary label-reading path. Tesseract OCR is an optional fallback; the native Tesseract executable is not bundled with the standard Vercel Python runtime, so OCR fallback may be unavailable there.
