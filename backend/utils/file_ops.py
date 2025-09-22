import os
import json
import shutil
from datetime import datetime
from config import APPLICANTS_FILE, RECORDINGS_DIR, QUESTIONS_FILE, LISTENING_TEST_QUESTIONS_FILE, USERS_FILE, DEFAULT_SUPER_ADMIN
from .db import db

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

def save_audio_file(audio_wav_path, applicant_info, session_id, question_index, test_type="speech"):
    """Save audio file to organized folder structure"""
    ensure_recordings_directory()  # Ensure recordings directory exists
    
    # Create applicant folder
    applicant_folder = get_applicant_folder_name(applicant_info, session_id)  # Get organized folder name
    
    # Create test-specific subfolder
    if test_type == "listening_test":
        test_folder = "listening_test_recordings"
        applicant_path = os.path.join(RECORDINGS_DIR, test_folder, applicant_folder)
    elif test_type == "speech":
        test_folder = "speech_evaluation_recordings"
        applicant_path = os.path.join(RECORDINGS_DIR, test_folder, applicant_folder)
    else:
        # Default case for other test types
        applicant_path = os.path.join(RECORDINGS_DIR, applicant_folder)
    
    if not os.path.exists(applicant_path):
        os.makedirs(applicant_path)  # Create applicant-specific folder
    
    # Generate filename for this question
    if test_type == "listening_test":
        filename = f"listening_q{question_index + 1}.wav"  # Name file by question number
    elif test_type == "speech":
        filename = f"speech_q{question_index + 1}.wav"  # Name file by question number
    else:
        filename = f"q{question_index + 1}.wav"  # Name file by question number
    
    destination_path = os.path.join(applicant_path, filename)
    
    # Move the audio file to the organized location
    if os.path.exists(audio_wav_path):
        shutil.move(audio_wav_path, destination_path)  # Move audio to organized location
        if test_type == "listening_test":
            return os.path.join(test_folder, applicant_folder, filename)
        elif test_type == "speech":
            return os.path.join(test_folder, applicant_folder, filename)
        else:
            return os.path.join(applicant_folder, filename)
    
    return None

def load_applicants():
    """Load all applicants from MongoDB."""
    applicants = list(db.applicants.find({}, {'_id': 0}))  # Exclude MongoDB's _id field
    return {"applicants": applicants}


def save_applicants(data):
    """Save applicants data to MongoDB (replace all)."""
    try:
        # Remove all existing applicants (to match previous file overwrite behavior)
        db.applicants.delete_many({})
        # Insert new applicants
        applicants = data.get("applicants", [])
        if applicants:
            db.applicants.insert_many(applicants)
        return True
    except Exception as e:
        print(f"Error saving applicants: {e}")
        return False

def load_questions():
    """Load questions from MongoDB."""
    questions = list(db.questions.find({}, {'_id': 0}))
    return questions


def save_questions(questions_data):
    """Save questions to MongoDB (replace all)."""
    try:
        db.questions.delete_many({})
        if questions_data:
            db.questions.insert_many(questions_data)
        return True
    except Exception as e:
        print(f"Error saving questions: {e}")
        return False

def load_listening_test_questions():
    """Load listening test questions from MongoDB."""
    questions = list(db.listening_test_questions.find({}, {'_id': 0}))
    return questions


def save_listening_test_questions(questions_data):
    """Save listening test questions to MongoDB (replace all)."""
    try:
        db.listening_test_questions.delete_many({})
        if questions_data:
            db.listening_test_questions.insert_many(questions_data)
        return True
    except Exception as e:
        print(f"Error saving listening test questions: {e}")
        return False

def load_written_test_questions():
    """Load written test questions from MongoDB."""
    questions = list(db.written_test_questions.find({}, {'_id': 0}))
    return questions


