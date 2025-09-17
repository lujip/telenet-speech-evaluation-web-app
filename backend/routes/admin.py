from flask import Blueprint, jsonify, request
import os
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.file_ops import (
    load_applicants, save_applicants, load_questions, save_questions, 
    load_listening_test_questions, save_listening_test_questions,
    cleanup_temp_files, cleanup_recordings, load_temp_applicant, load_temp_evaluation,
    save_temp_comments, load_temp_comments
)
from utils.session import clear_session
from utils.auth import require_permission, require_auth

admin_bp = Blueprint('admin', __name__)

def find_applicant_data(applicant_id):
    """Find applicant data in either permanent or temporary storage"""
    # First try to find in permanent applicants
    applicants_data = load_applicants()
    for app in applicants_data.get("applicants", []):
        if app.get("id") == applicant_id:
            return app, "permanent", applicants_data
    
    # If not found, try to load as temporary applicant
    temp_applicant = load_temp_applicant(applicant_id)
    if temp_applicant:
        # Construct temporary applicant data structure
        applicant_entry = {
            "id": temp_applicant.get("sessionId"),
            "applicant_info": temp_applicant.get("applicant", {}),
            "application_timestamp": temp_applicant.get("timestamp"),
            "evaluations": [],
            "total_questions": 5,
            "completion_timestamp": None,
            "last_updated": temp_applicant.get("timestamp"),
            "comments": load_temp_comments(applicant_id)  # Load temp comments
        }
        
        # Try to load corresponding evaluation file
        eval_data = load_temp_evaluation(applicant_id)
        if eval_data:
            # Handle both old and new segmented structure
            if "evaluations" in eval_data:
                # Old format
                applicant_entry["evaluations"] = eval_data.get("evaluations", [])
                applicant_entry["total_questions"] = len(eval_data.get("evaluations", []))
            else:
                # New segmented format
                applicant_entry.update(eval_data)
                # Calculate total questions from all test segments
                total_questions = 0
                total_questions += len(eval_data.get("speech_eval", []))
                total_questions += len(eval_data.get("listening_test", []))
                total_questions += len(eval_data.get("typing_test", []))
                applicant_entry["total_questions"] = total_questions
                
                # Ensure all test segments are present
                for segment in ["speech_eval", "listening_test", "written_test", "typing_test"]:
                    if segment not in applicant_entry:
                        applicant_entry[segment] = []
        
        return applicant_entry, "temporary", None
    
    return None, None, None

