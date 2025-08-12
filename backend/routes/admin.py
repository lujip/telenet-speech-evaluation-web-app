from flask import Blueprint, jsonify, request
import os
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.file_ops import (
    load_applicants, load_questions, save_questions, 
    cleanup_temp_files, cleanup_recordings
)
from utils.session import clear_session

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin/applicants", methods=["GET"])
def admin_get_applicants():
    """Admin endpoint to retrieve all applicants data including temporary files"""
    try:
        # Load main applicants data
        main_applicants = load_applicants()  # Load existing applicants from main data file
        
        # Find and load temporary applicant files
        temp_applicants = []  # Initialize list for temporary applicants
        data_dir = "data"  # Set data directory path
        if os.path.exists(data_dir):  # Check if data directory exists
            for filename in os.listdir(data_dir):  # Iterate through all files in data directory
                if filename.startswith("temp_applicant_") and filename.endswith(".json"):  # Find temporary applicant files
                    try:
                        with open(os.path.join(data_dir, filename), 'r') as f:  # Open temporary applicant file
                            import json
                            temp_data = json.load(f)  # Load JSON data from temporary file
                            # Convert temp format to main format
                            applicant_entry = {  # Create standardized applicant entry format
                                "id": temp_data.get("sessionId"),  # Use session ID as applicant ID
                                "applicant_info": temp_data.get("applicant", {}),  # Extract applicant information
                                "application_timestamp": temp_data.get("timestamp"),  # Get application timestamp
                                "evaluations": [],  # Initialize empty evaluations list
                                "total_questions": 5,  # Default to 5 questions
                                "completion_timestamp": None,  # Set completion timestamp to None
                                "last_updated": temp_data.get("timestamp")  # Set last updated timestamp
                            }
                            
                            # Try to load corresponding evaluation file
                            eval_filename = f"temp_evaluation_{temp_data.get('sessionId')}.json"  # Generate evaluation filename
                            eval_filepath = os.path.join(data_dir, eval_filename)
                            if os.path.exists(eval_filepath):  # Check if evaluation file exists
                                try:
                                    with open(eval_filepath, 'r') as eval_f:  # Open evaluation file
                                        eval_data = json.load(eval_f)  # Load evaluation JSON data
                                        # Handle both old and new segmented structure
                                        if "evaluations" in eval_data:
                                            # Old format - migrate to new structure
                                            applicant_entry["evaluations"] = eval_data.get("evaluations", [])
                                        else:
                                            # New segmented format - combine all sections
                                            all_evaluations = []
                                            all_evaluations.extend(eval_data.get("speech_eval", []))
                                            all_evaluations.extend(eval_data.get("listening_test", []))
                                            all_evaluations.extend(eval_data.get("written_test", []))
                                            all_evaluations.extend(eval_data.get("typing_test", []))
                                            applicant_entry["evaluations"] = all_evaluations
                                except Exception as eval_err:  # Handle evaluation file loading errors
                                    print(f"Error loading evaluation file {eval_filename}: {eval_err}")
                            
                            temp_applicants.append(applicant_entry)  # Add temporary applicant to list
                    except Exception as temp_err:  # Handle temporary file loading errors
                        print(f"Error loading temp file {filename}: {temp_err}")
        
        # Combine main and temporary applicants
        all_applicants = main_applicants.get("applicants", []) + temp_applicants  # Merge both applicant lists
        
        # Sort by application timestamp (newest first)
        all_applicants.sort(key=lambda x: x.get("application_timestamp", ""), reverse=True)  # Sort applicants by timestamp
        
        return jsonify({"applicants": all_applicants})  # Return all applicants as JSON response
    except Exception as e:  # Handle any unexpected errors
        return jsonify({"success": False, "message": f"Error retrieving applicants: {str(e)}"}), 500

@admin_bp.route("/admin/questions", methods=["GET"])
def admin_get_questions():
    """Get all questions (admin only)"""
    try:
        all_questions = load_questions()  # Load all questions from questions file
        return jsonify({"questions": all_questions})  # Return questions as JSON response
    except Exception as e:  # Handle loading errors
        return jsonify({"success": False, "message": f"Error retrieving questions: {str(e)}"}), 500

