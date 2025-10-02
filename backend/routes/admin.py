from flask import Blueprint, jsonify, request
import os
from config import ADMIN_USERNAME, ADMIN_PASSWORD
from utils.file_ops import (
    load_applicants, save_applicants, load_questions, save_questions, 
    load_listening_test_questions, save_listening_test_questions,
    cleanup_temp_files, cleanup_recordings, load_temp_applicant, load_temp_evaluation,
    save_temp_comments, load_temp_comments, load_all_temp_applicants
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
            # Add status field if not present
            if "status" not in app:
                app["status"] = "permanent"
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
            "total_questions": 0,  # Will calculate from evaluations
            "completion_timestamp": None,
            "last_updated": temp_applicant.get("timestamp"),
            "comments": load_temp_comments(applicant_id),  # Load temp comments
            "status": "temporary"  # Mark as temporary
        }
        
        # Try to load corresponding evaluation data
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
                total_questions += len(eval_data.get("written_test", []))
                total_questions += len(eval_data.get("personality_test", []))
                total_questions += len(eval_data.get("typing_test", []))
                applicant_entry["total_questions"] = total_questions
                
                # Ensure all test segments are present
                for segment in ["speech_eval", "listening_test", "written_test", "personality_test", "typing_test"]:
                    if segment not in applicant_entry:
                        applicant_entry[segment] = []
        else:
            # Initialize empty evaluation segments if no evaluations exist
            applicant_entry.update({
                "speech_eval": [],
                "listening_test": [],
                "written_test": [],
                "personality_test": [],
                "typing_test": []
            })
        
        return applicant_entry, "temporary", None
    
    return None, None, None

@admin_bp.route("/admin/applicants", methods=["GET"])
@require_permission("view_applicants")  # Re-enabled authentication
def admin_get_applicants():
    """Admin endpoint to retrieve all applicants data including temporary applicants"""
    try:
        # Load permanent applicants from MongoDB
        main_applicants = load_applicants()  # Now loads from MongoDB
        
        # Load temporary applicants and convert them to the same format
        temp_applicants_raw = load_all_temp_applicants()
        temp_applicants_formatted = []
        
        for temp_applicant in temp_applicants_raw:
            session_id = temp_applicant.get("sessionId")
            
            # Convert temp applicant to permanent applicant format
            formatted_applicant = {
                "id": session_id,
                "applicant_info": temp_applicant.get("applicant", {}),
                "application_timestamp": temp_applicant.get("timestamp"),
                "completion_timestamp": None,  # Not completed yet
                "last_updated": temp_applicant.get("timestamp"),
                "total_questions": 0,  # Will calculate from evaluations
                "comments": load_temp_comments(session_id),
                "status": "temporary"  # Mark as temporary for frontend
            }
            
            # Try to load corresponding evaluation data
            eval_data = load_temp_evaluation(session_id)
            if eval_data:
                # Handle segmented evaluation structure
                formatted_applicant.update(eval_data)
                # Calculate total questions from all test segments
                total_questions = 0
                total_questions += len(eval_data.get("speech_eval", []))
                total_questions += len(eval_data.get("listening_test", []))
                total_questions += len(eval_data.get("written_test", []))
                total_questions += len(eval_data.get("typing_test", []))
                formatted_applicant["total_questions"] = total_questions
                
                # Ensure all test segments are present
                for segment in ["speech_eval", "listening_test", "written_test", "typing_test"]:
                    if segment not in formatted_applicant:
                        formatted_applicant[segment] = []
            else:
                # Initialize empty evaluation segments if no evaluations exist
                formatted_applicant.update({
                    "speech_eval": [],
                    "listening_test": [],
                    "written_test": [],
                    "typing_test": []
                })
            
            temp_applicants_formatted.append(formatted_applicant)
        
        # Mark permanent applicants with status
        for applicant in main_applicants.get("applicants", []):
            applicant["status"] = "permanent"
        
        # Combine permanent and temporary applicants
        all_applicants = {
            "applicants": main_applicants.get("applicants", []) + temp_applicants_formatted
        }
        
        # Sort applicants by application timestamp (newest first)
        # Use application_timestamp to maintain chronological order of when applicants started
        def get_sort_timestamp(applicant):
            # Prioritize application_timestamp to sort by when applicant started, not completed
            if applicant.get("application_timestamp"):
                return applicant["application_timestamp"]
            elif applicant.get("last_updated"):
                return applicant["last_updated"]
            else:
                return "1970-01-01T00:00:00.000Z"  # Very old date for items without timestamps
        
        all_applicants["applicants"].sort(key=get_sort_timestamp, reverse=True)
        
        return jsonify(all_applicants)
    except Exception as e:
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
        if not save_questions(all_questions):  # Save updated questions to database
            return jsonify({"success": False, "message": "Failed to save question to database"}), 500
        
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
        
        if not save_questions(all_questions):  # Save updated questions to database
            return jsonify({"success": False, "message": "Failed to save question update to database"}), 500
        
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
            # Check if it exists in temporary MongoDB collections
            from utils.file_ops import load_temp_applicant
            temp_applicant_data = load_temp_applicant(session_id)
            if temp_applicant_data:  # Check if temporary data exists in MongoDB
                print(f"Found temporary applicant data in MongoDB for session: {session_id}")  # Log temporary data found
                try:
                    # Clean up temporary data from MongoDB collections
                    cleanup_success = cleanup_temp_files(session_id)
                    if cleanup_success:
                        print(f"Deleted temporary applicant data for session: {session_id}")  # Log data deletion
                    
                    # Clean up recordings
                    cleanup_recordings(session_id)  # Remove applicant's audio recordings
                    
                    return jsonify({"success": True, "message": "Temporary applicant deleted successfully"})  # Return success response
                except Exception as e:  # Handle temporary data deletion errors
                    print(f"Error deleting temporary files: {e}")  # Log deletion error
                    return jsonify({"success": False, "message": f"Error deleting temporary applicant: {str(e)}"}), 500
            else:
                return jsonify({"success": False, "message": f"Applicant with ID '{session_id}' not found"}), 404  # Return not found error
        
        # Save updated applicants data
        save_applicants(applicants_data)
        
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