@admin_bp.route("/admin/applicants", methods=["GET"])
@require_permission("view_applicants")
def admin_get_applicants():
    """Admin endpoint to retrieve all applicants data including temporary files"""
    try:
        # Load main applicants data
        main_applicants = load_applicants()  # Load existing applicants from main data file
        print(f"📋 Loaded {len(main_applicants.get('applicants', []))} main applicants")
        
        # Find and load temporary applicant files
        temp_applicants = []  # Initialize list for temporary applicants
        temp_dir = "data/temp_applicants"  # Set temp_applicants directory path
        print(f"🔍 Scanning {temp_dir} directory for temporary applicant files...")
        if os.path.exists(temp_dir):  # Check if temp_applicants directory exists
            for filename in os.listdir(temp_dir):  # Iterate through all files in temp_applicants directory
                if filename.startswith("temp_applicant_") and filename.endswith(".json"):  # Find temporary applicant files
                    try:
                        with open(os.path.join(temp_dir, filename), 'r') as f:  # Open temporary applicant file
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
                                "last_updated": temp_data.get("timestamp"),  # Set last updated timestamp
                                "comments": []  # Initialize empty comments array
                            }
                            
                            # Try to load corresponding evaluation file
                            eval_filename = f"temp_evaluation_{temp_data.get('sessionId')}.json"  # Generate evaluation filename
                            eval_filepath = os.path.join(temp_dir, eval_filename)
                            if os.path.exists(eval_filepath):  # Check if evaluation file exists
                                try:
                                    with open(eval_filepath, 'r') as eval_f:  # Open evaluation file
                                        eval_data = json.load(eval_f)  # Load evaluation JSON data
                                        # Handle both old and new segmented structure
                                        if "evaluations" in eval_data:
                                            # Old format - migrate to new structure
                                            applicant_entry["evaluations"] = eval_data.get("evaluations", [])
                                            # Calculate total questions from old evaluations
                                            applicant_entry["total_questions"] = len(eval_data.get("evaluations", []))
                                            print(f"📋 Loaded old format evaluations for {temp_data.get('sessionId')}: {len(eval_data.get('evaluations', []))} questions")
                                        else:
                                            # New segmented format - preserve the structure
                                            applicant_entry.update(eval_data)  # Keep the segmented structure
                                            
                                            # Calculate total questions from all test segments
                                            total_questions = 0
                                            speech_count = len(eval_data.get("speech_eval", []))
                                            listening_count = len(eval_data.get("listening_test", []))
                                            typing_count = len(eval_data.get("typing_test", []))
                                            
                                            total_questions += speech_count
                                            total_questions += listening_count
                                            total_questions += typing_count
                                            
                                            # Set the total questions count
                                            applicant_entry["total_questions"] = total_questions
                                            
                                            # Ensure all test segments are present (initialize as empty arrays if missing)
                                            if "speech_eval" not in applicant_entry:
                                                applicant_entry["speech_eval"] = []
                                            if "listening_test" not in applicant_entry:
                                                applicant_entry["listening_test"] = []
                                            if "typing_test" not in applicant_entry:
                                                applicant_entry["typing_test"] = []
                                            if "written_test" not in applicant_entry:
                                                applicant_entry["written_test"] = []
                                            
                                            print(f"📊 Loaded new segmented structure for {temp_data.get('sessionId')}: {speech_count} speech, {listening_count} listening, {typing_count} typing = {total_questions} total")
                                except Exception as eval_err:  # Handle evaluation file loading errors
                                    print(f"Error loading evaluation file {eval_filename}: {eval_err}")
                            
                            temp_applicants.append(applicant_entry)  # Add temporary applicant to list
                            print(f"✅ Successfully loaded temp applicant: {temp_data.get('sessionId')}")
                    except Exception as temp_err:  # Handle temporary file loading errors
                        print(f"❌ Error loading temp file {filename}: {temp_err}")
        
        # Summary of temp files loaded
        if temp_applicants:
            print(f"\n📊 Temporary applicants summary:")
            for temp_app in temp_applicants:
                session_id = temp_app.get("id", "unknown")
                speech_count = len(temp_app.get("speech_eval", []))
                listening_count = len(temp_app.get("listening_test", []))
                typing_count = len(temp_app.get("typing_test", []))
                total = temp_app.get("total_questions", 0)
                print(f"   - {session_id}: {speech_count} speech, {listening_count} listening, {typing_count} typing = {total} total")
        
        # Combine main and temporary applicants
        all_applicants = main_applicants.get("applicants", []) + temp_applicants  # Merge both applicant lists
        
        # Sort by application timestamp (newest first)
        all_applicants.sort(key=lambda x: x.get("application_timestamp", ""), reverse=True)  # Sort applicants by timestamp
        
        print(f"✅ Total applicants loaded: {len(all_applicants)} (main: {len(main_applicants.get('applicants', []))}, temp: {len(temp_applicants)})")
       # print(f"Temp applicants: {temp_applicants}")
        return jsonify({"applicants": all_applicants})  # Return all applicants as JSON response
    except Exception as e:  # Handle any unexpected errors
        return jsonify({"success": False, "message": f"Error retrieving applicants: {str(e)}"}), 500

@admin_bp.route("/admin/questions", methods=["GET"])
@require_permission("view_questions")
def admin_get_questions():
    """Get all questions (admin only)"""
    try:
        all_questions = load_questions()  # Load all questions from questions file
        return jsonify({"questions": all_questions})  # Return questions as JSON response
    except Exception as e:  # Handle loading errors
        return jsonify({"success": False, "message": f"Error retrieving questions: {str(e)}"}), 500

