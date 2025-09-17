import pyttsx3
import sounddevice as sd
import soundfile as sf
import whisper
import language_tool_python
import parselmouth
import numpy as np
import os
import openai
from openai import OpenAI
import gc
from dotenv import load_dotenv

load_dotenv()

#openai.api_key = "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" 
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = OPENAI_API_KEY)
# ------------------ API INTEGRATION (Type 1, simple prompt) ------------------ #
def judge_answer(question, answer):
    prompt = (
        f"Question: {question}\n"
        f"Answer: {answer}\n\n"
        "Evaluate the answer based on:\n"
        "- Relevance to the question\n"
        "- Clarity and grammar\n"
        "- Professional tone\n\n"
        "Return a JSON with:\n"
        "{score: (1-10), comment: 'your feedback'}"
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()


# ------------------ API INTEGRATION (Call Center Prompt Version) ------------------ #
def judge_answer_2(question, answer, scores=None):
    if not answer.strip():
        return """{
    "score": 0,
    "category_scores": {
      "relevance": 0,
      "grammar_lexis": 0,
      "communication_skills": 0,
      "fluency_pronunciation": 0,
      "customer_service_fit": 0
    },
    "comment": "The transcript was empty or unintelligible. Please ensure the response is clearly audible."
}"""

    scores_text = ""
    if scores:
        scores_text = "\nSystem Scores (for reference):\n" + "\n".join(f"- {k.replace('_',' ').title()}: {v}" for k, v in scores.items()) + "\n"

    prompt = (
        f"You are a **strict hiring evaluator** for a call center or BPO company. You're assessing an applicant's **spoken response** during a voice-based interview.\n\n"
        f"Question: {question}\n"
        f"Candidate's Answer: {answer}\n"
        f"{scores_text}\n"
        "Rate the answer using the following 5 criteria. Score **1 to 10**, but most poor answers should fall in the **1–4 range**:\n"
        "1. **Relevance** – Does the answer directly and clearly address the question? Off-topic or vague answers should score 3 or lower.\n"
        "2. **Grammar and Lexis** – Is grammar correct and vocabulary appropriate for customer interaction? Frequent grammar mistakes = score ≤ 3.\n"
        "3. **Communication Skills** – Does the speaker express ideas clearly, logically, and confidently? Is the message well-structured? = score ≤ 4.\n"
        "4. **Fluency and Pronunciation** –  Is the speech smooth and easy to follow? Penalize heavy use of filler words (e.g., 'um', 'kanang', 'uhm', 'ah', 'you know') and unnatural pauses.\n"
        "5. **Customer Service Fit** – Does the answer show empathy, patience, politeness, and the tone expected of someone speaking with customers over the phone? If absent, score ≤ 4.\n\n"
        "🛑 Be very strict. Do **not** be generous. If the response is disorganized, poorly spoken, or contains fillers, **score low**. Use 1s and 2s if necessary.\n\n"
        "Based on the CEFR English level reflected in the answer, recommend the most appropriate account type:\n"
        "- If the response is around B1 or B2 level, recommend accounts such as **JS, ONO, or BF**.\n"
        "- If the response is at C1 or C2 level, recommend **Transpo, RM, or Sales** accounts.\n\n"
        "Return a JSON object strictly in this format:\n"
        "{\n"
        "  \"score\": (1–10 overall),\n"
        "  \"category_scores\": {\n"
        "    \"relevance\": x,\n"
        "    \"grammar_lexis\": x,\n"
        "    \"communication_skills\": x,\n"
        "    \"fluency_pronunciation\": x,\n"
        "    \"customer_service_fit\": x\n"
        "  },\n"
        "  \"comment\": \"Give actionable, constructive feedback. Mention filler words, disorganization, bad tone, grammar errors, or anything weak about the customer service handling. Also, recommend the most suitable account based on the speaker's CEFR English level.\"\n"
        "}"
    )


    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()




# ------------------ 1. Speak the Question (OBSOLETE)------------------ #  
# def speak(text):
#     engine = pyttsx3.init()
#     voices = engine.getProperty('voices')
#
#     # Select a female voice
#     for voice in voices:
#         if "female" in voice.name.lower() or "zira" in voice.name.lower():
#             engine.setProperty('voice', voice.id)
#             break
#
#     engine.say(text)
#     engine.runAndWait()

# ------------------ 2. Record Audio ------------------ #
def record_audio(file_name, duration=10):
    fs = 44100
    print(f"🎙️ Recording for {duration} seconds...")
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait()
    sf.write(file_name, audio, fs)
    print("✅ Recording saved.\n")

# ------------------ 3.1. Transcribe Audio (OBSOLETE) ------------------ #
model = whisper.load_model("medium")

def transcribe_audio(file_path):
    result = model.transcribe(file_path, word_timestamps=True, language="en")
    return result["text"]

# ------------------ 3.2. Transcribe Audio (DETECT FILLERS AND STOP WORDS) (OBSOLETE) ------------------ #
#from faster_whisper import WhisperModel

#fw_model = WhisperModel("medium", compute_type="int8")  # or "float32"

# ------------------ Combined Transcriber with Filler Detection (OBSOLETE)------------------ #
def transcribe_audio_deepgram_api(audio_path, min_pause_duration=0.3):
    #from faster_whisper import WhisperModel

    segments, info = fw_model.transcribe(audio_path, beam_size=5, word_timestamps=True, language="en")

    words = []
    full_text = ""
    for segment in segments:
        for word in segment.words:
            words.append({
                "word": word.word,
                "start": word.start,
                "end": word.end,
                "probability": word.probability
            })
            full_text += word.word + " "

    sound = parselmouth.Sound(audio_path)
    intensity = sound.to_intensity()
    total_duration = sound.duration

    pauses = []
    current_pause_start = None
    for t in range(0, int(total_duration * 100)):
        time = t / 100.0
        db = intensity.get_value(time)

        if db is None or db < 40:  # silence threshold
            if current_pause_start is None:
                current_pause_start = time
        else:
            if current_pause_start is not None:
                pause_duration = time - current_pause_start
                if pause_duration >= min_pause_duration:
                    pauses.append((current_pause_start, time))
                current_pause_start = None

    # filler words (english + bisaya)
    filler_words = {
        "uh", "um", "umm", "uhh", "like", "well", "so", "you", "i", "just", "yeah", "hmm", "er", "ah", "okay",
        "kanang", "ano", "eh", "uhm", "bali", "parang", "diba"
    }

    filler_flags = []

    for word in words:
        word_text = word["word"].lower().strip()
        duration = word["end"] - word["start"]

        if word_text in filler_words:
            filler_flags.append({
                "type": "explicit_filler",
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "probability": float(word["probability"])
            })

        if duration > 1.2 and word_text in filler_words:
            filler_flags.append({
                "type": "stretched_filler",
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "duration": duration
            })

        if word["probability"] < 0.4:
            filler_flags.append({
                "type": "low_confidence_possible_filler",
                "word": word["word"],
                "start": word["start"],
                "end": word["end"],
                "probability": float(word["probability"])
            })

    return {
        "transcript": full_text.strip(),
        "words": words,
        "likely_fillers": filler_flags,
        "filler_count": len(filler_flags),
        "filler_words": list({f['word'].lower().strip() for f in filler_flags}),
        "pauses": pauses
    }

# ------------------ 3.3. Transcribe Audio (USING DEEPGRAM API) ------------------ #
import asyncio
from deepgram import Deepgram

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")  # Load from .env

def transcribe_audio_deepgram(audio_path):
    async def transcribe_async():
        dg_client = Deepgram(DEEPGRAM_API_KEY)
        mimetype = "audio/wav"
        if audio_path.endswith(".mp3"):
            mimetype = "audio/mpeg"
        elif audio_path.endswith(".flac"):
            mimetype = "audio/flac"
        with open(audio_path, 'rb') as audio_file:
            source = {
                'buffer': audio_file,
                'mimetype': mimetype
            }
            response = await dg_client.transcription.prerecorded(
                source,
                {
                    'punctuate': False,
                    'language': 'en',
                    'utterances': True,
                    'filler_words': True,
                    'diarize': False,
                    'model': 'nova'
                }
            )
        full_transcript = response['results']['channels'][0]['alternatives'][0]['transcript']
        words = response['results']['channels'][0]['alternatives'][0].get('words', [])
        fillers = [w for w in words if w.get("type") == "filler"]
        return {
            "transcript": full_transcript,
            "fillers": fillers,
            "words": words
        }
    return asyncio.run(transcribe_async())


# ------------------ 3.3b. Transcribe Audio (USING OPENAI WHISPER API) ------------------ #
import requests

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Load from .env

def transcribe_audio_whisper(audio_path):
    """
    Transcribe audio using OpenAI Whisper API.
    Returns a dict with 'transcript' and 'words' (if available).
    """
    api_url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    with open(audio_path, "rb") as audio_file:
        files = {
            "file": audio_file
        }
        data = {
            "model": "whisper-1",
            "response_format": "text"
            # You can add "language": "en" or "tl" if you want to force a language, but for code-switching, leave it out.
        }
        response = requests.post(api_url, headers=headers, files=files, data=data)
        response.raise_for_status()
        transcript = response.text.strip()
    return {
        "transcript": transcript,
        "words": None  # Whisper API does not return word-level timing in text mode
    }

    
# ------------------ 4. Grammar Check ------------------ #
tool = language_tool_python.LanguageTool('en-US')

def check_grammar(text):
    matches = tool.check(text)
    return matches

# ------------------ 5. Analyze Speech ------------------ #
def analyze_audio(file_path):
    snd = parselmouth.Sound(file_path)
    pitch = snd.to_pitch()
    duration = snd.duration
    pitch_values = pitch.selected_array['frequency']
    pitch_values = pitch_values[pitch_values != 0]
    avg_pitch = np.mean(pitch_values) if len(pitch_values) else 0
    words_estimate = duration / 0.4
    words_per_min = (words_estimate / duration) * 60
    return {
        "duration": round(duration, 2),
        "avg_pitch_hz": round(avg_pitch, 2),
        "estimated_wpm": round(words_per_min, 2)
    }

# ------------------ 6. Evaluate Answer ------------------ #
def evaluate_answer(transcript, audio_metrics, expected_keywords):
    # Temporarily let GPT handle all scoring and feedback
    return {
        "transcript": transcript,
        "audio_metrics": audio_metrics,
        # The following fields will be filled by GPT, not by internal logic
        # "fluency_score": None,
        # "grammar_issues": None,
        # "relevance_score": None,
        # "speech_score": None,
        # "total_score": None
    }

# ------------------ 7. API Callable Evaluation Function ------------------ #
def run_full_evaluation(question, keywords, audio_file, use_deepgram=True):
    transcript_data = transcribe_audio_deepgram(audio_file)
    transcript = transcript_data["transcript"]
    audio_metrics = analyze_audio(audio_file)
    # Let GPT handle all scoring and feedback
    try:
        gpt_judgment = judge_answer_2(question, transcript, audio_metrics)
        import json as _json
        gpt_result = _json.loads(gpt_judgment) if gpt_judgment.strip().startswith('{') else {}
    except Exception as e:
        gpt_judgment = f"GPT evaluation failed: {str(e)}"
        gpt_result = {}
    gc.collect()
    return {
        "transcript": transcript,
        "transcript_data": transcript_data,
        "audio_metrics": audio_metrics,
        "evaluation": gpt_result,
        "gpt_judgment": gpt_judgment
    }
