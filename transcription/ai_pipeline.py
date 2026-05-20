# transcription/ai_pipeline.py

import os
import json
from groq import Groq


def transcribe_audio(audio_path: str) -> list:
    """Transcribe audio using Groq Whisper API"""
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


def process_nlp(segments: list) -> list:
    """Label speakers using heuristics"""
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


def structure_clinical_document(labeled_segments: list) -> dict:
    """Extract medical fields using Groq LLaMA"""
    conversation_text = "\n".join(
        f"[{seg['role']}]: {seg['text']}"
        for seg in labeled_segments
        if seg["text"].strip()
    )

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    prompt = f"""You are an expert medical scribe AI. Carefully read this doctor-patient conversation.

Your job is to extract medical information even if it is implied or partially mentioned.
- If the doctor mentions a medicine name → put it in prescription
- If the doctor says "come back in X days" → put it in follow_up  
- If patient mentions pain/symptom duration → put it in present_illness
- If patient mentions family history → put it in past_medical_history
- Only write "Not mentioned" if truly absent

Return ONLY this JSON, no markdown, no explanation:

{{
  "chief_complaint": "main symptom the patient came for",
  "present_illness": "detailed description of current symptoms, duration, severity",
  "diagnosis": "doctor's diagnosis or suspected condition",
  "prescription": "medicines prescribed with dosage if mentioned",
  "treatment_plan": "treatment approach recommended by doctor",
  "follow_up": "when to return or next steps",
  "vitals": "blood pressure, temperature, pulse, weight if mentioned",
  "past_medical_history": "previous conditions, surgeries, family history"
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