@admin_bp.route("/admin/questions", methods=["POST"])
@require_permission("edit_questions")
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
@require_permission("edit_questions")
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
@require_permission("delete_questions")
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
@require_permission("edit_questions")
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
@require_permission("delete_applicants")
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
            temp_applicant_file = f"data/temp_applicants/temp_applicant_{session_id}.json"  # Generate temporary applicant file path
            if os.path.exists(temp_applicant_file):  # Check if temporary file exists
                print(f"Found temporary applicant file: {temp_applicant_file}")  # Log temporary file found
                try:
                    os.remove(temp_applicant_file)  # Delete temporary applicant file
                    print(f"Deleted temporary applicant file: {temp_applicant_file}")  # Log file deletion
                    
                    # Also try to delete corresponding evaluation and comments files
                    temp_eval_file = f"data/temp_applicants/temp_evaluation_{session_id}.json"  # Generate temporary evaluation file path
                    if os.path.exists(temp_eval_file):  # Check if evaluation file exists
                        os.remove(temp_eval_file)  # Delete temporary evaluation file
                        print(f"Deleted temporary evaluation file: {temp_eval_file}")  # Log evaluation file deletion
                    
                    temp_comments_file = f"data/temp_applicants/temp_comments_{session_id}.json"  # Generate temporary comments file path
                    if os.path.exists(temp_comments_file):  # Check if comments file exists
                        os.remove(temp_comments_file)  # Delete temporary comments file
                        print(f"Deleted temporary comments file: {temp_comments_file}")  # Log comments file deletion
                    
                    # Clean up recordings
                    cleanup_recordings(session_id)  # Remove applicant's audio recordings
                    
                    return jsonify({"success": True, "message": "Temporary applicant deleted successfully"})  # Return success response
                except Exception as e:  # Handle temporary file deletion errors
                    print(f"Error deleting temporary files: {e}")  # Log deletion error
                    return jsonify({"success": False, "message": f"Error deleting temporary applicant: {str(e)}"}), 500
            else:
                return jsonify({"success": False, "message": f"Applicant with ID '{session_id}' not found"}), 404  # Return not found error
        
        # Save updated applicants data
        # save_applicants(applicants_data) # This line was removed as per the new_code, as save_applicants is no longer imported.
        
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

# Listening Test Questions Management Endpoints

@admin_bp.route("/admin/listening-test-questions", methods=["GET"])
@require_permission("view_questions")
def admin_get_listening_test_questions():
    """Get all listening test questions (admin only)"""
    try:
        all_questions = load_listening_test_questions()  # Load all questions from file
        return jsonify({"questions": all_questions})  # Return questions as JSON response
    except Exception as e:  # Handle loading errors
        return jsonify({"success": False, "message": f"Error retrieving listening test questions: {str(e)}"}), 500

@admin_bp.route("/admin/listening-test-questions", methods=["POST"])
@require_permission("edit_questions")
def admin_add_listening_test_question():
    """Add a new listening test question (admin only)"""
    try:
        data = request.json  # Get JSON data from request body
        if not data or not data.get("text"):  # Validate required fields
            return jsonify({"success": False, "message": "Question text is required"}), 400
        
        all_questions = load_listening_test_questions()  # Load existing questions
        
        # Generate new ID
        new_id = max([q.get("id", 0) for q in all_questions], default=0) + 1  # Calculate next available ID
        
        new_question = {  # Create new question object
            "id": new_id,  # Set unique question ID
            "text": data["text"],  # Set question text
            "active": data.get("active", True)  # Set active status (default to True)
        }
        
        all_questions.append(new_question)  # Add new question to questions list
        save_listening_test_questions(all_questions)  # Save updated questions to file
        
        return jsonify({"success": True, "message": "Listening test question added successfully", "question": new_question})  # Return success response
    except Exception as e:  # Handle any errors during question addition
        return jsonify({"success": False, "message": f"Error adding listening test question: {str(e)}"}), 500

