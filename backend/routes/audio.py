from flask import Blueprint, jsonify, request, send_from_directory
import os
import subprocess
import uuid
from datetime import datetime
from utils.file_ops import save_audio_file, save_temp_evaluation, load_temp_evaluation
from utils.evaluation import run_evaluation
from utils.session import mark_question_answered
from utils.tts import speak_async

audio_bp = Blueprint('audio', __name__)

@audio_bp.route("/evaluate", methods=["POST", "OPTIONS"])
def evaluate():
    """Evaluate audio response for a question"""
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"})
    
    question = request.form.get("question")  # Get question text from form data
    keywords = request.form.getlist("keywords")  # Get expected keywords list
    audio = request.files.get("audio")  # Get uploaded audio file
    session_id = request.form.get("session_id")  # Get session ID from request
    question_index = int(request.form.get("question_index", 0))  # Get question index

    if not question or not keywords or not audio:  # Validate required fields
        return jsonify({"success": False, "message": "Missing question, keywords, or audio file."}), 400

    # Use unique file names to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    audio_webm_path = f"uploaded_answer_{unique_id}.webm"  # Temporary path for uploaded audio
    audio_wav_path = f"uploaded_answer_{unique_id}.wav"  # Temporary path for converted audio
    
    audio.save(audio_webm_path)  # Save uploaded audio to disk

    # Convert webm/ogg to wav using ffmpeg
    try:
        subprocess.run([  # Run ffmpeg command to convert audio format
            "ffmpeg", "-y", "-i", audio_webm_path, audio_wav_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:  # Handle conversion errors
        return jsonify({"success": False, "message": f"Audio conversion failed: {str(e)}"}), 500

    # Run evaluation
    result = run_evaluation(question, keywords, audio_wav_path)  # Process audio and get evaluation results
    
    # Get applicant info for folder organization
    applicant_info = None
    if session_id:  # Check if session ID exists
        from utils.file_ops import load_temp_applicant
        applicant_info = load_temp_applicant(session_id)  # Load applicant data
    
    # Save audio file to organized location
    audio_path = None
    if applicant_info:  # Check if applicant info exists
        audio_path = save_audio_file(audio_wav_path, applicant_info, session_id, question_index)  # Save organized audio file
    
    # Clean up temporary files AFTER evaluation is complete
    try:
        if os.path.exists(audio_webm_path):
            os.remove(audio_webm_path)  # Remove temporary webm file
        if os.path.exists(audio_wav_path):
            os.remove(audio_wav_path)  # Remove temporary wav file
    except Exception as cleanup_error:
        print(f"Cleanup error: {cleanup_error}")  # Log cleanup errors but don't fail
        pass
    
    # Add question and keywords to result
    result["question"] = question  # Include the question text
    result["keywords"] = keywords  # Include the expected keywords
    
    # Add audio path to result
    result["audio_path"] = audio_path  # Include audio file path in result
    
    # Save evaluation result
    if session_id:  # Check if session ID exists
        # Load existing temp evaluations for this session
        temp_evaluations = load_temp_evaluation(session_id)
        if not temp_evaluations:
            temp_evaluations = {
                "speech_eval": [],
                "listening_test": [],
                "written_test": [],
                "typing_test": []
            }
        
        # Add speech evaluation result to speech_eval section
        temp_evaluations["speech_eval"].append(result)
        
        # Save back to temporary evaluations
        if not save_temp_evaluation(temp_evaluations, session_id):
            print(f"Warning: Failed to save speech evaluation for session {session_id}")  # Log warning but don't fail request
    
    return jsonify(result)  # Return evaluation results

@audio_bp.route("/evaluate-listening-test", methods=["POST", "OPTIONS"])
def evaluate_listening_test():
    """Evaluate audio response for a listening test question"""
    # Handle preflight OPTIONS request
    if request.method == "OPTIONS":
        return jsonify({"message": "OK"})
    
    question_text = request.form.get("question_text")  # Get the phrase text from form data
    audio = request.files.get("audio")  # Get uploaded audio file
    session_id = request.form.get("session_id")  # Get session ID from request
    question_index = int(request.form.get("question_index", 0))  # Get question index

    if not question_text or not audio:  # Validate required fields
        return jsonify({"success": False, "message": "Missing question text or audio file."}), 400

    # Use unique file names to avoid conflicts
    unique_id = str(uuid.uuid4())[:8]
    audio_webm_path = f"uploaded_listening_answer_{unique_id}.webm"  # Temporary path for uploaded audio
    audio_wav_path = f"uploaded_listening_answer_{unique_id}.wav"  # Temporary path for converted audio
    
    audio.save(audio_webm_path)  # Save uploaded audio to disk
    print(f"Saved webm file: {audio_webm_path}, exists: {os.path.exists(audio_webm_path)}")

    # Convert webm/ogg to wav using ffmpeg
    try:
        subprocess.run([  # Run ffmpeg command to convert audio format
            "ffmpeg", "-y", "-i", audio_webm_path, audio_wav_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Converted to wav file: {audio_wav_path}, exists: {os.path.exists(audio_wav_path)}")
    except Exception as e:  # Handle conversion errors
        return jsonify({"success": False, "message": f"Audio conversion failed: {str(e)}"}), 500

    # Get applicant info for folder organization
    applicant_info = None
    if session_id:  # Check if session ID exists
        from utils.file_ops import load_temp_applicant
        applicant_info = load_temp_applicant(session_id)  # Load applicant data
    
    # Transcribe the audio using the existing transcription function BEFORE moving the file
    try:
        # Ensure the file exists before transcription
        if not os.path.exists(audio_wav_path):
            print(f"Audio file not found: {audio_wav_path}")
            transcript = "Transcription failed - file not found"
        else:
            print(f"Transcribing file: {audio_wav_path}")
            from test_eval import transcribe_audio_deepgram #old
            from test_eval import transcribe_audio_whisper #new
            #transcription_result = transcribe_audio_deepgram(audio_wav_path)  # Transcribe audio
            transcription_result = transcribe_audio_deepgram(audio_wav_path)  # Transcribe audio
            transcript = transcription_result.get("transcript", "").strip()  # Get transcript text
            print(f"Transcription successful: {transcript}")
    except Exception as e:  # Handle transcription errors
        transcript = "Transcription failed"  # Set fallback transcript
        print(f"Transcription error: {e}")  # Log error
    
    # Save audio file to organized location AFTER transcription
    audio_path = None
    if applicant_info:  # Check if applicant info exists
        print(f"Before save_audio_file: {audio_wav_path} exists: {os.path.exists(audio_wav_path)}")
        audio_path = save_audio_file(audio_wav_path, applicant_info, session_id, question_index, "listening_test")  # Save organized audio file
        print(f"After save_audio_file: {audio_wav_path} exists: {os.path.exists(audio_wav_path)}")
        print(f"Organized audio path: {audio_path}")
    
    # Clean up temporary files AFTER transcription is complete
    try:
        if os.path.exists(audio_webm_path):
            os.remove(audio_webm_path)  # Remove temporary webm file
        if os.path.exists(audio_wav_path):
            os.remove(audio_wav_path)  # Remove temporary wav file
    except Exception as cleanup_error:
        print(f"Cleanup error: {cleanup_error}")  # Log cleanup errors but don't fail
        pass
    
    # Compare transcript with question text (case-insensitive, ignoring punctuation)
    import re
    from difflib import SequenceMatcher
    question_clean = re.sub(r'[^\w\s]', '', question_text.lower().strip())  # Clean question text
    transcript_clean = re.sub(r'[^\w\s]', '', transcript.lower().strip())  # Clean transcript text
    
    # Calculate similarity ratio (0–1)
    similarity_ratio = SequenceMatcher(None, question_clean.split(), transcript_clean.split()).ratio()

    accuracy_percentage = round(similarity_ratio * 100, 1)

    # Flexible correctness threshold (e.g. 90%)
    is_correct = accuracy_percentage >= 90

    '''
    # Calculate accuracy percentage (OBSOLETE)
    if question_clean:
        # Split into words and compare
        question_words = question_clean.split()
        transcript_words = transcript_clean.split()
        
        if question_words:
            correct_words = 0
            for i, word in enumerate(question_words):
                if i < len(transcript_words) and word == transcript_words[i]:
                    correct_words += 1
            
            accuracy_percentage = (correct_words / len(question_words)) * 100
        else:
            accuracy_percentage = 0
    else:
        accuracy_percentage = 0
    '''
    
    # Create result object
    result = {
        "question_text": question_text,
        "transcript": transcript,
        "is_correct": is_correct,
        "accuracy_percentage": round(accuracy_percentage, 1),
        "audio_path": audio_path,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save evaluation result to listening test section
    if session_id:  # Check if session ID exists
        # Load existing temp evaluations for this session
        temp_evaluations = load_temp_evaluation(session_id)
        if not temp_evaluations:
            temp_evaluations = {
                "speech_eval": [],
                "listening_test": [],
                "written_test": [],
                "typing_test": []
            }
        
        # Add listening test result to listening_test section
        temp_evaluations["listening_test"].append(result)
        
        # Save back to temporary evaluations
        if not save_temp_evaluation(temp_evaluations, session_id):
            print(f"Warning: Failed to save listening test evaluation for session {session_id}")  # Log warning but don't fail request
    
    return jsonify(result)  # Return evaluation results

@audio_bp.route("/speak", methods=["POST"])
def speak_endpoint():
    """Speak the provided text"""
    try:
        data = request.json  # Get request data
        if not data or not data.get("text"):  # Check if text was provided
            return jsonify({"success": False, "message": "Text is required"}), 400  # Return error if no text

        text = data["text"]  # Extract text from request
        speak_async(text)  # Start text-to-speech in background

        return jsonify({"success": True, "message": "Text-to-speech started"})  # Return success message
    except Exception as e:  # Handle any errors
        return jsonify({"success": False, "message": f"Error with text-to-speech: {str(e)}"}), 500

#New speak function for audio files
@audio_bp.route("/speak-audio", methods=["POST"])
def speak_audio_endpoint():
    """Get the audio file URL for the provided audio ID"""
    try:
        data = request.json  # Get request data
        if not data or not data.get("id"):  # Check if audio ID was provided
            return jsonify({"success": False, "message": "Audio ID is required"}), 400  # Return error if no ID

        audio_id = data["id"]  # Extract audio ID from request
        print(f"DEBUG: Received request for audio with ID: {audio_id}")
        
        # Check if the audio file exists in listening questions first
        listening_audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions', 'listening_questions_audio')
        listening_audio_file = os.path.join(listening_audio_dir, f"{audio_id}.wav")
        
        # Check if the audio file exists in speech questions
        speech_audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions', 'speech_questions_audio')
        speech_audio_file = os.path.join(speech_audio_dir, f"{audio_id}.wav")
        
        if os.path.exists(listening_audio_file):
            # Return the URL to the listening audio file
            audio_url = f"/audio/listening-questions/{audio_id}.wav"
            print(f"DEBUG: Listening audio file found, returning URL: {audio_url}")
        elif os.path.exists(speech_audio_file):
            # Return the URL to the speech audio file
            audio_url = f"/audio/speech-questions/{audio_id}.wav"
            print(f"DEBUG: Speech audio file found, returning URL: {audio_url}")
        else:
            print(f"DEBUG: Audio file not found in either directory")
            return jsonify({"success": False, "message": "Audio file not found"}), 404
        
        return jsonify({
            "success": True, 
            "message": "Audio file available", 
            "audio_url": audio_url
        })
            
    except Exception as e:  # Handle any errors
        print(f"DEBUG: Error in speak-audio endpoint: {str(e)}")
        return jsonify({"success": False, "message": f"Error with audio file: {str(e)}"}), 500

@audio_bp.route("/audio/listening-questions/<path:filename>")
def serve_listening_audio(filename):
    """Serve audio files from the listening_questions_audio directory"""
    try:
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions', 'listening_questions_audio')
        print(f"DEBUG: Serving audio file {filename} from directory: {audio_dir}")
        print(f"DEBUG: Full path: {os.path.join(audio_dir, filename)}")
        return send_from_directory(audio_dir, filename)
    except Exception as e:
        print(f"Error serving audio file {filename}: {e}")
        return jsonify({"error": f"Audio file not found: {str(e)}"}), 404

@audio_bp.route("/audio/speech-questions/<path:filename>")
def serve_speech_audio(filename):
    """Serve audio files from the speech_questions_audio directory"""
    try:
        audio_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'questions', 'speech_questions_audio')
        print(f"DEBUG: Serving speech audio file {filename} from directory: {audio_dir}")
        print(f"DEBUG: Full path: {os.path.join(audio_dir, filename)}")
        return send_from_directory(audio_dir, filename)
    except Exception as e:
        print(f"Error serving speech audio file {filename}: {e}")
        return jsonify({"error": f"Speech audio file not found: {str(e)}"}), 404

@audio_bp.route("/recordings/<path:filename>")
def serve_audio(filename):
    """Serve audio files from the recordings directory"""
    try:
        return send_from_directory("recordings", filename)  # Serve audio file from recordings folder
    except Exception as e:  # Handle file serving errors
        return jsonify({"error": f"Audio file not found: {str(e)}"}), 404  # Return 404 if file not found 