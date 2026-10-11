import os
import sys
import time
import json
import base64
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes

import pipeline

PORT = 8000
HOST = "127.0.0.1"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Aushadh-Didi (औषध-दीदी) | Powered by Sarvam AI</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Rozha+One&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #0284c7;
      --primary-dark: #0369a1;
      --primary-light: #e0f2fe;
      --accent: #10b981;
      --accent-light: #d1fae5;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
      --shadow-md: 0 4px 6px -1px rgba(0,0,0,0.08), 0 2px 4px -2px rgba(0,0,0,0.05);
      --shadow-lg: 0 10px 15px -3px rgba(0,0,0,0.08), 0 4px 6px -4px rgba(0,0,0,0.04);
      --radius: 16px;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      background: var(--bg);
      color: var(--text-main);
      line-height: 1.6;
      padding-bottom: 60px;
    }

    header {
      background: linear-gradient(135deg, #0369a1 0%, #0284c7 60%, #06b6d4 100%);
      color: white;
      padding: 40px 20px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }
    header::before {
      content: "";
      position: absolute;
      top: -50%;
      left: -20%;
      width: 140%;
      height: 200%;
      background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
      pointer-events: none;
    }

    .badge-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(255,255,255,0.18);
      backdrop-filter: blur(8px);
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 14px;
      border: 1px solid rgba(255,255,255,0.25);
    }
    h1 {
      font-size: 2.5rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      margin-bottom: 8px;
    }
    h1 span.indic {
      font-family: 'Rozha One', serif;
      color: #fed7aa;
      font-weight: 400;
      margin-left: 8px;
    }
    header p {
      font-size: 1.1rem;
      max-width: 680px;
      margin: 0 auto;
      opacity: 0.92;
    }

    .container {
      max-width: 1100px;
      margin: -25px auto 0;
      padding: 0 20px;
    }

    .grid-inputs {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin-bottom: 24px;
    }
    @media (max-width: 768px) {
      .grid-inputs { grid-template-columns: 1fr; }
    }

    .card {
      background: var(--card-bg);
      border-radius: var(--radius);
      padding: 24px;
      box-shadow: var(--shadow-md);
      border: 1px solid var(--border);
      transition: transform 0.2s, box-shadow 0.2s;
    }
    .card:hover {
      box-shadow: var(--shadow-lg);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
    }
    .card-title {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 1.15rem;
      font-weight: 700;
      color: var(--text-main);
    }
    .tech-tag {
      font-size: 0.75rem;
      font-weight: 700;
      padding: 3px 8px;
      border-radius: 6px;
      background: var(--primary-light);
      color: var(--primary-dark);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .drop-zone {
      border: 2px dashed #cbd5e1;
      border-radius: 12px;
      padding: 24px 16px;
      text-align: center;
      background: #f8fafc;
      cursor: pointer;
      transition: all 0.2s;
      position: relative;
    }
    .drop-zone:hover {
      border-color: var(--primary);
      background: #f0f9ff;
    }
    .drop-zone input[type="file"] {
      position: absolute;
      top: 0; left: 0; width: 100%; height: 100%;
      opacity: 0;
      cursor: pointer;
    }

    .sample-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      margin-top: 12px;
      padding: 6px 12px;
      font-size: 0.85rem;
      font-weight: 600;
      background: white;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      color: #334155;
      cursor: pointer;
      transition: all 0.15s;
    }
    .sample-btn:hover {
      background: #f1f5f9;
      border-color: #94a3b8;
    }

    .preview-box {
      margin-top: 14px;
      border-radius: 8px;
      overflow: hidden;
      display: none;
      border: 1px solid var(--border);
    }
    .preview-box img {
      width: 100%;
      max-height: 220px;
      object-fit: cover;
      display: block;
    }
    .preview-box audio {
      width: 100%;
      margin-top: 8px;
    }

    .action-container {
      text-align: center;
      margin: 10px 0 30px;
    }
    .cta-btn {
      background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
      color: white;
      border: none;
      padding: 16px 36px;
      border-radius: 9999px;
      font-size: 1.15rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 14px rgba(2, 132, 199, 0.35);
      transition: all 0.2s;
      display: inline-flex;
      align-items: center;
      gap: 10px;
    }
    .cta-btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 6px 20px rgba(2, 132, 199, 0.45);
    }
    .cta-btn:disabled {
      background: #94a3b8;
      cursor: not-allowed;
      transform: none;
      box-shadow: none;
    }

    #loading-spinner {
      display: none;
      margin: 20px auto;
      text-align: center;
      color: var(--primary-dark);
      font-weight: 600;
    }
    .spinner {
      border: 4px solid #f3f3f3;
      border-top: 4px solid var(--primary);
      border-radius: 50%;
      width: 36px;
      height: 36px;
      animation: spin 1s linear infinite;
      margin: 0 auto 10px;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    #results-area {
      display: none;
      animation: fadeIn 0.4s ease-out;
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(10px); }
      to { opacity: 1; transform: translateY(0); }
    }

    .response-card {
      background: var(--card-bg);
      border-radius: var(--radius);
      padding: 30px;
      box-shadow: var(--shadow-lg);
      border: 1px solid var(--border);
      margin-bottom: 24px;
    }
    .audio-player-banner {
      background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
      border: 1px solid #bbf7d0;
      border-radius: 12px;
      padding: 16px 20px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .audio-label {
      font-weight: 700;
      color: #166534;
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .transcript-box {
      background: #f8fafc;
      border-left: 4px solid var(--primary);
      padding: 14px 18px;
      border-radius: 0 8px 8px 0;
      margin-bottom: 20px;
      font-style: italic;
      color: #334155;
    }

    .guidance-content {
      font-size: 1.05rem;
      white-space: pre-wrap;
      line-height: 1.8;
      color: #1e293b;
    }

    .sarvam-stack-footer {
      text-align: center;
      margin-top: 40px;
      padding-top: 20px;
      border-top: 1px solid var(--border);
      font-size: 0.9rem;
      color: var(--text-muted);
    }
    .stack-badges {
      display: flex;
      justify-content: center;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 8px;
    }
    .stack-badge {
      background: #f1f5f9;
      padding: 4px 10px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 0.8rem;
      color: #475569;
    }
  </style>
</head>
<body>

  <header>
    <div class="badge-pill">🇮🇳 100% Native Indian Language Healthcare Copilot</div>
    <h1>Aushadh-Didi <span class="indic">औषध-दीदी</span></h1>
    <p>Voice-First Prescription & Medicine Safety Guard for Grandparents and Caregivers — Powered entirely by Sarvam AI</p>
  </header>

  <div class="container">
    <div class="grid-inputs">
      <!-- Prescription Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <span>📄</span> 1. Prescription / Medicine Box
          </div>
          <span class="tech-tag">Sarvam Vision</span>
        </div>
        <div class="drop-zone" id="img-drop">
          <input type="file" id="img-input" accept="image/*,application/pdf">
          <div style="font-size: 2rem; margin-bottom: 6px;">📷</div>
          <div style="font-weight: 600; color: #334155;">Upload handwritten Rx or medicine photo</div>
          <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">PNG, JPG, or PDF</div>
        </div>
        <button class="sample-btn" id="load-sample-img">✨ Load Sample Rx (Dr. Sharma - Diabetes & BP)</button>
        <div class="preview-box" id="img-preview-box">
          <img id="img-preview" src="" alt="Prescription preview">
        </div>
      </div>

      <!-- Spoken Question Card -->
      <div class="card">
        <div class="card-header">
          <div class="card-title">
            <span>🎙️</span> 2. Spoken Patient Concern
          </div>
          <span class="tech-tag">Saaras v3 STT</span>
        </div>
        <div class="drop-zone" id="audio-drop">
          <input type="file" id="audio-input" accept="audio/*">
          <div style="font-size: 2rem; margin-bottom: 6px;">🗣️</div>
          <div style="font-weight: 600; color: #334155;">Upload voice note (Hindi / Hinglish / Tamil)</div>
          <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">WAV, MP3, M4A, or AAC</div>
        </div>
        <button class="sample-btn" id="load-sample-audio">✨ Load Sample Voice Query ("Metformin subah khali pet?")</button>
        <div class="preview-box" id="audio-preview-box">
          <audio id="audio-preview" controls></audio>
        </div>
      </div>
    </div>

    <!-- Action Button -->
    <div class="action-container">
      <button class="cta-btn" id="submit-btn">
        <span>👩‍⚕️</span> Consult Aushadh-Didi (औषध दीदी से पूछें)
      </button>
    </div>

    <!-- Loading State -->
    <div id="loading-spinner">
      <div class="spinner"></div>
      <p id="loading-msg">Consulting Sarvam AI (Transcribing with Saaras v3 & Analyzing with Sarvam-105B)...</p>
    </div>

    <!-- Output Area -->
    <div id="results-area">
      <div class="response-card">
        <!-- Audio Guidance Player -->
        <div class="audio-player-banner">
          <div class="audio-label">
            <span>🔊</span> Aushadh-Didi Spoken Voice Advice (Bulbul v3)
          </div>
          <audio id="response-audio" controls autoplay style="flex-grow: 1; max-width: 480px;"></audio>
        </div>

        <!-- Transcribed Question -->
        <div style="margin-bottom: 12px; font-weight: 700; color: #475569; display: flex; align-items: center; gap: 8px;">
          <span>👂</span> Spoken Question Transcribed by Saaras v3:
        </div>
        <div class="transcript-box" id="transcript-display"></div>

        <!-- Full Guidance -->
        <div style="margin: 24px 0 12px; font-weight: 700; color: #0284c7; font-size: 1.2rem; display: flex; align-items: center; gap: 8px;">
          <span>📋</span> Complete Medication Schedule & Safety Advice:
        </div>
        <div class="guidance-content" id="guidance-display"></div>
      </div>
    </div>

    <!-- Footer -->
    <div class="sarvam-stack-footer">
      Built for Sarvam AI Hackathon • 100% Sarvam Stack
      <div class="stack-badges">
        <span class="stack-badge">Saaras v3 (STT)</span>
        <span class="stack-badge">Sarvam Vision 1.5 (Doc AI)</span>
        <span class="stack-badge">Sarvam-105B (Indic Reasoning)</span>
        <span class="stack-badge">Bulbul v3 (Expressive TTS)</span>
      </div>
    </div>
  </div>

  <script>
    let selectedImageFile = null;
    let selectedAudioFile = null;
    let useSampleImage = false;
    let useSampleAudio = false;

    const imgInput = document.getElementById('img-input');
    const audioInput = document.getElementById('audio-input');
    const imgPreviewBox = document.getElementById('img-preview-box');
    const imgPreview = document.getElementById('img-preview');
    const audioPreviewBox = document.getElementById('audio-preview-box');
    const audioPreview = document.getElementById('audio-preview');

    imgInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        selectedImageFile = e.target.files[0];
        useSampleImage = false;
        imgPreview.src = URL.createObjectURL(selectedImageFile);
        imgPreviewBox.style.display = 'block';
      }
    });

    audioInput.addEventListener('change', (e) => {
      if (e.target.files.length) {
        selectedAudioFile = e.target.files[0];
        useSampleAudio = false;
        audioPreview.src = URL.createObjectURL(selectedAudioFile);
        audioPreviewBox.style.display = 'block';
      }
    });

    document.getElementById('load-sample-img').addEventListener('click', () => {
      useSampleImage = true;
      selectedImageFile = null;
      imgPreview.src = '/samples/sample_prescription.png';
      imgPreviewBox.style.display = 'block';
    });

    document.getElementById('load-sample-audio').addEventListener('click', () => {
      useSampleAudio = true;
      selectedAudioFile = null;
      audioPreview.src = '/samples/sample_patient_query.wav';
      audioPreviewBox.style.display = 'block';
    });

    document.getElementById('submit-btn').addEventListener('click', async () => {
      const btn = document.getElementById('submit-btn');
      const spinner = document.getElementById('loading-spinner');
      const resultsArea = document.getElementById('results-area');

      btn.disabled = true;
      spinner.style.display = 'block';
      resultsArea.style.display = 'none';

      const formData = new FormData();
      formData.append('use_sample_image', useSampleImage ? 'true' : 'false');
      formData.append('use_sample_audio', useSampleAudio ? 'true' : 'false');
      if (selectedImageFile) formData.append('image_file', selectedImageFile);
      if (selectedAudioFile) formData.append('audio_file', selectedAudioFile);

      try {
        const response = await fetch('/api/consult', {
          method: 'POST',
          body: formData
        });

        const data = await response.json();
        if (data.error) {
          alert('Error: ' + data.error);
          return;
        }

        document.getElementById('transcript-display').innerText = `"${data.patient_query}"`;
        document.getElementById('guidance-display').innerText = data.guidance_text;
        
        const audioEl = document.getElementById('response-audio');
        audioEl.src = 'data:audio/wav;base64,' + data.audio_base64;
        audioEl.play().catch(e => console.log('Autoplay deferred'));

        resultsArea.style.display = 'block';
        resultsArea.scrollIntoView({ behavior: 'smooth' });
      } catch (err) {
        alert('Request failed: ' + err.message);
      } finally {
        btn.disabled = false;
        spinner.style.display = 'none';
      }
    });
  </script>
