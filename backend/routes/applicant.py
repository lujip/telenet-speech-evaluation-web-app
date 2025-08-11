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

        save_temp_applicant(applicant_data, session_id)  # Save to temporary file

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
                    "evaluations": evaluation_data.get('evaluations', []),  # Get all evaluation results
                    "total_questions": len(evaluation_data.get('evaluations', [])),  # Count total questions
                    "completion_timestamp": datetime.now().isoformat(),  # Record completion time
                    "last_updated": datetime.now().isoformat()  # Update timestamp
                }

                # Check if applicant already exists (by session_id)
                existing_index = None  # Track if applicant exists
                for i, applicant in enumerate(applicants_data["applicants"]):  # Search existing applicants
                    if applicant.get("id") == session_id:  # Check for matching session ID
                        existing_index = i  # Store index of existing applicant
                        break

                if existing_index is not None:  # If applicant exists
                    # Update existing applicant with all evaluations
                    applicants_data["applicants"][existing_index] = combined_record  # Replace with updated data
                else:  # If new applicant
                    # Add new applicant
                    applicants_data["applicants"].append(combined_record)  # Add to applicants list

                # Save to applicants.json
                save_applicants(applicants_data)  # Persist updated data to file

                # Clean up temporary files
                cleanup_temp_files(session_id)  # Remove temporary files

                print(f"Completed evaluation for applicant {session_id} with {len(evaluation_data.get('evaluations', []))} questions")

        # Clear session state for this session
        clear_session(session_id)  # Clean up session memory

        return jsonify({"success": True, "message": "Evaluation completed successfully"})
    except Exception as e:  # Handle any errors during completion
        return jsonify({"success": False, "message": str(e)}), 500

@applicant_bp.route("/get_applicants", methods=["GET"])
def get_applicants():
    """Retrieve all stored applicants data"""
    try:
        applicants_data = load_applicants()  # Load all applicants from file
        return jsonify(applicants_data)  # Return applicants data as JSON
    except Exception as e:  # Handle any errors during retrieval
        return jsonify({"success": False, "message": f"Error retrieving applicants: {str(e)}"}), 500 