def save_written_test_questions(questions_data):
    """Save written test questions to MongoDB (replace all)."""
    try:
        db.written_test_questions.delete_many({})
        if questions_data:
            db.written_test_questions.insert_many(questions_data)
        return True
    except Exception as e:
        print(f"Error saving written test questions: {e}")
        return False

def save_temp_applicant(applicant_data, session_id):
    """Store applicant data temporarily in MongoDB for later combination with evaluation."""
    try:
        db.temp_applicants.replace_one({"sessionId": session_id}, applicant_data, upsert=True)
        return True
    except Exception as e:
        print(f"Error saving temp applicant: {e}")
        return False


def load_temp_applicant(session_id):
    """Load temporary applicant data from MongoDB."""
    doc = db.temp_applicants.find_one({"sessionId": session_id}, {'_id': 0})
    return doc

def load_all_temp_applicants():
    """Load all temporary applicants from MongoDB."""
    try:
        temp_applicants = list(db.temp_applicants.find({}, {'_id': 0}))
        return temp_applicants
    except Exception as e:
        print(f"Error loading all temp applicants: {e}")
        return []

def save_temp_evaluation(evaluation_data, session_id, question_index=None, test_type="speech"):
    """Store evaluation data temporarily in MongoDB with segmented structure."""
    try:
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
            for section in ['speech_eval', 'listening_test', 'written_test', 'typing_test']:
                if section in evaluation_data:
                    existing_data[section] = evaluation_data[section]
        # If question_index is provided, store at specific index (not implemented for MongoDB, just store the structure)
        db.temp_evaluations.replace_one({"sessionId": session_id}, {"sessionId": session_id, **existing_data}, upsert=True)
        return True
    except Exception as e:
        print(f"Error saving temp evaluation: {e}")
        return False


def load_temp_evaluation(session_id):
    """Load temporary evaluation data from MongoDB."""
    doc = db.temp_evaluations.find_one({"sessionId": session_id}, {'_id': 0})
    if doc:
        doc.pop("sessionId", None)
    return doc

def save_temp_comments(session_id, comments):
    """Save comments for a temporary applicant to MongoDB"""
    try:
        db.temp_comments.replace_one(
            {"sessionId": session_id}, 
            {"sessionId": session_id, "comments": comments}, 
            upsert=True
        )
        return True
    except Exception as e:
        print(f"Error saving temp comments: {e}")
        return False

def load_temp_comments(session_id):
    """Load comments for a temporary applicant from MongoDB"""
    try:
        doc = db.temp_comments.find_one({"sessionId": session_id}, {'_id': 0})
        if doc:
            return doc.get("comments", "")
        return ""
    except Exception as e:
        print(f"Error loading temp comments: {e}")
        return ""

def cleanup_temp_files(session_id):
    """Clean up temporary data for a session from MongoDB collections"""
    try:
        # Remove temporary applicant data
        result1 = db.temp_applicants.delete_one({"sessionId": session_id})
        if result1.deleted_count > 0:
            print(f"Deleted temporary applicant data for session {session_id}")
        
        # Remove temporary evaluation data
        result2 = db.temp_evaluations.delete_one({"sessionId": session_id})
        if result2.deleted_count > 0:
            print(f"Deleted temporary evaluation data for session {session_id}")
        
        # Remove temporary comments data
        result3 = db.temp_comments.delete_one({"sessionId": session_id})
        if result3.deleted_count > 0:
            print(f"Deleted temporary comments data for session {session_id}")
            
        return True
    except Exception as e:
        print(f"Error cleaning up temporary data for session {session_id}: {e}")
        return False