@admin_bp.route("/admin/questions", methods=["POST"])
def admin_add_question():
    """Add a new question (admin only)"""
    try:
        data = request.json  # Get JSON data from request body
        if not data or not data.get("text") or not data.get("keywords"):  # Validate required fields
            return jsonify({"success": False, "message": "Question text and keywords are required"}), 400
        
        all_questions = load_questions()  # Load existing questions
        
        # Generate new ID
        new_id = max([q.get("id", 0) for q in all_questions], default=0) + 1  # Calculate next available ID
        
        new_question = {  # Create new question object
            "id": new_id,  # Set unique question ID
            "text": data["text"],  # Set question text
            "keywords": data["keywords"],  # Set expected keywords
            "active": data.get("active", True)  # Set active status (default to True)
        }
        
        all_questions.append(new_question)  # Add new question to questions list
        save_questions(all_questions)  # Save updated questions to file
        
        return jsonify({"success": True, "message": "Question added successfully", "question": new_question})  # Return success response
    except Exception as e:  # Handle any errors during question addition
        return jsonify({"success": False, "message": f"Error adding question: {str(e)}"}), 500

@admin_bp.route("/admin/questions/<int:question_id>", methods=["PUT"])
def admin_update_question(question_id):
    """Update an existing question (admin only)"""
    try:
        data = request.json  # Get JSON data from request body
        if not data:  # Validate data was provided
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        all_questions = load_questions()  # Load existing questions
        
        # Find the question to update
        question_index = None  # Initialize question index variable
        for i, q in enumerate(all_questions):  # Iterate through all questions
            if q.get("id") == question_id:  # Check if question ID matches
                question_index = i  # Store question index
                break
        
        if question_index is None:  # Check if question was found
            return jsonify({"success": False, "message": "Question not found"}), 404
        
        # Update the question
        if "text" in data:  # Check if text should be updated
            all_questions[question_index]["text"] = data["text"]  # Update question text
        if "keywords" in data:  # Check if keywords should be updated
            all_questions[question_index]["keywords"] = data["keywords"]  # Update keywords
        if "active" in data:  # Check if active status should be updated
            all_questions[question_index]["active"] = data["active"]  # Update active status
        
        save_questions(all_questions)  # Save updated questions to file
        
        return jsonify({"success": True, "message": "Question updated successfully", "question": all_questions[question_index]})  # Return success response
    except Exception as e:  # Handle any errors during question update
        return jsonify({"success": False, "message": f"Error updating question: {str(e)}"}), 500

@admin_bp.route("/admin/questions/<int:question_id>", methods=["DELETE"])
def admin_delete_question(question_id):
    """Delete a question (admin only)"""
    try:
        all_questions = load_questions()  # Load existing questions
        
        # Find the question to delete
        question_index = None  # Initialize question index variable
        for i, q in enumerate(all_questions):  # Iterate through all questions
            if q.get("id") == question_id:  # Check if question ID matches
                question_index = i  # Store question index
                break
        
        if question_index is None:  # Check if question was found
            return jsonify({"success": False, "message": "Question not found"}), 404
        
        # Remove the question
        deleted_question = all_questions.pop(question_index)  # Remove question and store deleted data
        save_questions(all_questions)  # Save updated questions to file
        
        return jsonify({"success": True, "message": "Question deleted successfully", "deleted_question": deleted_question})  # Return success response
    except Exception as e:  # Handle any errors during question deletion
        return jsonify({"success": False, "message": f"Error deleting question: {str(e)}"}), 500

@admin_bp.route("/admin/questions/reload", methods=["POST"])
def admin_reload_questions():
    """Reload questions from file (admin only)"""
    try:
        # This will be handled by the session management
        return jsonify({"success": True, "message": "Questions reloaded successfully"})  # Return success response
    except Exception as e:  # Handle any errors during reload
        return jsonify({"success": False, "message": f"Error reloading questions: {str(e)}"}), 500

