from flask import Blueprint, jsonify, request
from datetime import datetime
from utils.file_ops import (
    save_temp_applicant, load_temp_applicant, load_temp_evaluation,
    load_applicants, save_applicants, cleanup_temp_files, cleanup_recordings
)
from utils.session import clear_session

applicant_bp = Blueprint('applicant', __name__)

@applicant_bp.route("/store_applicant", methods=["POST"])
def store_applicant():
    """Store applicant data temporarily for later combination with evaluation"""
    try:
        applicant_data = request.get_json()  # Get applicant data from request body
        if not applicant_data:  # Check if data was provided
            return jsonify({"success": False, "message": "No applicant data provided"}), 400

        # Store in a temporary file named with session ID
        session_id = applicant_data.get('sessionId')  # Extract session ID from data
        if not session_id:  # Validate session ID exists
            return jsonify({"success": False, "message": "Session ID required"}), 400

        # Validate required fields in the new comprehensive format
        applicant_info = applicant_data.get('applicant', {})
        required_fields = ['positionApplied', 'lastName', 'firstName', 'email', 'dateOfBirth', 'gender', 'civilStatus']
        
        missing_fields = []
        for field in required_fields:
            if not applicant_info.get(field, '').strip():
                missing_fields.append(field)
        
        if missing_fields:
            return jsonify({
                "success": False, 
                "message": f"Missing required fields: {', '.join(missing_fields)}"
            }), 400

        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, applicant_info.get('email', '')):
            return jsonify({"success": False, "message": "Invalid email format"}), 400

        # Override client timestamp with server UTC timestamp to ensure consistency
        applicant_data['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Save to temporary storage
        if not save_temp_applicant(applicant_data, session_id):
            return jsonify({"success": False, "message": "Failed to save applicant data"}), 500

        print(f"Stored comprehensive applicant data for session {session_id}")
        print(f"  - Position: {applicant_info.get('positionApplied', 'N/A')}")
        print(f"  - Name: {applicant_info.get('lastName', '')}, {applicant_info.get('firstName', '')}")
        print(f"  - Email: {applicant_info.get('email', 'N/A')}")
        print(f"  - Work History entries: {len(applicant_info.get('workHistory', []))}")

        return jsonify({"success": True, "message": "Applicant data stored successfully"})

    except Exception as e:  # Handle any errors during storage
        return jsonify({"success": False, "message": f"Error storing applicant data: {str(e)}"}), 500

@applicant_bp.route("/finish_evaluation", methods=["POST"])
def finish_evaluation():
    """Handle evaluation completion and save all results to applicants.json"""
    try:
        session_id = request.json.get("session_id") if request.is_json else None  # Extract session ID from request

        if session_id:  # Check if session ID was provided
            # Load temporary applicant data
            applicant_data = load_temp_applicant(session_id)  # Load stored applicant information
            evaluation_data = load_temp_evaluation(session_id)  # Load stored evaluation results

            if applicant_data and evaluation_data:  # Check if both data sets exist
                # Load existing applicants data
                applicants_data = load_applicants()  # Load current applicants from file

                # Create combined record with all evaluations
                combined_record = {  # Combine applicant and evaluation data
                    "id": session_id,  # Use session ID as unique identifier
                    "applicant_info": applicant_data.get('applicant', {}),  # Extract applicant details
                    "application_timestamp": applicant_data.get('timestamp'),  # Get application time
                    "total_questions": 0,  # Will calculate total from all sections
                    "completion_timestamp": datetime.utcnow().isoformat() + 'Z',  # Record completion time in UTC
                    "last_updated": datetime.utcnow().isoformat() + 'Z',  # Update timestamp in UTC
                    "comments": []  # Initialize empty comments array
                }
                
                # Handle both old and new segmented structure
                if "evaluations" in evaluation_data:
                    # Old format - use directly
                    combined_record["evaluations"] = evaluation_data.get("evaluations", [])
                    combined_record["total_questions"] = len(evaluation_data.get("evaluations", []))
                else:
                    # New segmented format - preserve the structure
                    combined_record.update(evaluation_data)  # Keep the segmented structure
                    # Calculate total questions from all sections
                    total_questions = 0
                    total_questions += len(evaluation_data.get("speech_eval", []))
                    total_questions += len(evaluation_data.get("listening_test", []))
                    total_questions += len(evaluation_data.get("written_test", []))
                    total_questions += len(evaluation_data.get("personality_test", []))
                    total_questions += len(evaluation_data.get("typing_test", []))
                    combined_record["total_questions"] = total_questions

                # Check if applicant already exists (by session_id)
                existing_index = None  # Track if applicant exists
                for i, applicant in enumerate(applicants_data["applicants"]):  # Search existing applicants
                    if applicant.get("id") == session_id:  # Check for matching session ID
                        existing_index = i  # Store index of existing applicant
                        break

                if existing_index is not None:  # If applicant exists
                    # Preserve existing comments when updating
                    existing_comments = applicants_data["applicants"][existing_index].get("comments", [])
                    combined_record["comments"] = existing_comments
                    # Update existing applicant with all evaluations
                    applicants_data["applicants"][existing_index] = combined_record  # Replace with updated data
                else:  # If new applicant
                    # Add new applicant
                    applicants_data["applicants"].append(combined_record)  # Add to applicants list

                # Save to applicants.json
                if not save_applicants(applicants_data):
                    return jsonify({
                        "success": False, 
                        "message": "Failed to save applicant data to database"
                    }), 500

                # Clean up temporary files
                cleanup_temp_files(session_id)  # Remove temporary files

                applicant_info = combined_record.get("applicant_info", {})
                print(f"Completed evaluation for applicant {session_id}")
                print(f"  - Name: {applicant_info.get('lastName', '')}, {applicant_info.get('firstName', '')}")
                print(f"  - Position: {applicant_info.get('positionApplied', 'N/A')}")
                if "evaluations" in evaluation_data:
                    print(f"  - Total evaluations: {len(evaluation_data.get('evaluations', []))}")
                else:
                    print(f"  - Speech evaluations: {len(evaluation_data.get('speech_eval', []))}")
                    print(f"  - Listening tests: {len(evaluation_data.get('listening_test', []))}")
                    print(f"  - Written tests: {len(evaluation_data.get('written_test', []))}")
                    print(f"  - Personality tests: {len(evaluation_data.get('personality_test', []))}")
                    print(f"  - Typing tests: {len(evaluation_data.get('typing_test', []))}")
                    print(f"  - Total: {combined_record['total_questions']}")

        # Mark all tests as completed before clearing session
        try:
            from utils.session import mark_test_completed
            mark_test_completed(session_id, 'listening')
            mark_test_completed(session_id, 'written')
            mark_test_completed(session_id, 'speech')
            mark_test_completed(session_id, 'personality')
            mark_test_completed(session_id, 'typing')
            print(f"All tests marked as completed for session {session_id}")
        except Exception as e:
            print(f"Warning: Could not mark tests as completed: {str(e)}")

        # Clear session state for this session
        clear_session(session_id)  # Clean up session memory

        return jsonify({"success": True, "message": "Evaluation completed successfully"})
    except Exception as e:  # Handle any errors during completion
        return jsonify({"success": False, "message": str(e)}), 500

@applicant_bp.route("/get_applicants", methods=["GET"])
def get_applicants():
    """Retrieve all stored applicants data including temporary applicants"""
    try:
        # Load permanent applicants from MongoDB
        applicants_data = load_applicants()  # Load applicants from database
        
        # Load temporary applicants and convert them to the same format
        from utils.file_ops import load_all_temp_applicants, load_temp_evaluation, load_temp_comments
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
                total_questions += len(eval_data.get("personality_test", []))
                total_questions += len(eval_data.get("typing_test", []))
                formatted_applicant["total_questions"] = total_questions
                
                # Ensure all test segments are present
                for segment in ["speech_eval", "listening_test", "written_test", "personality_test", "typing_test"]:
                    if segment not in formatted_applicant:
                        formatted_applicant[segment] = []
            else:
                # Initialize empty evaluation segments if no evaluations exist
                formatted_applicant.update({
                    "speech_eval": [],
                    "listening_test": [],
                    "written_test": [],
                    "personality_test": [],
                    "typing_test": []
                })
            
            temp_applicants_formatted.append(formatted_applicant)
        
        # Mark permanent applicants with status
        for applicant in applicants_data.get("applicants", []):
            if "status" not in applicant:
                applicant["status"] = "permanent"
        
        # Combine permanent and temporary applicants
        all_applicants = {
            "applicants": applicants_data.get("applicants", []) + temp_applicants_formatted
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
        
        return jsonify(all_applicants)  # Return combined applicants data as JSON
    except Exception as e:  # Handle any errors during retrieval
        return jsonify({"success": False, "message": f"Error retrieving applicants: {str(e)}"}), 500

@applicant_bp.route("/get_applicant_details", methods=["GET"])
def get_applicant_details():
    """Retrieve detailed information for a specific applicant"""
    try:
        applicant_id = request.args.get("id")  # Get applicant ID from query params
        
        if not applicant_id:  # Validate applicant ID exists
            return jsonify({"success": False, "message": "Applicant ID required"}), 400
        
        # Use the admin function to find applicant in both permanent and temporary storage
        from routes.admin import find_applicant_data
        applicant, storage_type, _ = find_applicant_data(applicant_id)
        
        if not applicant:
            return jsonify({"success": False, "message": "Applicant not found"}), 404
        
        return jsonify({
            "success": True,
            "applicant": applicant,
            "storage_type": storage_type  # Let frontend know if this is temporary
        })
        
    except Exception as e:  # Handle any errors during retrieval
        return jsonify({"success": False, "message": f"Error retrieving applicant details: {str(e)}"}), 500

@applicant_bp.route("/get_test_completion_status", methods=["GET"])
def get_test_completion_status():
    """Get the completion status of all tests for a session"""
    try:
        session_id = request.args.get("session_id")  # Get session ID from query params
        
        if not session_id:  # Validate session ID exists
            return jsonify({"success": False, "message": "Session ID required"}), 400
        
        # Import here to avoid circular imports
        from utils.session import get_test_completion_status as get_session_test_status
        
        completion_status = get_session_test_status(session_id)  # Get completion status
        
        return jsonify({
            "success": True,
            "completion_status": completion_status
        })
        
    except Exception as e:  # Handle any errors
        return jsonify({"success": False, "message": f"Error getting test completion status: {str(e)}"}), 500

@applicant_bp.route("/mark_test_completed", methods=["POST"])
def mark_test_completed():
    """Mark a specific test as completed for a session"""
    try:
        data = request.get_json()  # Get JSON data from request
        
        if not data:  # Validate request data exists
            return jsonify({"success": False, "message": "Request data required"}), 400
        
        session_id = data.get("session_id")  # Get session ID from request data
        test_type = data.get("test_type")  # Get test type from request data
        
        if not session_id or not test_type:  # Validate required fields
            return jsonify({"success": False, "message": "Session ID and test type required"}), 400
        
        # Validate test type
        valid_test_types = ['listening', 'written', 'speech', 'personality', 'typing']
        if test_type not in valid_test_types:
            return jsonify({"success": False, "message": f"Invalid test type. Must be one of: {valid_test_types}"}), 400
        
        # Import here to avoid circular imports
        from utils.session import mark_test_completed as mark_session_test_completed
        
        mark_session_test_completed(session_id, test_type)  # Mark test as completed
        
        return jsonify({
            "success": True,
            "message": f"{test_type} test marked as completed for session {session_id}"
        })
        
    except Exception as e:  # Handle any errors
        return jsonify({"success": False, "message": f"Error marking test as completed: {str(e)}"}), 500 