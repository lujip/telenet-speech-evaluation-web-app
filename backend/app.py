from flask import Flask, jsonify, request, send_from_directory
import threading
from flask_cors import CORS
from test_eval import run_full_evaluation
import json
import pyttsx3
import os
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# File path for storing applicant data
APPLICANTS_FILE = "data/applicants.json"
RECORDINGS_DIR = "recordings"

# Global variables for session management
session_questions = None  # Store randomized questions for current session
current_index = 0
current_question = {"text": ""}
session_states = {}  # Store session state for each session ID

def ensure_data_directory():
    # Ensure the data directory exists
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def ensure_recordings_directory():
    # Ensure the recordings directory exists
    if not os.path.exists(RECORDINGS_DIR):
        os.makedirs(RECORDINGS_DIR)

def get_applicant_folder_name(applicant_info, session_id):
    # Generate a folder name for the applicant's recordings
    if applicant_info and applicant_info.get('fullName'):
        # Create a safe folder name from the applicant's name
        safe_name = "".join(c for c in applicant_info['fullName'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        return f"{safe_name}_{session_id}"
    else:
        return f"applicant_{session_id}"

def save_audio_file(audio_wav_path, applicant_info, session_id, question_index):
    # Save audio file to organized folder structure
    ensure_recordings_directory()
    
    # Create applicant folder
    applicant_folder = get_applicant_folder_name(applicant_info, session_id)
    applicant_path = os.path.join(RECORDINGS_DIR, applicant_folder)
    
    if not os.path.exists(applicant_path):
        os.makedirs(applicant_path)
    
    # Generate filename for this question
    filename = f"q{question_index + 1}.wav"
    destination_path = os.path.join(applicant_path, filename)
    
    # Move the audio file to the organized location
    if os.path.exists(audio_wav_path):
        import shutil
        shutil.move(audio_wav_path, destination_path)
        return os.path.join(applicant_folder, filename)
    
    return None

def load_applicants():
    # Load existing applicants data or create empty structure
    ensure_data_directory()
    if os.path.exists(APPLICANTS_FILE):
        try:
            with open(APPLICANTS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"applicants": []}
    return {"applicants": []}

def save_applicants(data):
    #Save applicants data to JSON file
    ensure_data_directory()
    with open(APPLICANTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_questions():
    #Load questions from JSON file
    ensure_data_directory()
    questions_file = "data/questions.json"
    if os.path.exists(questions_file):
        try:
            with open(questions_file, 'r') as f:
                data = json.load(f)
                return data.get("questions", [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def save_questions(questions_data):
    #Save questions to JSON file#
    ensure_data_directory()
    questions_file = "data/questions.json"
    with open(questions_file, 'w') as f:
        json.dump({"questions": questions_data}, f, indent=2)

def get_active_questions():
    #Get only active questions and randomize to 5 questions (only once per session)#
    global session_questions
    
    # If we already have session questions, return them
    if session_questions is not None:
        return session_questions
    
    # Otherwise, randomize and store for this session
    all_questions = load_questions()
    active_questions = [q for q in all_questions if q.get("active", True)]
    
    # Randomize and select only 5 questions
    if len(active_questions) > 5:
        random.shuffle(active_questions)
        active_questions = active_questions[:5]
    
    # Store for this session
    session_questions = active_questions
    return session_questions

def reset_session_questions():
    #Reset session questions for new evaluation session#
    global session_questions, current_index, current_question
    session_questions = None
    current_index = 0
    current_question = {"text": ""}

def get_session_state(session_id):
    #Get session state for a specific session#
    if session_id not in session_states:
        session_states[session_id] = {
            'current_index': 0,
            'questions': None,
            'has_answered': set()
        }
    return session_states[session_id]

def set_session_state(session_id, state):
    #Set session state for a specific session#
    session_states[session_id] = state

def get_active_questions_for_session(session_id):
    #Get active questions for a specific session (randomized once per session)#
    state = get_session_state(session_id)
    
    # If we already have session questions, return them
    if state['questions'] is not None:
        return state['questions']
    
    # Otherwise, randomize and store for this session
    all_questions = load_questions()
    active_questions = [q for q in all_questions if q.get("active", True)]
    
    # Randomize and select only 5 questions
    if len(active_questions) > 5:
        random.shuffle(active_questions)
        active_questions = active_questions[:5]
    
    # Store for this session
    state['questions'] = active_questions
    set_session_state(session_id, state)
    return active_questions

# Initialize questions
questions = get_active_questions()
current_question = {"text": questions[0]["text"] if questions else ""}

def speak(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    for voice in voices:
        if "female" in voice.name.lower() or "zira" in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()

@app.route("/question", methods=["GET"])
def get_current_question():
    # Get session ID from query parameters
    session_id = request.args.get("session_id")
    
    if not session_id:
        return jsonify({"text": "Session ID required", "keywords": []}), 400
    
    # Get session-specific questions and state
    questions = get_active_questions_for_session(session_id)
    state = get_session_state(session_id)
    current_index = state['current_index']
    
    print(f"DEBUG: Session {session_id} - Loaded {len(questions)} active questions")
    print(f"DEBUG: Session {session_id} - Current index: {current_index}")
    
    if not questions or len(questions) == 0:
        print("DEBUG: No active questions found")
        return jsonify({"text": "No questions available", "keywords": []})
    
    # Ensure current_question is valid
    if current_index < len(questions):
        current_question = {
            "text": questions[current_index]["text"],
            "keywords": questions[current_index]["keywords"]
        }
        print(f"DEBUG: Session {session_id} - Returning question {current_index + 1}: {current_question['text'][:50]}...")
    else:
        current_question = {
            "text": questions[0]["text"] if questions else "",
            "keywords": questions[0]["keywords"] if questions else []
        }
        print(f"DEBUG: Session {session_id} - Index out of range, returning first question")
    
    return jsonify(current_question)

@app.route("/question_count", methods=["GET"])
def get_question_count():
    # Get session ID from query parameters
    session_id = request.args.get("session_id")
    
    if not session_id:
        return jsonify({"total": 0, "current": 0}), 400
    
    # Get session-specific questions and state
    questions = get_active_questions_for_session(session_id)
    state = get_session_state(session_id)
    current_index = state['current_index']
    
    return jsonify({
        "total": len(questions),
        "current": current_index
    })

@app.route("/reset_questions", methods=["POST"])
def reset_questions():
    # Get session ID from request
    session_id = request.json.get("session_id") if request.is_json else None
    
    if not session_id:
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    # Get session state
    state = get_session_state(session_id)
    
    # Reset current index but keep the same randomized questions
    state['current_index'] = 0
    state['has_answered'] = set()
    set_session_state(session_id, state)
    
    # Get session-specific questions
    questions = get_active_questions_for_session(session_id)
    
    print(f"DEBUG: Session {session_id} - Resetting questions, new index: {state['current_index']}")
    print(f"DEBUG: Session {session_id} - Loaded {len(questions)} active questions after reset")
    
    if questions and len(questions) > 0:
        current_question = {
            "text": questions[state['current_index']]["text"],
            "keywords": questions[state['current_index']]["keywords"]
        }
        print(f"DEBUG: Session {session_id} - Reset successful, first question: {current_question['text'][:50]}...")
        return jsonify({
            "success": True, 
            "message": "Questions reset to beginning",
            "question": current_question
        })
    else:
        current_question = {
            "text": "",
            "keywords": []
        }
        print(f"DEBUG: Session {session_id} - No active questions available for reset")
        return jsonify({"success": False, "message": "No active questions available"})

@app.route("/finish_evaluation", methods=["POST"])
def finish_evaluation():
    # Handle evaluation completion and save all results to applicants.json
    try:
        session_id = request.json.get("session_id") if request.is_json else None
        
        if session_id:
            # Load temporary applicant data
            temp_applicant_file = f"data/temp_applicant_{session_id}.json"
            temp_eval_file = f"data/temp_evaluation_{session_id}.json"
            
            if os.path.exists(temp_applicant_file) and os.path.exists(temp_eval_file):
                try:
                    # Load applicant data
                    with open(temp_applicant_file, 'r') as f:
                        applicant_data = json.load(f)
                    
                    # Load evaluation data
                    with open(temp_eval_file, 'r') as f:
                        evaluation_data = json.load(f)
                    
                    # Load existing applicants data
                    applicants_data = load_applicants()
                    
                    # Create combined record with all evaluations
                    combined_record = {
                        "id": session_id,
                        "applicant_info": applicant_data.get('applicant', {}),
                        "application_timestamp": applicant_data.get('timestamp'),
                        "evaluations": evaluation_data.get('evaluations', []),
                        "total_questions": len(evaluation_data.get('evaluations', [])),
                        "completion_timestamp": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat()
                    }
                    
                    # Check if applicant already exists (by session_id)
                    existing_index = None
                    for i, applicant in enumerate(applicants_data["applicants"]):
                        if applicant.get("id") == session_id:
                            existing_index = i
                            break
                    
                    if existing_index is not None:
                        # Update existing applicant with all evaluations
                        applicants_data["applicants"][existing_index] = combined_record
                    else:
                        # Add new applicant
                        applicants_data["applicants"].append(combined_record)
                    
                    # Save to applicants.json
                    save_applicants(applicants_data)
                    
                    # Clean up temporary files
                    os.remove(temp_applicant_file)
                    os.remove(temp_eval_file)
                    
                    print(f"Completed evaluation for applicant {session_id} with {len(evaluation_data.get('evaluations', []))} questions")
                    
                except Exception as e:
                    print(f"Error combining final applicant data: {e}")
                    return jsonify({"success": False, "message": f"Error saving evaluation: {str(e)}"}), 500
        
        # Reset question index for next user
        global current_index
        current_index = 0
        current_question["text"] = questions[current_index]["text"]
        
        # Reset session questions for next evaluation
        reset_session_questions()
        
        # Clear session state for this session
        if session_id in session_states:
            del session_states[session_id]
        
        return jsonify({"success": True, "message": "Evaluation completed successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/next_question", methods=["POST"])
def next_question():
    # Get session ID from request
    session_id = request.json.get("session_id") if request.is_json else None
    
    if not session_id:
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    # Get session-specific questions and state
    questions = get_active_questions_for_session(session_id)
    state = get_session_state(session_id)
    current_index = state['current_index']
    
    if not questions or len(questions) == 0:
        return jsonify({
            "success": False, 
            "message": "No active questions available.",
            "currentIndex": current_index
        })
    
    if current_index + 1 < len(questions):
        # Mark current question as answered
        state['has_answered'].add(current_index)
        
        # Move to next question
        state['current_index'] = current_index + 1
        set_session_state(session_id, state)
        
        current_question = {
            "text": questions[state['current_index']]["text"],
            "keywords": questions[state['current_index']]["keywords"]
        }
        
        threading.Thread(target=speak, args=(current_question["text"],)).start()
        return jsonify({
            "success": True, 
            "question": current_question,
            "currentIndex": state['current_index']
        })
    else:
        return jsonify({
            "success": False, 
            "message": "No more questions available.",
            "currentIndex": current_index
        })

@app.route("/store_applicant", methods=["POST"])
def store_applicant():
    # Store applicant data temporarily for later combination with evaluation
    try:
        applicant_data = request.get_json()
        if not applicant_data:
            return jsonify({"success": False, "message": "No applicant data provided"}), 400
        
        # Store in a temporary file named with session ID
        session_id = applicant_data.get('sessionId')
        if not session_id:
            return jsonify({"success": False, "message": "Session ID required"}), 400
        
        temp_file = f"data/temp_applicant_{session_id}.json"
        ensure_data_directory()
        with open(temp_file, 'w') as f:
            json.dump(applicant_data, f, indent=2)
        
        return jsonify({"success": True, "message": "Applicant data stored successfully"})
    
    except Exception as e:
        return jsonify({"success": False, "message": f"Error storing applicant data: {str(e)}"}), 500

@app.route("/evaluate", methods=["POST"])
def evaluate():
    question = request.form.get("question")
    keywords = request.form.getlist("keywords")
    audio = request.files.get("audio")
    session_id = request.form.get("session_id")  # Get session ID from request
    question_index = int(request.form.get("question_index", 0))  # Get question index
    
    if not question or not keywords or not audio:
        return jsonify({"success": False, "message": "Missing question, keywords, or audio file."}), 400
    
    audio_webm_path = "uploaded_answer.webm"
    audio_wav_path = "uploaded_answer.wav"
    audio.save(audio_webm_path)
    
    # Convert webm/ogg to wav using ffmpeg
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", audio_webm_path, audio_wav_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        return jsonify({"success": False, "message": f"Audio conversion failed: {str(e)}"}), 500
    
    result = run_full_evaluation(question, keywords, audio_wav_path)
    import gc
    gc.collect()
    
    # Separate evaluation and comment
    evaluation = result.get("evaluation", {})
    gpt_judgment = result.get("gpt_judgment", "")
    comment = None
    
    # Try to extract comment from gpt_judgment if it's a JSON string
    try:
        import json as _json
        gpt_eval = _json.loads(gpt_judgment) if isinstance(gpt_judgment, str) and gpt_judgment.strip().startswith('{') else None
        if gpt_eval and 'comment' in gpt_eval:
            comment = gpt_eval['comment']
    except Exception:
        pass
    
    if not comment:
        comment = gpt_judgment
    
    # Get applicant info for folder organization
    applicant_info = None
    if session_id:
        temp_applicant_file = f"data/temp_applicant_{session_id}.json"
        if os.path.exists(temp_applicant_file):
            try:
                with open(temp_applicant_file, 'r') as f:
                    temp_data = json.load(f)
                    applicant_info = temp_data.get('applicant', {})
            except Exception as e:
                print(f"Error loading applicant info: {e}")
    
    # Save audio file to organized folder structure
    audio_path = None
    if session_id and applicant_info:
        audio_path = save_audio_file(audio_wav_path, applicant_info, session_id, question_index)
    
    # Prepare evaluation result
    evaluation_result = {
        "question": question,
        "transcript": result.get("transcript"),
        "audio_metrics": result.get("audio_metrics"),
        "evaluation": evaluation,
        "comment": comment,
        "timestamp": datetime.now().isoformat(),
        "audio_path": audio_path  # Add audio path to the evaluation
    }
    
    # Store evaluation result temporarily if session_id is provided
    if session_id:
        # Mark current question as answered
        state = get_session_state(session_id)
        state['has_answered'].add(question_index)
        set_session_state(session_id, state)
        
        temp_eval_file = f"data/temp_evaluation_{session_id}.json"
        ensure_data_directory()
        try:
            # Load existing temporary evaluations or create new
            if os.path.exists(temp_eval_file):
                with open(temp_eval_file, 'r') as f:
                    temp_evaluations = json.load(f)
            else:
                temp_evaluations = {"evaluations": []}
            
            # Add new evaluation
            temp_evaluations["evaluations"].append(evaluation_result)
            
            # Save back to temporary file
            with open(temp_eval_file, 'w') as f:
                json.dump(temp_evaluations, f, indent=2)
            
            print(f"Stored evaluation {len(temp_evaluations['evaluations'])} for session {session_id}")
            
        except Exception as e:
            print(f"Error storing temporary evaluation: {e}")
    
    # Remove uploaded and converted files after processing
    for path in [audio_webm_path, audio_wav_path]:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as cleanup_err:
            print(f"Cleanup failed: {cleanup_err}")
    
    # Print all output for checking
    print("\n--- Evaluation Output ---")
    print(f"Transcript: {result.get('transcript')}")
    print(f"Audio Metrics: {result.get('audio_metrics')}")
    print(f"Evaluation: {evaluation}")
    print(f"Comment: {comment}")
    print("--- End of Output ---\n")
    
    # Return separated evaluation and comment
    return jsonify({
        "transcript": result.get("transcript"),
        "audio_metrics": result.get("audio_metrics"),
        "evaluation": evaluation,
        "comment": comment
    })

@app.route("/get_applicants", methods=["GET"])
def get_applicants():
    # Retrieve all stored applicants data
    try:
        applicants_data = load_applicants()
        return jsonify(applicants_data)
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving applicants: {str(e)}"}), 500

@app.route("/admin/applicants", methods=["GET"])
def admin_get_applicants():
    # Admin endpoint to retrieve all applicants data including temporary files
    try:
        # Load main applicants data
        main_applicants = load_applicants()
        
        # Find and load temporary applicant files
        temp_applicants = []
        data_dir = "data"
        if os.path.exists(data_dir):
            for filename in os.listdir(data_dir):
                if filename.startswith("temp_applicant_") and filename.endswith(".json"):
                    try:
                        with open(os.path.join(data_dir, filename), 'r') as f:
                            temp_data = json.load(f)
                            # Convert temp format to main format
                            applicant_entry = {
                                "id": temp_data.get("sessionId"),
                                "applicant_info": temp_data.get("applicant", {}),
                                "application_timestamp": temp_data.get("timestamp"),
                                "evaluations": [],
                                "total_questions": len(get_active_questions()),
                                "completion_timestamp": None,
                                "last_updated": temp_data.get("timestamp")
                            }
                            
                            # Try to load corresponding evaluation file
                            eval_filename = f"temp_evaluation_{temp_data.get('sessionId')}.json"
                            eval_filepath = os.path.join(data_dir, eval_filename)
                            if os.path.exists(eval_filepath):
                                try:
                                    with open(eval_filepath, 'r') as eval_f:
                                        eval_data = json.load(eval_f)
                                        applicant_entry["evaluations"] = eval_data.get("evaluations", [])
                                except Exception as eval_err:
                                    print(f"Error loading evaluation file {eval_filename}: {eval_err}")
                            
                            temp_applicants.append(applicant_entry)
                    except Exception as temp_err:
                        print(f"Error loading temp file {filename}: {temp_err}")
        
        # Combine main and temporary applicants
        all_applicants = main_applicants.get("applicants", []) + temp_applicants
        
        # Sort by application timestamp (newest first)
        all_applicants.sort(key=lambda x: x.get("application_timestamp", ""), reverse=True)
        
        return jsonify({"applicants": all_applicants})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving applicants: {str(e)}"}), 500

# Admin endpoints for question management
@app.route("/admin/questions", methods=["GET"])
def admin_get_questions():
    #Get all questions (admin only)#
    try:
        all_questions = load_questions()
        return jsonify({"questions": all_questions})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving questions: {str(e)}"}), 500

@app.route("/admin/questions", methods=["POST"])
def admin_add_question():
    #Add a new question (admin only)#
    try:
        data = request.json
        if not data or not data.get("text") or not data.get("keywords"):
            return jsonify({"success": False, "message": "Question text and keywords are required"}), 400
        
        all_questions = load_questions()
        
        # Generate new ID
        new_id = max([q.get("id", 0) for q in all_questions], default=0) + 1
        
        new_question = {
            "id": new_id,
            "text": data["text"],
            "keywords": data["keywords"],
            "active": data.get("active", True)
        }
        
        all_questions.append(new_question)
        save_questions(all_questions)
        
        # Reload active questions
        global questions, current_question
        questions = get_active_questions()
        if questions and current_index < len(questions):
            current_question["text"] = questions[current_index]["text"]
        
        return jsonify({"success": True, "message": "Question added successfully", "question": new_question})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error adding question: {str(e)}"}), 500

@app.route("/admin/questions/<int:question_id>", methods=["PUT"])
def admin_update_question(question_id):
    #Update an existing question (admin only)#
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        all_questions = load_questions()
        
        # Find the question to update
        question_index = None
        for i, q in enumerate(all_questions):
            if q.get("id") == question_id:
                question_index = i
                break
        
        if question_index is None:
            return jsonify({"success": False, "message": "Question not found"}), 404
        
        # Update the question
        if "text" in data:
            all_questions[question_index]["text"] = data["text"]
        if "keywords" in data:
            all_questions[question_index]["keywords"] = data["keywords"]
        if "active" in data:
            all_questions[question_index]["active"] = data["active"]
        
        save_questions(all_questions)
        
        # Reload active questions
        global questions, current_question
        questions = get_active_questions()
        if questions and current_index < len(questions):
            current_question["text"] = questions[current_index]["text"]
        
        return jsonify({"success": True, "message": "Question updated successfully", "question": all_questions[question_index]})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating question: {str(e)}"}), 500

@app.route("/admin/questions/<int:question_id>", methods=["DELETE"])
def admin_delete_question(question_id):
    #Delete a question (admin only)#
    try:
        all_questions = load_questions()
        
        # Find the question to delete
        question_index = None
        for i, q in enumerate(all_questions):
            if q.get("id") == question_id:
                question_index = i
                break
        
        if question_index is None:
            return jsonify({"success": False, "message": "Question not found"}), 404
        
        # Remove the question
        deleted_question = all_questions.pop(question_index)
        save_questions(all_questions)
        
        # Reload active questions
        global questions, current_question
        questions = get_active_questions()
        if questions and current_index < len(questions):
            current_question["text"] = questions[current_index]["text"]
        elif questions:
            current_question["text"] = questions[0]["text"]
        else:
            current_question["text"] = ""
        
        return jsonify({"success": True, "message": "Question deleted successfully", "deleted_question": deleted_question})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error deleting question: {str(e)}"}), 500

@app.route("/admin/questions/reload", methods=["POST"])
def admin_reload_questions():
    #Reload questions from file (admin only)#
    try:
        global questions, current_question
        questions = get_active_questions()
        if questions and current_index < len(questions):
            current_question["text"] = questions[current_index]["text"]
        elif questions:
            current_question["text"] = questions[0]["text"]
        else:
            current_question["text"] = ""
        
        # Reset session questions to get fresh randomized set
        reset_session_questions()
        questions = get_active_questions()
        
        return jsonify({"success": True, "message": "Questions reloaded successfully", "total_questions": len(get_active_questions())})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error reloading questions: {str(e)}"}), 500

@app.route("/admin/auth", methods=["POST"])
def admin_auth():
    #Admin authentication endpoint#
    try:
        data = request.json
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"success": False, "message": "Username and password required"}), 400
        
        # Get credentials from environment variables
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")
        
        if not admin_username or not admin_password:
            return jsonify({"success": False, "message": "Admin credentials not configured"}), 500
        
        # Check credentials
        if data["username"] == admin_username and data["password"] == admin_password:
            return jsonify({"success": True, "message": "Authentication successful"})
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Authentication error: {str(e)}"}), 500

@app.route("/admin/applicants/<session_id>", methods=["DELETE"])
def admin_delete_applicant(session_id):
    #Delete an applicant (admin only)#
    try:
        print(f"Attempting to delete applicant with session_id: {session_id}")
        
        # Load existing applicants data
        applicants_data = load_applicants()
        
        # Find and remove the applicant
        original_count = len(applicants_data["applicants"])
        applicants_data["applicants"] = [
            applicant for applicant in applicants_data["applicants"] 
            if applicant.get("id") != session_id
        ]
        
        # Check if applicant was found and removed
        if len(applicants_data["applicants"]) == original_count:
            print(f"Applicant {session_id} not found in applicants.json")
            # Check if it exists in temporary files
            temp_applicant_file = f"data/temp_applicant_{session_id}.json"
            if os.path.exists(temp_applicant_file):
                print(f"Found temporary applicant file: {temp_applicant_file}")
                try:
                    os.remove(temp_applicant_file)
                    print(f"Deleted temporary applicant file: {temp_applicant_file}")
                    
                    # Also try to delete corresponding evaluation file
                    temp_eval_file = f"data/temp_evaluation_{session_id}.json"
                    if os.path.exists(temp_eval_file):
                        os.remove(temp_eval_file)
                        print(f"Deleted temporary evaluation file: {temp_eval_file}")
                    
                    # Clean up recordings
                    recordings_dir = "recordings"
                    if os.path.exists(recordings_dir):
                        for folder in os.listdir(recordings_dir):
                            if session_id in folder:
                                folder_path = os.path.join(recordings_dir, folder)
                                try:
                                    import shutil
                                    shutil.rmtree(folder_path)
                                    print(f"Deleted recordings folder: {folder_path}")
                                except Exception as e:
                                    print(f"Error deleting recordings folder {folder_path}: {e}")
                    
                    return jsonify({"success": True, "message": "Temporary applicant deleted successfully"})
                except Exception as e:
                    print(f"Error deleting temporary files: {e}")
                    return jsonify({"success": False, "message": f"Error deleting temporary applicant: {str(e)}"}), 500
            else:
                return jsonify({"success": False, "message": f"Applicant with ID '{session_id}' not found"}), 404
        
        # Save updated applicants data
        save_applicants(applicants_data)
        
        # Clean up temporary files if they exist
        temp_applicant_file = f"data/temp_applicant_{session_id}.json"
        temp_eval_file = f"data/temp_evaluation_{session_id}.json"
        
        for temp_file in [temp_applicant_file, temp_eval_file]:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                    print(f"Deleted temporary file: {temp_file}")
                except Exception as e:
                    print(f"Error deleting temporary file {temp_file}: {e}")
        
        # Clean up recordings directory if it exists
        recordings_dir = "recordings"
        if os.path.exists(recordings_dir):
            for folder in os.listdir(recordings_dir):
                if session_id in folder:
                    folder_path = os.path.join(recordings_dir, folder)
                    try:
                        import shutil
                        shutil.rmtree(folder_path)
                        print(f"Deleted recordings folder: {folder_path}")
                    except Exception as e:
                        print(f"Error deleting recordings folder {folder_path}: {e}")
        
        print(f"Deleted applicant {session_id}")
        return jsonify({"success": True, "message": "Applicant deleted successfully"})
        
    except Exception as e:
        print(f"Error in admin_delete_applicant: {e}")
        return jsonify({"success": False, "message": f"Error deleting applicant: {str(e)}"}), 500

@app.route("/speak", methods=["POST"])
def speak_endpoint():
    #Speak the provided text#
    try:
        data = request.json
        if not data or not data.get("text"):
            return jsonify({"success": False, "message": "Text is required"}), 400
        
        text = data["text"]
        threading.Thread(target=speak, args=(text,)).start()
        
        return jsonify({"success": True, "message": "Text-to-speech started"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error with text-to-speech: {str(e)}"}), 500

@app.route("/recordings/<path:filename>")
def serve_audio(filename):
    # Serve audio files from the recordings directory
    try:
        return send_from_directory("recordings", filename)
    except Exception as e:
        return jsonify({"error": f"Audio file not found: {str(e)}"}), 404

@app.route("/question_status", methods=["GET"])
def get_question_status():
    # Get session ID from query parameters
    session_id = request.args.get("session_id")
    
    if not session_id:
        return jsonify({"has_answered": False}), 400
    
    # Get session state
    state = get_session_state(session_id)
    current_index = state['current_index']
    
    return jsonify({
        "has_answered": current_index in state['has_answered'],
        "current_index": current_index
    })

@app.route("/mark_answered", methods=["POST"])
def mark_answered():
    # Mark a question as answered for a session
    try:
        data = request.json
        session_id = data.get("session_id")
        question_index = data.get("question_index")
        
        if not session_id or question_index is None:
            return jsonify({"success": False, "message": "Session ID and question index required"}), 400
        
        # Get session state and mark question as answered
        state = get_session_state(session_id)
        state['has_answered'].add(question_index)
        set_session_state(session_id, state)
        
        return jsonify({"success": True, "message": "Question marked as answered"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Error marking question as answered: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(port=5000)