def cleanup_recordings(session_id):
    """Clean up recordings directory for a session"""
    if os.path.exists(RECORDINGS_DIR):  # Check if recordings directory exists
        # Clean up test-specific folders
        test_folders = ["speech_evaluation_recordings", "listening_test_recordings"]
        
        for test_folder in test_folders:
            test_folder_path = os.path.join(RECORDINGS_DIR, test_folder)
            if os.path.exists(test_folder_path):
                for applicant_folder in os.listdir(test_folder_path):
                    if session_id in applicant_folder:  # Check if folder belongs to this session
                        folder_path = os.path.join(test_folder_path, applicant_folder)
                        try:
                            shutil.rmtree(folder_path)  # Remove entire folder and contents
                            print(f"Deleted recordings folder: {folder_path}")  # Log successful deletion
                        except Exception as e:
                            print(f"Error deleting recordings folder {folder_path}: {e}")  # Log deletion errors
        
        # Also clean up any folders directly in recordings directory (for backward compatibility)
        for folder in os.listdir(RECORDINGS_DIR):  # Iterate through all folders
            folder_path = os.path.join(RECORDINGS_DIR, folder)
            if os.path.isdir(folder_path) and session_id in folder:  # Check if folder belongs to this session
                try:
                    shutil.rmtree(folder_path)  # Remove entire folder and contents
                    print(f"Deleted recordings folder: {folder_path}")  # Log successful deletion
                except Exception as e:
                    print(f"Error deleting recordings folder {folder_path}: {e}")  # Log deletion errors 

def load_users():
    """Load users from MongoDB."""
    users = list(db.users.find({}, {'_id': 0}))
    return users


def save_users(users_list):
    """Save users to MongoDB (replace all)."""
    try:
        db.users.delete_many({})
        if users_list:
            db.users.insert_many(users_list)
        return True
    except Exception as e:
        print(f"Error saving users: {e}")
        return False

def find_user_by_username(username):
    """Find a user by username"""
    users = load_users()
    return next((user for user in users if user.get("username") == username), None)

def find_user_by_id(user_id):
    """Find a user by ID"""
    users = load_users()
    return next((user for user in users if user.get("id") == user_id), None)

def create_user(user_data):
    """Create a new user"""
    users = load_users()
    
    # Generate new ID - safely handle different ID formats
    max_user_num = 0
    for user in users:
        user_id = user.get('id', '')
        if user_id.startswith('user_'):
            try:
                # Extract numeric part after 'user_'
                num_part = user_id.split('_', 1)[1]
                user_num = int(num_part)
                max_user_num = max(max_user_num, user_num)
            except (ValueError, IndexError):
                # Skip IDs that don't match expected format
                continue
    
    new_id = f"user_{max_user_num + 1}"
    
    user_data["id"] = new_id
    user_data["created_at"] = datetime.now().isoformat()
    
    users.append(user_data)
    
    if save_users(users):
        return user_data
    return None

def update_user(user_id, update_data):
    """Update an existing user"""
    users = load_users()
    
    for i, user in enumerate(users):
        if user.get("id") == user_id:
            users[i].update(update_data)
            users[i]["updated_at"] = datetime.now().isoformat()
            
            if save_users(users):
                return users[i]
            break
    
    return None

def delete_user(user_id):
    """Delete a user"""
    users = load_users()
    
    # Don't allow deleting the last super admin
    super_admins = [u for u in users if u.get("role") == "super_admin" and u.get("active", True)]
    if len(super_admins) <= 1:
        user_to_delete = next((u for u in users if u.get("id") == user_id), None)
        if user_to_delete and user_to_delete.get("role") == "super_admin":
            return False, "Cannot delete the last super admin"
    
    original_count = len(users)
    users = [user for user in users if user.get("id") != user_id]
    
    if len(users) < original_count:
        if save_users(users):
            return True, "User deleted successfully"
    
    return False, "User not found or could not be deleted" 

def load_typing_tests():
    """Load typing tests from MongoDB."""
    tests = list(db.typing_tests.find({}, {'_id': 0}))
    return tests


def save_typing_tests(tests_data):
    """Save typing tests to MongoDB (replace all)."""
    try:
        db.typing_tests.delete_many({})
        if tests_data:
            db.typing_tests.insert_many(tests_data)
        return True
    except Exception as e:
        print(f"Error saving typing tests: {e}")
        return False 