</body>
</html>
"""


class AushadhDidiHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Clean logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {format % args}\n")

    def do_GET(self):
        url_parts = urllib.parse.urlparse(self.path)
        path = url_parts.path

        if path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))
            return

        if path.startswith("/samples/"):
            file_name = path[len("/samples/"):]
            file_path = Path("samples") / file_name
            if file_path.exists() and file_path.is_file():
                mime, _ = mimetypes.guess_type(str(file_path))
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def do_POST(self):
        if self.path == "/api/consult":
            try:
                content_type = self.headers.get("Content-Type", "")
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length)

                # Parse multipart form data
                boundary = content_type.split("boundary=")[-1].encode("utf-8")
                parts = body.split(b"--" + boundary)

                use_sample_image = True
                use_sample_audio = True
                image_data = None
                audio_data = None
                image_filename = "upload.jpg"
                audio_filename = "upload.wav"

                for part in parts:
                    if b'name="use_sample_image"' in part:
                        val = part.split(b"\r\n\r\n")[1].split(b"\r\n")[0].decode("utf-8").strip()
                        use_sample_image = (val.lower() == "true")
                    elif b'name="use_sample_audio"' in part:
                        val = part.split(b"\r\n\r\n")[1].split(b"\r\n")[0].decode("utf-8").strip()
                        use_sample_audio = (val.lower() == "true")
                    elif b'name="image_file"' in part:
                        headers_and_body = part.split(b"\r\n\r\n", 1)
                        if len(headers_and_body) == 2:
                            header_str = headers_and_body[0].decode("utf-8", errors="ignore")
                            if 'filename="' in header_str:
                                image_filename = header_str.split('filename="')[1].split('"')[0].strip()
                            data = headers_and_body[1].rsplit(b"\r\n", 1)[0]
                            if len(data) > 0:
                                image_data = data
                                use_sample_image = False
                    elif b'name="audio_file"' in part:
                        headers_and_body = part.split(b"\r\n\r\n", 1)
                        if len(headers_and_body) == 2:
                            header_str = headers_and_body[0].decode("utf-8", errors="ignore")
                            if 'filename="' in header_str:
                                audio_filename = header_str.split('filename="')[1].split('"')[0].strip()
                            data = headers_and_body[1].rsplit(b"\r\n", 1)[0]
                            if len(data) > 0:
                                audio_data = data
                                use_sample_audio = False

                uploads_dir = Path("uploads")
                uploads_dir.mkdir(exist_ok=True)

                # Determine files to process
                if use_sample_image or not image_data:
                    target_image = "samples/sample_prescription.png"
                else:
                    ext = Path(image_filename).suffix.lower() if image_filename else ".jpg"
                    if ext not in (".jpg", ".jpeg", ".png", ".pdf"):
                        ext = ".jpg"
                    target_image = str(uploads_dir / f"user_prescription_{int(time.time())}{ext}")
                    Path(target_image).write_bytes(image_data)

                if use_sample_audio or not audio_data:
                    target_audio = "samples/sample_patient_query.wav"
                else:
                    ext = Path(audio_filename).suffix.lower() if audio_filename else ".wav"
                    if ext not in (".wav", ".mp3", ".m4a", ".aac", ".ogg", ".webm"):
                        ext = ".wav"
                    target_audio = str(uploads_dir / f"user_audio_{int(time.time())}{ext}")
                    Path(target_audio).write_bytes(audio_data)

                # Run Sarvam Pipeline
                result = pipeline.run_full_pipeline(
                    audio_path=target_audio,
                    image_path=target_image
                )

                # Return JSON response
                response_payload = {
                    "patient_query": result["patient_query"],
                    "detected_language": result["detected_language"],
                    "prescription_text": result["prescription_text"],
                    "guidance_text": result["guidance_text"],
                    "audio_base64": result["audio_base64"]
                }

                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))

            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def run_cli_mode():
    print("\n=======================================================")
    print("👩‍⚕️ Aushadh-Didi (औषध दीदी) — CLI Mode")
    print("=======================================================")
    audio_path = "samples/sample_patient_query.wav"
    image_path = "samples/sample_prescription.png"

    print(f"Loading Prescription: {image_path}")
    print(f"Loading Audio Query : {audio_path}")

    res = pipeline.run_full_pipeline(audio_path=audio_path, image_path=image_path)
    print("\n[Patient Doubt Transcribed]")
    print(f"\"{res['patient_query']}\"")
    print("\n[Aushadh-Didi Clinical Guidance]")
    print(res["guidance_text"])
    out_file = Path("samples/output_aushadh_didi_response.wav")
    out_file.write_bytes(res["audio_bytes"])
    print(f"\n[Spoken Audio Response Saved]")
    print(f"-> {out_file.resolve()}\n")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_cli_mode()
    else:
        server = HTTPServer((HOST, PORT), AushadhDidiHandler)
        print(f"\n✨ Aushadh-Didi Web App running at http://{HOST}:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            server.server_close()
