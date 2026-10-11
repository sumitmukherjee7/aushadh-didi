# 👩‍⚕️ Aushadh-Didi (औषध-दीदी)

> **Voice-First Prescription & Medicine Safety Guard for Grandparents & Caregivers**  
> *Built 100% on the Sarvam AI Sovereign Stack for Indian Languages.*

[![Sarvam AI](https://img.shields.io/badge/Powered%20By-Sarvam%20AI-0284c7?style=for-the-badge)](https://sarvam.ai)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

---

## 🌟 The Problem
In India, millions of elderly patients and non-English-literate family members receive scrawled, barely legible doctor prescriptions with cryptic medical jargon (*e.g., "Tab. Metformin 500mg SR bid pc"*). 

Patients and anxious caregivers ask in spoken Hindi, Tamil, or Hinglish:
> *"दीदी, ये मेटफॉर्मिन सुबह खाली पेट लेनी है या नाश्ते के बाद? और क्या इसे बीपी की गोली के साथ ले सकते हैं?"*

Because they cannot read tiny English chemical labels or handwriting, accidental dosing errors, skipped medications, and drug interaction risks are rampant.

---

## 💡 The Solution: Aushadh-Didi
**Aushadh-Didi** is a voice-first healthcare companion that bridges the gap between doctor prescriptions and elderly patients using **100% native Indian language AI**:

1. **Uploads a photo of the prescription** (handwritten or printed Rx).
2. **Speaks their concern or question** as a natural voice note in Hindi, Hinglish, Tamil, etc.
3. **Receives both a structured schedule and warm, caring spoken audio advice** in their native language explaining:
   - Direct, reassuring answer to their spoken doubt.
   - Exact timings (Morning/Noon/Night) and meal guidelines (Before/After food).
   - Critical precautions and drug interaction warnings.

---

## 🏗️ 100% Pure Sarvam AI Stack

```
   📸 Prescription Photo (JPG/PNG/PDF)  ──>  Sarvam Vision 1.5 (Doc AI)  ──┐
                                                                              ├──>  Sarvam-105B Model  ──>  Bulbul v3 TTS  ──>  🔊 Spoken Voice
   🎙️ Spoken Voice Concern (Hindi/Hinglish)  ──>  Saaras v3 (STT)         ──┘     (Clinical Reasoning)      (Expressive Voice)         (MP3/WAV Audio)
```

| Component | Sarvam Model / API | Purpose |
| :--- | :--- | :--- |
| **Speech-to-Text** | `Saaras v3` (`saaras:v3`) | Transcribes noisy, colloquial Indian voice notes across regional languages and code-mixing. |
| **Document Vision** | `Sarvam Vision 1.5` (`doc_ai.digitise`) | Digitizes and extracts handwriting, medication names, dosages, and doctor notes. |
| **Clinical Reasoning** | `Sarvam-105B` (`sarvam-105b-conversations`) | Correlates prescription with patient doubt, formulates dosage schedule and warnings. |
| **Text-to-Speech** | `Bulbul v3` (`bulbul:v3`, speaker `ritu`) | Synthesizes warm, clear Indian voice audio guidance so grandparents can listen without reading screens. |

---

## 🚀 Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/aushadh-didi.git
cd aushadh-didi
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Your API Key
Copy `.env.example` to `.env` and add your Sarvam API subscription key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
SARVAM_API_KEY=your_sarvam_api_key_here
```
*(Never commit `.env` to GitHub. It is protected in `.gitignore`.)*

---

## 💻 Running the App

### Option A: Interactive Web UI (Zero External Dependencies)
Launch the built-in web server:
```bash
python app.py
```
Open **`http://127.0.0.1:8000`** in your browser.

* Click **"✨ Load Sample Rx"** and **"✨ Load Sample Voice Query"** for an instant 1-click demo!
* Or upload your own prescription image and record/upload a voice note.
* Click **"👩‍⚕️ Consult Aushadh-Didi"** to view the clinical schedule and listen to the spoken audio response.

### Option B: Command Line (CLI Mode)
Run directly from the terminal with bundled sample fixtures:
```bash
python app.py --cli
```

---

## 📁 Repository Structure
```
├── app.py                 # Zero-dependency Web application & CLI runner
├── pipeline.py            # End-to-end Sarvam AI pipeline (Saaras, Vision, 105B, Bulbul)
├── main.py                # Minimal initial test script for Sarvam-105B
├── requirements.txt       # Python package dependencies
├── .env.example           # Environment template for SARVAM_API_KEY
├── .gitignore             # Git ignore configuration protecting secrets
└── samples/               # Demo-ready test fixtures
    ├── sample_prescription.png       # Sample doctor prescription (Diabetes + BP)
    ├── sample_patient_query.wav      # Sample Hinglish voice note
    └── output_aushadh_didi_response.wav  # Synthesized voice response audio
```

---

## 🛡️ Privacy & Safety
- **Environment Variables**: API keys are loaded strictly from the local environment and never hardcoded or printed.
- **Doctor First**: Aushadh-Didi serves as an explanatory patient companion and always advises consulting the treating physician for changes to prescription regimens.

---

## 📜 License
MIT License. Built for the **Sarvam AI Hackathon**.
