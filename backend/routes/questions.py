from flask import Blueprint, jsonify, request
from utils.session import (
    get_active_questions_for_session, get_session_state, set_session_state,
    get_current_question_for_session, move_to_next_question, 
    mark_question_answered, get_question_status, reset_session_questions,
    get_active_listening_test_questions_for_session, get_question_by_index,
    resume_session_from_last_checkpoint, resume_listening_session_from_last_checkpoint,
    get_next_unanswered_question_index, get_next_unanswered_listening_question_index,
    get_test_completion_status
)
from utils.tts import speak_async
from utils.file_ops import (
    load_questions, save_questions, load_listening_test_questions, save_listening_test_questions, load_written_test_questions, save_written_test_questions
)

questions_bp = Blueprint('questions', __name__)

@questions_bp.route("/questions/current", methods=["GET"])
def get_current_question():
    """Get the current question from MongoDB."""
    try:
        questions = load_questions()
        # ... (existing logic to select the current question)
        # Return the question as before
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

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
        current_question = get_question_by_index(session_id, 0)  # Get first question
        if current_question:  # Verify question data exists
            print(f"DEBUG: Session {session_id} - Reset successful, first question: {current_question['text'][:50]}...")
            return jsonify({  # Return success with first question
                "success": True, 
                "message": "Questions reset to beginning",
                "question": {
                    "text": current_question["text"],
                    "keywords": current_question.get("keywords", []),
                    "id": current_question.get("id"),
                    "audio_id": current_question.get("audio_id", "")
                }
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
        current_question = get_question_by_index(session_id, state['current_index'])  # Get next question data
        
        return jsonify({  # Return success with next question
            "success": True, 
            "question": {
                "text": current_question["text"],
                "keywords": current_question.get("keywords", []),
                "id": current_question.get("id"),
                "audio_id": current_question.get("audio_id", "")
            },
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

@questions_bp.route("/listening-test-question", methods=["GET"])
def get_current_listening_test_question():
    """Get current listening test question for a session"""
    # Get session ID from query parameters
    session_id = request.args.get("session_id")  # Extract session ID from query params
    
    if not session_id:  # Validate session ID exists
        return jsonify({"text": "Session ID required", "keywords": []}), 400
    
    # Get session-specific listening test questions and state
    questions = get_active_listening_test_questions_for_session(session_id)  # Load session-specific listening test questions
    state = get_session_state(session_id)  # Get current session state
    current_index = state.get('listening_current_index', 0)  # Get current listening question index
    
    print(f"DEBUG: Session {session_id} - Loaded {len(questions)} active listening test questions")
    print(f"DEBUG: Session {session_id} - Current listening index: {current_index}")
    
    if not questions or len(questions) == 0:  # Check if questions exist
        print("DEBUG: No active listening test questions found")
        return jsonify({"text": "No listening test questions available", "keywords": []})
    
    # Get current question
    if current_index < len(questions):  # Check if current index is valid
        current_question = questions[current_index]  # Get current question data
        print(f"DEBUG: Session {session_id} - Returning listening question {current_index + 1}: {current_question['text'][:50]}...")
        return jsonify({
            "text": current_question["text"],
            "id": current_question["id"],
            "audio_id": current_question.get("audio_id", "")
        })  # Return current question as JSON
    else:  # If no current question
        print(f"DEBUG: Session {session_id} - No current listening question available")
        return jsonify({"text": "No listening test questions available", "keywords": []})

@questions_bp.route("/listening-test-question-count", methods=["GET"])
def get_listening_test_question_count():
    """Get listening test question count for a session"""
    # Get session ID from query parameters
    session_id = request.args.get("session_id")  # Extract session ID from query params
    
    if not session_id:  # Validate session ID exists
        return jsonify({"total": 0, "current": 0}), 400
    
    # Get session-specific listening test questions and state
    questions = get_active_listening_test_questions_for_session(session_id)  # Load session-specific listening test questions
    state = get_session_state(session_id)  # Get current session state
    current_index = state.get('listening_current_index', 0)  # Get current listening question index
    
    return jsonify({  # Return question count information
        "total": len(questions),  # Total number of listening test questions in session
        "current": current_index  # Current listening question index (0-based)
    })

@questions_bp.route("/listening-test-next-question", methods=["POST"])
def listening_test_next_question():
    """Move to next listening test question for a session"""
    # Get session ID from request
    session_id = request.json.get("session_id") if request.is_json else None  # Extract session ID from request body
    
    if not session_id:  # Validate session ID exists
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    # Get session-specific listening test questions and state
    questions = get_active_listening_test_questions_for_session(session_id)  # Load session-specific listening test questions
    state = get_session_state(session_id)  # Get current session state
    current_index = state.get('listening_current_index', 0)  # Get current listening question index
    
    if not questions or len(questions) == 0:  # Check if questions exist
        return jsonify({  # Return error if no questions available
            "success": False, 
            "message": "No active listening test questions available.",
            "currentIndex": current_index
        })
    
    # Try to move to next question
    if current_index + 1 < len(questions):  # Check if next question exists
        # Mark current question as answered
        state['listening_has_answered'] = state.get('listening_has_answered', set())
        state['listening_has_answered'].add(current_index)  # Track that current question was answered
        
        # Move to next question
        state['listening_current_index'] = current_index + 1  # Increment question index
        set_session_state(session_id, state)  # Save updated state
        
        # Get new current question
        current_question = questions[state['listening_current_index']]  # Get next question data
        
        return jsonify({  # Return success with next question
            "success": True, 
            "question": {
                "text": current_question["text"],
                "id": current_question["id"],
                "audio_id": current_question.get("audio_id", "")
            },
            "currentIndex": state['listening_current_index']
        })
    else:  # If no more questions
        return jsonify({  # Return error indicating no more questions
            "success": False, 
            "message": "No more listening test questions available.",
            "currentIndex": current_index
        })

@questions_bp.route("/listening-test-reset", methods=["POST"])
def listening_test_reset():
    """Reset listening test questions for a session"""
    # Get session ID from request
    session_id = request.json.get("session_id") if request.is_json else None  # Extract session ID from request body
    
    if not session_id:  # Validate session ID exists
        return jsonify({"success": False, "message": "Session ID required"}), 400
    
    # Reset listening test session state
    state = get_session_state(session_id)  # Get current session state
    state['listening_current_index'] = 0  # Reset to first question
    state['listening_questions'] = None  # Clear cached questions to force regeneration
    state['listening_has_answered'] = set()  # Clear answered questions tracking
    set_session_state(session_id, state)  # Save reset state
    
    # Get session-specific listening test questions (will regenerate with new randomization)
    questions = get_active_listening_test_questions_for_session(session_id)  # Load session-specific listening test questions
    
    print(f"DEBUG: Session {session_id} - Resetting listening test questions, new index: {state['listening_current_index']}")
    print(f"DEBUG: Session {session_id} - Loaded {len(questions)} active listening test questions after reset")
    
    if questions and len(questions) > 0:  # Check if questions exist after reset
        current_question = questions[0]  # Get first question
        if current_question:  # Verify question data exists
            print(f"DEBUG: Session {session_id} - Listening test reset successful, first question: {current_question['text'][:50]}...")
            return jsonify({  # Return success with first question
                "success": True, 
                "message": "Listening test questions reset to beginning",
                "question": {
                    "text": current_question["text"],
                    "id": current_question["id"],
                    "audio_id": current_question.get("audio_id", "")
                }
            })
    
    print(f"DEBUG: Session {session_id} - No active listening test questions available for reset")
    return jsonify({"success": False, "message": "No active listening test questions available"})  # Return error if no questions

@questions_bp.route("/session_progress", methods=["GET"])
def get_session_progress():
    """Get current session progress for resumption after page reload"""
    try:
        session_id = request.args.get("session_id")
        
        if not session_id:
            return jsonify({"success": False, "message": "Session ID required"}), 400
        
        # Get session state from MongoDB (persistent storage)
        state = get_session_state(session_id)
        
        # Get test completion status
        test_completion = get_test_completion_status(session_id)
        
        # Get speech evaluation progress
        speech_questions = get_active_questions_for_session(session_id)
        speech_next_index = get_next_unanswered_question_index(session_id)
        speech_answered_count = len(state.get('has_answered', set()))
        
        # Get listening test progress
        listening_questions = get_active_listening_test_questions_for_session(session_id)
        listening_next_index = get_next_unanswered_listening_question_index(session_id)
        listening_answered_count = len(state.get('listening_has_answered', set()))
        
        progress_data = {
            "success": True,
            "session_id": session_id,
            "test_completion": test_completion,
            "speech_evaluation": {
                "current_index": speech_next_index,
                "total_questions": len(speech_questions) if speech_questions else 0,
                "answered_count": speech_answered_count,
                "is_complete": test_completion.get('speech', False)
            },
            "listening_test": {
                "current_index": listening_next_index,
                "total_questions": len(listening_questions) if listening_questions else 0,
                "answered_count": listening_answered_count,
                "is_complete": test_completion.get('listening', False)
            },
            "last_updated": state.get('last_updated')
        }
        
        print(f"Session {session_id} progress retrieved: Speech {speech_answered_count}/{len(speech_questions) if speech_questions else 0}, Listening {listening_answered_count}/{len(listening_questions) if listening_questions else 0}")
        
        return jsonify(progress_data)
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error getting session progress: {str(e)}"}), 500

@questions_bp.route("/resume_session", methods=["POST"])
def resume_session():
    """Resume session from last checkpoint (next unanswered question)"""
    try:
        data = request.json
        session_id = data.get("session_id")
        test_type = data.get("test_type", "speech")  # Default to speech evaluation
        
        if not session_id:
            return jsonify({"success": False, "message": "Session ID required"}), 400
        
        # Import mark_test_completed here
        from utils.session import mark_test_completed, get_session_state
        
        # Resume based on test type
        if test_type == "listening":
            questions = get_active_listening_test_questions_for_session(session_id)
            state = get_session_state(session_id)
            answered_count = len(state.get('listening_has_answered', set()))
            
            # Check if all questions are answered but test not marked complete
            if answered_count >= len(questions):
                print(f"All {len(questions)} listening questions answered, auto-marking test as complete")
                mark_test_completed(session_id, 'listening')
                return jsonify({
                    "success": True,
                    "resumed": False,
                    "all_complete": True,
                    "message": "All listening test questions completed"
                })
            
            next_index = resume_listening_session_from_last_checkpoint(session_id)
            
            if next_index < len(questions):
                current_question = questions[next_index]
                return jsonify({
                    "success": True,
                    "resumed": True,
                    "current_index": next_index,
                    "question": {
                        "text": current_question["text"],
                        "id": current_question["id"],
                        "audio_id": current_question.get("audio_id", "")
                    },
                    "message": f"Resumed listening test at question {next_index + 1}"
                })
            else:
                # All questions done, mark complete
                mark_test_completed(session_id, 'listening')
                return jsonify({
                    "success": True,
                    "resumed": False,
                    "all_complete": True,
                    "message": "All listening test questions completed"
                })
        else:  # speech evaluation
            questions = get_active_questions_for_session(session_id)
            state = get_session_state(session_id)
            answered_count = len(state.get('has_answered', set()))
            
            # Check if all questions are answered but test not marked complete
            if answered_count >= len(questions):
                print(f"All {len(questions)} speech questions answered, auto-marking test as complete")
                mark_test_completed(session_id, 'speech')
                return jsonify({
                    "success": True,
                    "resumed": False,
                    "all_complete": True,
                    "message": "All speech evaluation questions completed"
                })
            
            next_index = resume_session_from_last_checkpoint(session_id)
            
            if next_index < len(questions):
                current_question = get_question_by_index(session_id, next_index)
                return jsonify({
                    "success": True,
                    "resumed": True,
                    "current_index": next_index,
                    "question": {
                        "text": current_question["text"],
                        "keywords": current_question.get("keywords", []),
                        "id": current_question.get("id"),
                        "audio_id": current_question.get("audio_id", "")
                    },
                    "message": f"Resumed speech evaluation at question {next_index + 1}"
                })
            else:
                # All questions done, mark complete
                mark_test_completed(session_id, 'speech')
                return jsonify({
                    "success": True,
                    "resumed": False,
                    "all_complete": True,
                    "message": "All speech evaluation questions completed"
                })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error resuming session: {str(e)}"}), 500 