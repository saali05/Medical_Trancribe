import os
import json
from groq import Groq


# ── Transcribe using Groq Whisper API (free + fast) ──────────────────────────
def transcribe_audio(audio_path: str) -> list:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    with open(audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_path), audio_file.read()),
            model="whisper-large-v3",
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )

    segments = []
    for seg in transcription.segments:
        # Groq returns dicts, handle both dict and object
        if isinstance(seg, dict):
            segments.append({
                "start": round(seg["start"], 2),
                "end":   round(seg["end"], 2),
                "text":  seg["text"].strip()
            })
        else:
            segments.append({
                "start": round(seg.start, 2),
                "end":   round(seg.end, 2),
                "text":  seg.text.strip()
            })
    return segments


# ── Label speakers using heuristics ──────────────────────────────────────────
def label_speakers(segments: list) -> list:
    labeled = []
    for i, seg in enumerate(segments):
        text = seg["text"].strip()

        if i == 0:
            role = "Doctor"
        elif text.endswith("?"):
            role = "Patient"
        else:
            prev_role = labeled[-1]["role"] if labeled else "Doctor"
            prev_text = labeled[-1]["text"] if labeled else ""
            if len(prev_text.split()) < 10 and prev_role == "Patient":
                role = "Doctor"
            elif len(text.split()) > 15:
                role = "Doctor"
            else:
                role = "Patient" if prev_role == "Doctor" else "Doctor"

        labeled.append({**seg, "role": role})

    return labeled


# ── Extract medical fields using Groq LLaMA ──────────────────────────────────
def extract_medical_fields(labeled_segments: list) -> dict:
    conversation_text = "\n".join(
        f"[{seg['role']}]: {seg['text']}"
        for seg in labeled_segments
        if seg["text"].strip()
    )

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = f"""You are a medical scribe AI. Read the doctor-patient conversation below.
Extract ONLY the following fields. If a field is not mentioned, write "Not mentioned".
Return ONLY valid JSON with these exact keys, no explanation, no markdown:

{{
  "chief_complaint": "...",
  "present_illness": "...",
  "diagnosis": "...",
  "prescription": "...",
  "treatment_plan": "...",
  "follow_up": "...",
  "vitals": "...",
  "past_medical_history": "..."
}}

Conversation:
{conversation_text}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return {"error": "Could not parse response", "raw": raw}


# ── Main entry point ──────────────────────────────────────────────────────────
def process_audio(audio_path: str) -> dict:
    print(f"Processing: {audio_path}")
    segments = transcribe_audio(audio_path)
    print(f"Transcribed {len(segments)} segments")
    labeled  = label_speakers(segments)
    medical  = extract_medical_fields(labeled)
    print(f"Done: {medical}")
    return {
        "conversation":    labeled,
        "medical_summary": medical
    }