from flask import Blueprint, jsonify, request, send_from_directory
import os
import subprocess
from datetime import datetime
from utils.file_ops import save_audio_file, save_temp_evaluation
from utils.evaluation import run_evaluation
from utils.session import mark_question_answered
from utils.tts import speak_async

audio_bp = Blueprint('audio', __name__)

@audio_bp.route("/evaluate", methods=["POST"])
def evaluate():
    """Evaluate audio response for a question"""
    question = request.form.get("question")  # Get question text from form data
    keywords = request.form.getlist("keywords")  # Get expected keywords list
    audio = request.files.get("audio")  # Get uploaded audio file
    session_id = request.form.get("session_id")  # Get session ID from request
    question_index = int(request.form.get("question_index", 0))  # Get question index

    if not question or not keywords or not audio:  # Validate required fields
        return jsonify({"success": False, "message": "Missing question, keywords, or audio file."}), 400

    audio_webm_path = "uploaded_answer.webm"  # Temporary path for uploaded audio
    audio_wav_path = "uploaded_answer.wav"  # Temporary path for converted audio
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
        from utils.file_ops import load_temp_applicant  # Import function to load applicant data
        applicant_info = load_temp_applicant(session_id)  # Load applicant information for this session
        if applicant_info:  # Check if applicant data was found
            applicant_info = applicant_info.get('applicant', {})  # Extract applicant details

    # Save audio file to organized folder structure
    audio_path = None
    if session_id and applicant_info:  # Check if we have both session and applicant info
        audio_path = save_audio_file(audio_wav_path, applicant_info, session_id, question_index)  # Save audio to organized folder
    
        # Prepare evaluation result
    evaluation_result = {  # Create evaluation result object
        "question": question,  # Store the question that was answered
        "transcript": result.get("transcript"),  # Store speech-to-text transcript
        "audio_metrics": result.get("audio_metrics"),  # Store audio analysis metrics
        "evaluation": result.get("evaluation"),  # Store evaluation scores
        "comment": result.get("comment"),  # Store GPT-generated comment
        "timestamp": datetime.now().isoformat(),  # Record when evaluation was performed
        "audio_path": audio_path  # Add audio path to the evaluation
    }

    # Store evaluation result temporarily if session_id is provided
    if session_id:  # Check if this is part of a session
        # Mark current question as answered
        mark_question_answered(session_id, question_index)  # Update session state

        # Load existing temporary evaluations or create new
        from utils.file_ops import load_temp_evaluation  # Import function to load evaluation data
        temp_evaluations = load_temp_evaluation(session_id)  # Load existing evaluations for this session
        if not temp_evaluations:  # Check if no evaluations exist yet
            temp_evaluations = {
                "speech_eval": [],
                "listening_test": [],
                "written_test": [],
                "typing_test": []
            }

        # Add new evaluation to speech_eval section
        temp_evaluations["speech_eval"].append(evaluation_result)  # Append new evaluation to speech_eval list

        # Save back to temporary file
        save_temp_evaluation(temp_evaluations, session_id)  # Persist updated evaluations

        print(f"Stored speech evaluation {len(temp_evaluations['speech_eval'])} for session {session_id}")  # Log evaluation count
    
        # Remove uploaded and converted files after processing
    for path in [audio_webm_path, audio_wav_path]:  # Iterate through temporary audio files
        try:
            if os.path.exists(path):  # Check if file exists
                os.remove(path)  # Delete temporary audio file
        except Exception as cleanup_err:  # Handle cleanup errors
            print(f"Cleanup failed: {cleanup_err}")  # Log cleanup failures

    # Print all output for checking
    print("\n--- Evaluation Output ---")  # Debug output header
    print(f"Transcript: {result.get('transcript')}")  # Print speech transcript
    print(f"Audio Metrics: {result.get('audio_metrics')}")  # Print audio analysis results
    print(f"Evaluation: {result.get('evaluation')}")  # Print evaluation scores
    print(f"Comment: {result.get('comment')}")  # Print GPT comment
    print("--- End of Output ---\n")  # Debug output footer

    # Return separated evaluation and comment
    return jsonify({  # Return evaluation results as JSON
        "transcript": result.get("transcript"),  # Return speech transcript
        "audio_metrics": result.get("audio_metrics"),  # Return audio metrics
        "evaluation": result.get("evaluation"),  # Return evaluation scores
        "comment": result.get("comment")  # Return GPT comment
    })

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

@audio_bp.route("/recordings/<path:filename>")
def serve_audio(filename):
    """Serve audio files from the recordings directory"""
    try:
        return send_from_directory("recordings", filename)  # Serve audio file from recordings folder
    except Exception as e:  # Handle file serving errors
        return jsonify({"error": f"Audio file not found: {str(e)}"}), 404  # Return 404 if file not found 