import os
import json
import shutil
from datetime import datetime
from config import APPLICANTS_FILE, RECORDINGS_DIR, QUESTIONS_FILE, LISTENING_TEST_QUESTIONS_FILE, USERS_FILE, DEFAULT_SUPER_ADMIN

def ensure_data_directory():
    """Ensure the data directory exists"""
    data_dir = "data"  # Create data directory if it doesn't exist
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

def ensure_temp_applicants_directory():
    """Ensure the temp_applicants directory exists"""
    temp_dir = "data/temp_applicants"  # Create temp_applicants directory if it doesn't exist
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

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

def load_listening_test_questions():
    """Load listening test questions from JSON file"""
    ensure_data_directory()  # Ensure data directory exists
    if os.path.exists(LISTENING_TEST_QUESTIONS_FILE):  # Check if file exists
        try:
            with open(LISTENING_TEST_QUESTIONS_FILE, 'r') as f:
                data = json.load(f)  # Load questions data
                return data.get("questions", [])  # Return questions array or empty list
        except (json.JSONDecodeError, FileNotFoundError):
            return []  # Return empty list on error
    return []

def save_listening_test_questions(questions_data):
    """Save listening test questions to JSON file"""
    ensure_data_directory()  # Ensure data directory exists
    with open(LISTENING_TEST_QUESTIONS_FILE, 'w') as f:
        json.dump({"questions": questions_data}, f, indent=2)  # Save questions data to JSON file

def save_temp_applicant(applicant_data, session_id):
    """Store applicant data temporarily for later combination with evaluation"""
    ensure_temp_applicants_directory()  # Ensure temp_applicants directory exists
    temp_file = f"data/temp_applicants/temp_applicant_{session_id}.json"  # Create temp filename with session ID
    with open(temp_file, 'w') as f:
        json.dump(applicant_data, f, indent=2)  # Save applicant data to temporary file

def load_temp_applicant(session_id):
    """Load temporary applicant data"""
    temp_file = f"data/temp_applicants/temp_applicant_{session_id}.json"  # Construct temp filename
    if os.path.exists(temp_file):  # Check if temp file exists
        try:
            with open(temp_file, 'r') as f:
                return json.load(f)  # Load and return temp applicant data
        except Exception:
            return None  # Return None on error
    return None

def save_temp_evaluation(evaluation_data, session_id, question_index=None, test_type="speech"):
    """Store evaluation data temporarily with segmented structure"""
    ensure_temp_applicants_directory()  # Ensure temp_applicants directory exists
    temp_file = f"data/temp_applicants/temp_evaluation_{session_id}.json"  # Create temp filename with session ID
    
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
    
    # If question_index is provided, store at specific index
    if question_index is not None:
        if test_type == "listening_test":
            # Ensure listening_test array has enough elements
            while len(existing_data["listening_test"]) <= question_index:
                existing_data["listening_test"].append({})
            
            # Store evaluation at the correct index
            existing_data["listening_test"][question_index] = evaluation_data
        else:
            # Handle speech evaluation (new segmented format)
            if "speech_eval" not in existing_data:
                existing_data["speech_eval"] = []
            
            # Ensure speech_eval array has enough elements
            while len(existing_data["speech_eval"]) <= question_index:
                existing_data["speech_eval"].append({})
            
            # Store evaluation at the correct index
            existing_data["speech_eval"][question_index] = evaluation_data
    else:
        # Merge with existing data, preserving segmented structure
        for section in ['speech_eval', 'listening_test', 'written_test', 'typing_test']:
            if section in evaluation_data:
                existing_data[section] = evaluation_data[section]
    
    with open(temp_file, 'w') as f:
        json.dump(existing_data, f, indent=2)  # Save evaluation data to temporary file

def load_temp_evaluation(session_id):
    """Load temporary evaluation data"""
    temp_file = f"data/temp_applicants/temp_evaluation_{session_id}.json"  # Construct temp filename
    if os.path.exists(temp_file):  # Check if temp file exists
        try:
            with open(temp_file, 'r') as f:
                return json.load(f)  # Load and return temp evaluation data
        except Exception:
            return None  # Return None on error
    return None

def save_temp_comments(session_id, comments):
    """Save comments for a temporary applicant"""
    ensure_temp_applicants_directory()  # Ensure temp_applicants directory exists
    temp_file = f"data/temp_applicants/temp_comments_{session_id}.json"  # Create temp comments filename
    with open(temp_file, 'w') as f:
        json.dump({"comments": comments}, f, indent=2)  # Save comments data

def load_temp_comments(session_id):
    """Load comments for a temporary applicant"""
    temp_file = f"data/temp_applicants/temp_comments_{session_id}.json"  # Construct temp comments filename
    if os.path.exists(temp_file):  # Check if temp comments file exists
        try:
            with open(temp_file, 'r') as f:
                data = json.load(f)  # Load comments data
                return data.get("comments", [])  # Return comments array
        except Exception:
            return []  # Return empty list on error
    return []

def cleanup_temp_files(session_id):
    """Clean up temporary files for a session"""
    temp_files = [
        f"data/temp_applicants/temp_applicant_{session_id}.json",  # List of temp files to clean up
        f"data/temp_applicants/temp_evaluation_{session_id}.json",
        f"data/temp_applicants/temp_comments_{session_id}.json"
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
    """Load users from the users file"""
    try:
        if not os.path.exists(USERS_FILE):
            # Create default structure with default super admin
            default_data = {
                "users": [],
                "last_updated": datetime.now().isoformat()
            }
            
            # Create data directory if it doesn't exist
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            
            # Create default super admin if no users file exists
            from utils.auth import hash_password
            default_admin = DEFAULT_SUPER_ADMIN.copy()
            default_admin["password"] = hash_password(default_admin["password"])
            default_admin["created_at"] = datetime.now().isoformat()
            default_data["users"] = [default_admin]
            
            with open(USERS_FILE, 'w') as f:
                json.dump(default_data, f, indent=2)
            
            print(f"✅ Created default users file with super admin: {default_admin['username']}")
            return default_data["users"]
        
        with open(USERS_FILE, 'r') as f:
            data = json.load(f)
            return data.get("users", [])
    except Exception as e:
        print(f"❌ Error loading users: {e}")
        return []

def save_users(users_list):
    """Save users to the users file"""
    try:
        ensure_data_directory()
        
        users_data = {
            "users": users_list,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(USERS_FILE, 'w') as f:
            json.dump(users_data, f, indent=2)
        
        print(f"✅ Saved {len(users_list)} users to {USERS_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error saving users: {e}")
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