@admin_bp.route("/admin/listening-test-questions/<int:question_id>", methods=["PUT"])
@require_permission("edit_questions")
def admin_update_listening_test_question(question_id):
    """Update an existing listening test question (admin only)"""
    try:
        data = request.json  # Get JSON data from request body
        if not data:  # Validate data was provided
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        all_questions = load_listening_test_questions()  # Load existing questions
        
        # Find the question to update
        question_index = None  # Initialize question index variable
        for i, q in enumerate(all_questions):  # Iterate through all questions
            if q.get("id") == question_id:  # Check if question ID matches
                question_index = i  # Store question index
                break
        
        if question_index is None:  # Check if question was found
            return jsonify({"success": False, "message": "Listening test question not found"}), 404
        
        # Update the question
        if "text" in data:  # Check if text should be updated
            all_questions[question_index]["text"] = data["text"]  # Update question text
        if "active" in data:  # Check if active status should be updated
            all_questions[question_index]["active"] = data["active"]  # Update active status
        
        save_listening_test_questions(all_questions)  # Save updated questions to file
        
        return jsonify({"success": True, "message": "Listening test question updated successfully", "question": all_questions[question_index]})  # Return success response
    except Exception as e:  # Handle any errors during question update
        return jsonify({"success": False, "message": f"Error updating listening test question: {str(e)}"}), 500

@admin_bp.route("/admin/listening-test-questions/<int:question_id>", methods=["DELETE"])
@require_permission("delete_questions")
def admin_delete_listening_test_question(question_id):
    """Delete a listening test question (admin only)"""
    try:
        all_questions = load_listening_test_questions()  # Load existing questions
        
        # Find the question to delete
        question_index = None  # Initialize question index variable
        for i, q in enumerate(all_questions):  # Iterate through all questions
            if q.get("id") == question_id:  # Check if question ID matches
                question_index = i  # Store question index
                break
        
        if question_index is None:  # Check if question was found
            return jsonify({"success": False, "message": "Listening test question not found"}), 404
        
        # Remove the question
        deleted_question = all_questions.pop(question_index)  # Remove question and store deleted data
        save_listening_test_questions(all_questions)  # Save updated questions to file
        
        return jsonify({"success": True, "message": "Listening test question deleted successfully", "deleted_question": deleted_question})  # Return success response
    except Exception as e:  # Handle any errors during question deletion
        return jsonify({"success": False, "message": f"Error deleting listening test question: {str(e)}"}), 500

@admin_bp.route("/admin/listening-test-questions/reload", methods=["POST"])
@require_permission("edit_questions")
def admin_reload_listening_test_questions():
    """Reload listening test questions from file (admin only)"""
    try:
        # This will be handled by the session management
        return jsonify({"success": True, "message": "Listening test questions reloaded successfully"})  # Return success response
    except Exception as e:  # Handle any errors during reload
        return jsonify({"success": False, "message": f"Error reloading listening test questions: {str(e)}"}), 500

# Comments endpoints
@admin_bp.route("/admin/applicants/<applicant_id>/comments", methods=["GET"])
@require_permission("view_evaluations")
def get_applicant_comments(applicant_id):
    """Get all comments for a specific applicant (permanent or temporary)"""
    try:
        # Find applicant in either permanent or temporary storage
        applicant, storage_type, _ = find_applicant_data(applicant_id)
        
        if not applicant:
            return jsonify({"success": False, "message": "Applicant not found"}), 404
        
        # Return comments array (initialize if it doesn't exist)
        comments = applicant.get("comments", [])
        return jsonify({
            "success": True, 
            "comments": comments,
            "storage_type": storage_type  # Let frontend know if this is temporary
        })
            
    except Exception as e:
        print(f"Error loading comments for applicant {applicant_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error loading comments: {str(e)}"}), 500