@admin_bp.route("/admin/auth", methods=["POST"])
def admin_auth():
    """Admin authentication endpoint"""
    try:
        data = request.json  # Get JSON data from request body
        if not data or not data.get("username") or not data.get("password"):  # Validate required fields
            return jsonify({"success": False, "message": "Username and password required"}), 400
        
        # Check credentials
        if data["username"] == ADMIN_USERNAME and data["password"] == ADMIN_PASSWORD:  # Validate admin credentials
            return jsonify({"success": True, "message": "Authentication successful"})  # Return success response
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401  # Return authentication failure
            
    except Exception as e:  # Handle any authentication errors
        return jsonify({"success": False, "message": f"Authentication error: {str(e)}"}), 500

@admin_bp.route("/admin/applicants/<session_id>", methods=["DELETE"])
def admin_delete_applicant(session_id):
    """Delete an applicant (admin only)"""
    try:
        print(f"Attempting to delete applicant with session_id: {session_id}")  # Log deletion attempt
        
        # Load existing applicants data
        applicants_data = load_applicants()  # Load current applicants data
        
        # Find and remove the applicant
        original_count = len(applicants_data["applicants"])  # Store original applicant count
        applicants_data["applicants"] = [  # Filter out the applicant to delete
            applicant for applicant in applicants_data["applicants"] 
            if applicant.get("id") != session_id  # Keep applicants that don't match session ID
        ]
        
        # Check if applicant was found and removed
        if len(applicants_data["applicants"]) == original_count:  # Check if no applicant was removed
            print(f"Applicant {session_id} not found in applicants.json")  # Log that applicant wasn't found
            # Check if it exists in temporary files
            temp_applicant_file = f"data/temp_applicant_{session_id}.json"  # Generate temporary applicant file path
            if os.path.exists(temp_applicant_file):  # Check if temporary file exists
                print(f"Found temporary applicant file: {temp_applicant_file}")  # Log temporary file found
                try:
                    os.remove(temp_applicant_file)  # Delete temporary applicant file
                    print(f"Deleted temporary applicant file: {temp_applicant_file}")  # Log file deletion
                    
                    # Also try to delete corresponding evaluation file
                    temp_eval_file = f"data/temp_evaluation_{session_id}.json"  # Generate temporary evaluation file path
                    if os.path.exists(temp_eval_file):  # Check if evaluation file exists
                        os.remove(temp_eval_file)  # Delete temporary evaluation file
                        print(f"Deleted temporary evaluation file: {temp_eval_file}")  # Log evaluation file deletion
                    
                    # Clean up recordings
                    cleanup_recordings(session_id)  # Remove applicant's audio recordings
                    
                    return jsonify({"success": True, "message": "Temporary applicant deleted successfully"})  # Return success response
                except Exception as e:  # Handle temporary file deletion errors
                    print(f"Error deleting temporary files: {e}")  # Log deletion error
                    return jsonify({"success": False, "message": f"Error deleting temporary applicant: {str(e)}"}), 500
            else:
                return jsonify({"success": False, "message": f"Applicant with ID '{session_id}' not found"}), 404  # Return not found error
        
        # Save updated applicants data
        save_applicants(applicants_data)  # Save updated applicants list to file
        
        # Clean up temporary files and recordings
        cleanup_temp_files(session_id)  # Remove temporary data files
        cleanup_recordings(session_id)  # Remove audio recordings
        
        # Clear session state
        clear_session(session_id)  # Clear session data from memory
        
        print(f"Deleted applicant {session_id}")  # Log successful deletion
        return jsonify({"success": True, "message": "Applicant deleted successfully"})  # Return success response
        
    except Exception as e:  # Handle any errors during applicant deletion
        print(f"Error in admin_delete_applicant: {e}")  # Log error details
        return jsonify({"success": False, "message": f"Error deleting applicant: {str(e)}"}), 500 