@admin_bp.route("/admin/applicants/<applicant_id>/status", methods=["PUT"])
@require_permission("edit_applicants")
def update_applicant_status(applicant_id):
    """Update the status of an applicant (new, pending, approved, rejected)"""
    try:
        data = request.get_json()
        new_status = data.get("status")
        
        if not new_status:
            return jsonify({"success": False, "message": "Status is required"}), 400
        
        # Validate status value
        valid_statuses = ['new', 'pending', 'approved', 'rejected', 'temporary', 'permanent']
        if new_status not in valid_statuses:
            return jsonify({"success": False, "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
        
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
            
            # Update the applicant_status in applicant_info
            if "applicant_info" not in applicants_data["applicants"][applicant_index]:
                applicants_data["applicants"][applicant_index]["applicant_info"] = {}
            
            applicants_data["applicants"][applicant_index]["applicant_info"]["applicant_status"] = new_status
            
            # Also update last_updated timestamp
            from datetime import datetime
            applicants_data["applicants"][applicant_index]["last_updated"] = datetime.now().isoformat()
            
            # Save updated applicants data
            if not save_applicants(applicants_data):
                return jsonify({"success": False, "message": "Failed to save applicant status"}), 500
            
        else:  # storage_type == "temporary"
            # For temporary applicants, we need to update the temp file
            temp_applicant = load_temp_applicant(applicant_id)
            if not temp_applicant:
                return jsonify({"success": False, "message": "Temporary applicant not found"}), 404
            
            # Update the applicant_status in applicant data
            if "applicant" not in temp_applicant:
                temp_applicant["applicant"] = {}
            
            temp_applicant["applicant"]["applicant_status"] = new_status
            
            # Save updated temp applicant
            from utils.file_ops import save_temp_applicant
            if not save_temp_applicant(temp_applicant, applicant_id):
                return jsonify({"success": False, "message": "Failed to save temporary applicant status"}), 500
        
        return jsonify({
            "success": True, 
            "message": "Status updated successfully",
            "status": new_status
        })
        
    except Exception as e:
        print(f"Error updating status for applicant {applicant_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error updating status: {str(e)}"}), 500 