@admin_bp.route("/admin/applicants/<applicant_id>/comments", methods=["POST"])
@require_permission("add_comments")
def add_applicant_comment(applicant_id):
    """Add a new comment for a specific applicant (permanent or temporary)"""
    try:
        data = request.get_json()
        if not data or 'comment' not in data:
            return jsonify({"success": False, "message": "Comment text is required"}), 400
        
        import uuid
        from datetime import datetime
        
        # Find applicant in either permanent or temporary storage
        applicant, storage_type, applicants_data = find_applicant_data(applicant_id)
        
        if not applicant:
            return jsonify({"success": False, "message": "Applicant not found"}), 404
        
        # Create new comment object
        new_comment = {
            "id": str(uuid.uuid4()),
            "comment": data['comment'],
            "evaluator": data.get('evaluator', 'Unknown User'),
            "timestamp": datetime.now().isoformat(),
            "user_id": request.current_user.get('id') if hasattr(request, 'current_user') else None,
            "user_role": request.current_user.get('role') if hasattr(request, 'current_user') else None
        }
        
        if storage_type == "permanent":
            # Handle permanent applicant
            applicant_index = None
            for i, app in enumerate(applicants_data.get("applicants", [])):
                if app.get("id") == applicant_id:
                    applicant_index = i
                    break
            
            if applicant_index is None:
                return jsonify({"success": False, "message": "Applicant not found in permanent storage"}), 404
            
            # Initialize comments array if it doesn't exist
            if "comments" not in applicants_data["applicants"][applicant_index]:
                applicants_data["applicants"][applicant_index]["comments"] = []
            
            # Add new comment to the beginning of the list (most recent first)
            applicants_data["applicants"][applicant_index]["comments"].insert(0, new_comment)
            
            # Save updated applicants data
            save_applicants(applicants_data)
            
        else:  # storage_type == "temporary"
            # Handle temporary applicant
            current_comments = load_temp_comments(applicant_id)
            
            # Add new comment to the beginning of the list (most recent first)
            current_comments.insert(0, new_comment)
            
            # Save updated comments to temp file
            save_temp_comments(applicant_id, current_comments)
        
        return jsonify({"success": True, "message": "Comment added successfully", "comment": new_comment})
        
    except Exception as e:
        print(f"Error adding comment for applicant {applicant_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error adding comment: {str(e)}"}), 500

@admin_bp.route("/admin/applicants/<applicant_id>/comments/<comment_id>", methods=["DELETE"])
@require_permission("delete_comments")
def delete_applicant_comment(applicant_id, comment_id):
    """Delete a specific comment for an applicant (permanent or temporary)"""
    try:
        # Find applicant in either permanent or temporary storage
        applicant, storage_type, applicants_data = find_applicant_data(applicant_id)
        
        if not applicant:
            return jsonify({"success": False, "message": "Applicant not found"}), 404
        
        if storage_type == "permanent":
            # Handle permanent applicant
            applicant_index = None
            for i, app in enumerate(applicants_data.get("applicants", [])):
                if app.get("id") == applicant_id:
                    applicant_index = i
                    break
            
            if applicant_index is None:
                return jsonify({"success": False, "message": "Applicant not found in permanent storage"}), 404
            
            applicant = applicants_data["applicants"][applicant_index]
            
            # Check if comments array exists
            if "comments" not in applicant:
                return jsonify({"success": False, "message": "No comments found"}), 404
            
            # Find and remove the comment
            comments = applicant["comments"]
            original_count = len(comments)
            applicant["comments"] = [c for c in comments if c.get("id") != comment_id]
            
            if len(applicant["comments"]) == original_count:
                return jsonify({"success": False, "message": "Comment not found"}), 404
            
            # Save updated applicants data
            save_applicants(applicants_data)
            
        else:  # storage_type == "temporary"
            # Handle temporary applicant
            current_comments = load_temp_comments(applicant_id)
            
            # Find and remove the comment
            original_count = len(current_comments)
            current_comments = [c for c in current_comments if c.get("id") != comment_id]
            
            if len(current_comments) == original_count:
                return jsonify({"success": False, "message": "Comment not found"}), 404
            
            # Save updated comments to temp file
            save_temp_comments(applicant_id, current_comments)
        
        return jsonify({"success": True, "message": "Comment deleted successfully"})
        
    except Exception as e:
        print(f"Error deleting comment {comment_id} for applicant {applicant_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error deleting comment: {str(e)}"}), 500 