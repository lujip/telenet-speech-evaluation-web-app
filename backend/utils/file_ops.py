import os
import json
import shutil
from datetime import datetime
from config import APPLICANTS_FILE, RECORDINGS_DIR, QUESTIONS_FILE

def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = "data"  # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def ensure_recordings_directory():
    """Ensure the recordings directory exists"""
    if not os.path.exists(RECORDINGS_DIR):  # Create recordings directory if it doesn't exist
        os.makedirs(RECORDINGS_DIR)

def get_applicant_folder_name(applicant_info, session_id):
    """Generate a folder name for the applicant's recordings"""
    if applicant_info and applicant_info.get('fullName'):  # Generate safe folder name from applicant's full name
        # Create a safe folder name from the applicant's name
        safe_name = "".join(c for c in applicant_info['fullName'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_')
        return f"{safe_name}_{session_id}"
    else:
        return f"applicant_{session_id}"  # Fallback to generic name if no applicant info

def save_audio_file(audio_wav_path, applicant_info, session_id, question_index):
    """Save audio file to organized folder structure"""
    ensure_recordings_directory()  # Ensure recordings directory exists
    
    # Create applicant folder
    applicant_folder = get_applicant_folder_name(applicant_info, session_id)  # Get organized folder name
    applicant_path = os.path.join(RECORDINGS_DIR, applicant_folder)
    
    if not os.path.exists(applicant_path):
        os.makedirs(applicant_path)  # Create applicant-specific folder
    
    # Generate filename for this question
    filename = f"q{question_index + 1}.wav"  # Name file by question number
    destination_path = os.path.join(applicant_path, filename)
    
    # Move the audio file to the organized location
    if os.path.exists(audio_wav_path):
        shutil.move(audio_wav_path, destination_path)  # Move audio to organized location
        return os.path.join(applicant_folder, filename)
    
    return None

def load_applicants():
    """Load existing applicants data or create empty structure"""
    ensure_data_directory()  # Ensure data directory exists
    if os.path.exists(APPLICANTS_FILE):  # Check if applicants file exists
        try:
            with open(APPLICANTS_FILE, 'r') as f:
                return json.load(f)  # Load and return applicants data
        except (json.JSONDecodeError, FileNotFoundError):
            return {"applicants": []}  # Return empty structure on error
    return {"applicants": []}

def save_applicants(data):
    """Save applicants data to JSON file"""
    ensure_data_directory()  # Ensure data directory exists
    with open(APPLICANTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)  # Save applicants data to JSON file

def load_questions():
    """Load questions from JSON file"""
    ensure_data_directory()  # Ensure data directory exists
    if os.path.exists(QUESTIONS_FILE):  # Check if questions file exists
        try:
            with open(QUESTIONS_FILE, 'r') as f:
                data = json.load(f)  # Load questions data
                return data.get("questions", [])  # Return questions array or empty list
        except (json.JSONDecodeError, FileNotFoundError):
            return []  # Return empty list on error
    return []

def save_questions(questions_data):
    """Save questions to JSON file"""
    ensure_data_directory()  # Ensure data directory exists
    with open(QUESTIONS_FILE, 'w') as f:
        json.dump({"questions": questions_data}, f, indent=2)  # Save questions data to JSON file

def save_temp_applicant(applicant_data, session_id):
    """Store applicant data temporarily for later combination with evaluation"""
    ensure_data_directory()  # Ensure data directory exists
    temp_file = f"data/temp_applicant_{session_id}.json"  # Create temp filename with session ID
    with open(temp_file, 'w') as f:
        json.dump(applicant_data, f, indent=2)  # Save applicant data to temporary file

def load_temp_applicant(session_id):
    """Load temporary applicant data"""
    temp_file = f"data/temp_applicant_{session_id}.json"  # Construct temp filename
    if os.path.exists(temp_file):  # Check if temp file exists
        try:
            with open(temp_file, 'r') as f:
                return json.load(f)  # Load and return temp applicant data
        except Exception:
            return None  # Return None on error
    return None

def save_temp_evaluation(evaluation_data, session_id):
    """Store evaluation data temporarily with segmented structure"""
    ensure_data_directory()  # Ensure data directory exists
    temp_file = f"data/temp_evaluation_{session_id}.json"  # Create temp filename with session ID
    
    # Load existing data to preserve structure
    existing_data = load_temp_evaluation(session_id)
    if existing_data:
        # Merge with existing data, preserving segmented structure
        for section in ['speech_eval', 'listening_test', 'written_test', 'typing_test']:
            if section in evaluation_data:
                existing_data[section] = evaluation_data[section]
    else:
        # Create new segmented structure
        existing_data = {
            "speech_eval": [],
            "listening_test": [],
            "written_test": [],
            "typing_test": []
        }
        # If evaluation_data has the old format, migrate it
        if "evaluations" in evaluation_data:
            existing_data["speech_eval"] = evaluation_data["evaluations"]
        else:
            # Merge new sections
            for section in ['speech_eval', 'listening_test', 'written_test', 'typing_test']:
                if section in evaluation_data:
                    existing_data[section] = evaluation_data[section]
    
    with open(temp_file, 'w') as f:
        json.dump(existing_data, f, indent=2)  # Save evaluation data to temporary file

def load_temp_evaluation(session_id):
    """Load temporary evaluation data"""
    temp_file = f"data/temp_evaluation_{session_id}.json"  # Construct temp filename
    if os.path.exists(temp_file):  # Check if temp file exists
        try:
            with open(temp_file, 'r') as f:
                return json.load(f)  # Load and return temp evaluation data
        except Exception:
            return None  # Return None on error
    return None

def cleanup_temp_files(session_id):
    """Clean up temporary files for a session"""
    temp_files = [
        f"data/temp_applicant_{session_id}.json",  # List of temp files to clean up
        f"data/temp_evaluation_{session_id}.json"
    ]
    
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)  # Delete each temporary file
        except Exception as e:
            print(f"Error deleting temporary file {temp_file}: {e}")  # Log deletion errors

def cleanup_recordings(session_id):
    """Clean up recordings directory for a session"""
    if os.path.exists(RECORDINGS_DIR):  # Check if recordings directory exists
        for folder in os.listdir(RECORDINGS_DIR):  # Iterate through all folders
            if session_id in folder:  # Check if folder belongs to this session
                folder_path = os.path.join(RECORDINGS_DIR, folder)
                try:
                    shutil.rmtree(folder_path)  # Remove entire folder and contents
                    print(f"Deleted recordings folder: {folder_path}")  # Log successful deletion
                except Exception as e:
                    print(f"Error deleting recordings folder {folder_path}: {e}")  # Log deletion errors 