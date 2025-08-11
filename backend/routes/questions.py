from flask import Blueprint, jsonify, request
from utils.session import (
    get_active_questions_for_session, get_session_state, set_session_state,
    get_current_question_for_session, move_to_next_question, 
    mark_question_answered, get_question_status, reset_session_questions
)
from utils.tts import speak_async

questions_bp = Blueprint('questions', __name__)

@questions_bp.route("/question", methods=["GET"])
def get_current_question():
    """Get current question for a session"""
    # Get session ID from query parameters
    session_id = request.args.get("session_id")  # Extract session ID from query params
    
    if not session_id:  # Validate session ID exists
        return jsonify({"text": "Session ID required", "keywords": []}), 400
    
    # Get session-specific questions and state
    questions = get_active_questions_for_session(session_id)  # Load questions for this session
    state = get_session_state(session_id)  # Get current session state
    current_index = state['current_index']  # Get current question index
    
    print(f"DEBUG: Session {session_id} - Loaded {len(questions)} active questions")  # Debug logging
    print(f"DEBUG: Session {session_id} - Current index: {current_index}")
    
    if not questions or len(questions) == 0:  # Check if questions exist
        print("DEBUG: No active questions found")
        return jsonify({"text": "No questions available", "keywords": []})
    
    # Get current question
    current_question = get_current_question_for_session(session_id)  # Get current question data
    if current_question:  # Check if question exists
        print(f"DEBUG: Session {session_id} - Returning question {current_index + 1}: {current_question['text'][:50]}...")
        return jsonify(current_question)  # Return current question as JSON
    else:  # If no current question
        print(f"DEBUG: Session {session_id} - No current question available")
        return jsonify({"text": "No questions available", "keywords": []})

@questions_bp.route("/question_count", methods=["GET"])
def get_question_count():
    """Get question count for a session"""
    # Get session ID from query parameters
    session_id = request.args.get("session_id")  # Extract session ID from query params
    
    if not session_id:  # Validate session ID exists
        return jsonify({"total": 0, "current": 0}), 400
    
    # Get session-specific questions and state
    questions = get_active_questions_for_session(session_id)  # Load questions for this session
    state = get_session_state(session_id)  # Get current session state
    current_index = state['current_index']  # Get current question index
    
    return jsonify({  # Return question count information
        "total": len(questions),  # Total number of questions in session
        "current": current_index  # Current question index (0-based)
    })

@questions_bp.route("/reset_questions", methods=["POST"])
def reset_questions():
    """Reset questions for a session"""
    # Get session ID from request
    session_id = request.json.get("session_id") if request.is_json else None  # Extract session ID from request body
    
    if not session_id:  # Validate session ID exists
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    # Reset session questions
    reset_session_questions(session_id)  # Reset question index and answered tracking
    
    # Get session-specific questions
    questions = get_active_questions_for_session(session_id)  # Load questions for this session
    state = get_session_state(session_id)  # Get current session state
    
    print(f"DEBUG: Session {session_id} - Resetting questions, new index: {state['current_index']}")  # Debug logging
    print(f"DEBUG: Session {session_id} - Loaded {len(questions)} active questions after reset")
    
    if questions and len(questions) > 0:  # Check if questions exist after reset
        current_question = get_current_question_for_session(session_id)  # Get first question
        if current_question:  # Verify question data exists
            print(f"DEBUG: Session {session_id} - Reset successful, first question: {current_question['text'][:50]}...")
            return jsonify({  # Return success with first question
                "success": True, 
                "message": "Questions reset to beginning",
                "question": current_question
            })
    
    print(f"DEBUG: Session {session_id} - No active questions available for reset")
    return jsonify({"success": False, "message": "No active questions available"})  # Return error if no questions

@questions_bp.route("/next_question", methods=["POST"])
def next_question():
    """Move to next question for a session"""
    # Get session ID from request
    session_id = request.json.get("session_id") if request.is_json else None  # Extract session ID from request body
    
    if not session_id:  # Validate session ID exists
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    # Get session-specific questions and state
    questions = get_active_questions_for_session(session_id)  # Load questions for this session
    state = get_session_state(session_id)  # Get current session state
    current_index = state['current_index']  # Get current question index
    
    if not questions or len(questions) == 0:  # Check if questions exist
        return jsonify({  # Return error if no questions available
            "success": False, 
            "message": "No active questions available.",
            "currentIndex": current_index
        })
    
    # Try to move to next question
    if move_to_next_question(session_id):  # Attempt to advance to next question
        # Get new current question
        current_question = get_current_question_for_session(session_id)  # Get next question data
        
        # Speak the question
        speak_async(current_question["text"])  # Use TTS to speak the question
        
        return jsonify({  # Return success with next question
            "success": True, 
            "question": current_question,
            "currentIndex": state['current_index']
        })
    else:  # If no more questions
        return jsonify({  # Return error indicating no more questions
            "success": False, 
            "message": "No more questions available.",
            "currentIndex": current_index
        })

@questions_bp.route("/question_status", methods=["GET"])
def get_question_status_route():
    """Get question status for a session"""
    # Get session ID from query parameters
    session_id = request.args.get("session_id")  # Extract session ID from query params
    
    if not session_id:  # Validate session ID exists
        return jsonify({"has_answered": False}), 400  # Return error if no session ID
    
    return jsonify(get_question_status(session_id))  # Return question status for session

@questions_bp.route("/mark_answered", methods=["POST"])
def mark_answered():
    """Mark a question as answered for a session"""
    try:
        data = request.json  # Get request data
        session_id = data.get("session_id")  # Extract session ID
        question_index = data.get("question_index")  # Extract question index
        
        if not session_id or question_index is None:  # Validate required fields
            return jsonify({"success": False, "message": "Session ID and question index required"}), 400
        
        # Mark question as answered
        mark_question_answered(session_id, question_index)  # Update session state
        
        return jsonify({"success": True, "message": "Question marked as answered"})  # Return success
    except Exception as e:  # Handle any errors
        return jsonify({"success": False, "message": f"Error marking question as answered: {str(e)}"}), 500 