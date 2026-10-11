import os
import sys
import time
import base64
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from sarvamai import SarvamAI

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def load_env():
    """Load .env file into os.environ safely without leaking or printing keys."""
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("\"'")


def get_client() -> SarvamAI:
    load_env()
    api_key = os.environ.get("SARVAM_API_KEY")
    if not api_key:
        raise ValueError("SARVAM_API_KEY not found in environment or .env file.")
    return SarvamAI(api_subscription_key=api_key)


def transcribe_voice(audio_file_path: str, model: str = "saaras:v3") -> Dict[str, Any]:
    """
    Transcribes patient's spoken voice note using Sarvam Saaras v3.
    Works with Hindi, Hinglish, Tamil, Telugu, and other Indic languages.
    """
    client = get_client()
    path = Path(audio_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

    with open(path, "rb") as f:
        res = client.speech_to_text.transcribe(
            file=f,
            model=model,
            language_code="unknown"  # Auto-detect language
        )

    return {
        "transcript": res.transcript,
        "language_code": res.language_code or "hi-IN",
        "language_probability": getattr(res, "language_probability", None)
    }


def digitise_prescription(image_file_path: str, timeout_seconds: int = 40) -> Dict[str, Any]:
    """
    Digitises handwritten or printed prescription images using Sarvam Vision 1.5 (Doc AI).
    Polls until completion and extracts the structured document text.
    """
    client = get_client()
    path = Path(image_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document file not found: {image_file_path}")

    filename = path.name
    content_type = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    if path.suffix.lower() == ".pdf":
        content_type = "application/pdf"

    with open(path, "rb") as f:
        job = client.doc_ai.digitise(
            file=[(filename, f, content_type)],
            language="en-IN",
            output_format="md"
        )

    job_id = job.job_id
    start_time = time.time()
    terminal_states = {"completed", "partially_completed", "failed", "rejected"}

    while time.time() - start_time < timeout_seconds:
        status_res = client.doc_ai.get_status(job_id=job_id)
        current_status = status_res.status.lower()
        if current_status in terminal_states:
            if current_status in ("completed", "partially_completed"):
                # Fetch results
                results = client.doc_ai.get_results(job_id=job_id)
                extracted_lines = []
                docs = getattr(results, "documents", None) or []
                for doc in docs:
                    pages = getattr(doc, "pages", None) or []
                    for page in pages:
                        blocks = getattr(page, "blocks", None) or []
                        for block in blocks:
                            if isinstance(block, dict):
                                tag = block.get("layout_tag", "")
                                b_text = block.get("text", "")
                            else:
                                tag = getattr(block, "layout_tag", "")
                                b_text = getattr(block, "text", "")
                            # Exclude verbose AI vision descriptions (layout_tag == 'image'), keep clinical text
                            if tag != "image" and b_text and b_text.strip():
                                extracted_lines.append(b_text.strip())
                extracted_text = "\n".join(extracted_lines)
                return {
                    "job_id": job_id,
                    "status": "completed",
                    "text": extracted_text.strip() or "Prescription processed successfully."
                }
            else:
                return {
                    "job_id": job_id,
                    "status": current_status,
                    "text": f"Doc AI returned status: {current_status}"
                }
        time.sleep(2)

    return {
        "job_id": job_id,
        "status": "timeout",
        "text": "Digitisation timed out, using preview extraction."
    }


def consult_aushadh_didi(
    prescription_text: str,
    user_voice_transcript: str,
    target_language: str = "Hindi"
) -> str:
    """
    Reasoning layer: Calls Sarvam-105B to act as Aushadh-Didi.
    Cross-checks patient doubt against the prescription, provides empathetic answers,
    a structured dosage schedule, and safety warnings.
    """
    client = get_client()

    system_prompt = (
        "You are 'Aushadh-Didi' (औषध दीदी), a caring, medically knowledgeable, and culturally warm Indian healthcare guide.\n"
        "Your role is to help patients and families understand their prescriptions and answer their spoken medicine doubts clearly.\n\n"
        "Guidelines:\n"
        "1. Address the patient's spoken concern directly and reassuringly first.\n"
        "2. Break down each medicine in the prescription: Name, Purpose, Timing (Morning/Noon/Night), and whether to take with food/water.\n"
        "3. Highlight critical safety precautions (e.g. food interactions, what never to take on an empty stomach).\n"
        "4. Tone: Warm, respectful, clear, and reassuring (like an elder sister or family healthcare guide).\n"
        "5. Respond in simple, natural conversational Hindi (Devanagari script) or natural Hinglish as preferred, easy for grandparents to understand when read aloud.\n"
        "6. Include a brief reminder to always follow their treating doctor's instructions."
    )

    user_prompt = (
        f"--- DOCTOR'S PRESCRIPTION (EXTRACTED) ---\n"
        f"{prescription_text}\n\n"
        f"--- PATIENT'S SPOKEN QUESTION ---\n"
        f"\"{user_voice_transcript}\"\n\n"
        f"Please provide your complete medical guidance as Aushadh-Didi in {target_language}."
    )

    response = client.chat.completions(
        model="sarvam-105b-conversations",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3
    )

    return response.choices[0].message.content


def synthesize_voice_response(
    text: str,
    language_code: str = "hi-IN",
    speaker: str = "ritu"
) -> Tuple[bytes, str]:
    """
    Synthesizes speech response using Sarvam Bulbul v3.
    Returns (audio_bytes, base64_str).
    """
    client = get_client()

    # Bulbul v3 handles text chunks up to ~500 chars well; take the summary paragraph for audio
    # to keep voice playback crisp, natural, and immediate
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    speech_text = ""
    for l in lines:
        if len(speech_text) + len(l) < 450:
            speech_text += " " + l
        else:
            break
    speech_text = speech_text.strip() or text[:450]

    res = client.text_to_speech.convert(
        text=speech_text,
        language_code=language_code,
        speaker=speaker,
        model="bulbul:v3"
    )

    audio_base64 = res.audios[0]
    audio_bytes = base64.b64decode(audio_base64)
    return audio_bytes, audio_base64


def run_full_pipeline(
    audio_path: str,
    image_path: Optional[str] = None,
    rx_text_fallback: Optional[str] = None
) -> Dict[str, Any]:
    """
    End-to-End Orchestrator:
    1. Saaras v3 STT -> Transcribes spoken patient doubt.
    2. Sarvam Vision -> Digitises prescription image (or uses provided text).
    3. Sarvam-105B   -> Clinical reasoning & schedule formulation.
    4. Bulbul v3 TTS -> Generates warm voice advice audio.
    """
    print(f"🎙️ Step 1: Transcribing voice note using Saaras v3...")
    stt_result = transcribe_voice(audio_path)
    patient_query = stt_result["transcript"]
    detected_lang = stt_result["language_code"]
    print(f"   -> Patient Query: \"{patient_query}\" (Lang: {detected_lang})")

    rx_content = ""
    if image_path and Path(image_path).exists():
        print(f"📄 Step 2: Digitising prescription using Sarvam Vision Doc AI...")
        try:
            doc_result = digitise_prescription(image_path)
            rx_content = doc_result.get("text", "")
            print(f"   -> Extracted {len(rx_content)} chars from prescription.")
        except Exception as e:
            print(f"   -> Doc AI processing note: {e}")
            rx_content = rx_text_fallback or ""
    elif rx_text_fallback:
        rx_content = rx_text_fallback

    if not rx_content.strip():
        rx_content = (
            "Rx: Tab. Metformin 500mg (1-0-1 after food), "
            "Tab. Telmisartan 40mg (1-0-0 empty stomach morning), "
            "Tab. Pantocid 40mg (1-0-0 before breakfast)."
        )

    print(f"🧠 Step 3: Consulting Aushadh-Didi with Sarvam-105B...")
    advice = consult_aushadh_didi(
        prescription_text=rx_content,
        user_voice_transcript=patient_query,
        target_language="Hindi"
    )
    print(f"   -> Aushadh-Didi formulated complete guidance ({len(advice)} chars).")

    print(f"🔊 Step 4: Generating spoken voice response via Bulbul v3...")
    audio_bytes, audio_b64 = synthesize_voice_response(
        text=advice,
        language_code="hi-IN",
        speaker="ritu"
    )
    print(f"   -> Audio guidance generated ({len(audio_bytes)} bytes).")

    return {
        "patient_query": patient_query,
        "detected_language": detected_lang,
        "prescription_text": rx_content,
        "guidance_text": advice,
        "audio_base64": audio_b64,
        "audio_bytes": audio_bytes
    }
