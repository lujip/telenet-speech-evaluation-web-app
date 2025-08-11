import random
from config import MAX_QUESTIONS_PER_SESSION
from .file_ops import load_questions

# Global variables for session management
session_states = {}  # Store session state for each session ID

def get_session_state(session_id):
    """Get session state for a specific session"""
    if session_id not in session_states:  # Check if session exists
        session_states[session_id] = {  # Initialize new session state
            'current_index': 0,  # Start at first question
            'questions': None,  # Questions not loaded yet
            'has_answered': set()  # Track answered questions
        }
    return session_states[session_id]  # Return existing or new session state

def set_session_state(session_id, state):
    """Set session state for a specific session"""
    session_states[session_id] = state  # Update session state with new data

def get_active_questions_for_session(session_id):
    """Get active questions for a specific session (randomized once per session)"""
    state = get_session_state(session_id)  # Get current session state
    
    # If we already have session questions, return them
    if state['questions'] is not None:  # Check if questions already loaded
        return state['questions']  # Return cached questions
    
    # Otherwise, randomize and store for this session
    all_questions = load_questions()  # Load all questions from file
    active_questions = [q for q in all_questions if q.get("active", True)]  # Filter active questions only
    
    # Randomize and select only MAX_QUESTIONS_PER_SESSION questions
    if len(active_questions) > MAX_QUESTIONS_PER_SESSION:  # Check if we have too many questions
        random.shuffle(active_questions)  # Randomize question order
        active_questions = active_questions[:MAX_QUESTIONS_PER_SESSION]  # Limit to max questions per session
    
    # Store for this session
    state['questions'] = active_questions  # Cache questions for this session
    set_session_state(session_id, state)  # Save updated state
    return active_questions

def reset_session_questions(session_id):
    """Reset session questions for new evaluation session"""
    if session_id in session_states:  # Check if session exists
        state = session_states[session_id]  # Get current session state
        state['current_index'] = 0  # Reset to first question
        state['has_answered'] = set()  # Clear answered questions tracking
        set_session_state(session_id, state)  # Save reset state

def clear_session(session_id):
    """Clear session state for a specific session"""
    if session_id in session_states:  # Check if session exists
        del session_states[session_id]  # Remove session from memory

def get_current_question_for_session(session_id):
    """Get current question for a specific session"""
    questions = get_active_questions_for_session(session_id)  # Get session questions
    state = get_session_state(session_id)  # Get session state
    current_index = state['current_index']  # Get current question index
    
    if not questions or len(questions) == 0:  # Check if questions exist
        return None  # Return None if no questions
    
    if current_index < len(questions):  # Check if current index is valid
        return {  # Return current question with text and keywords
            "text": questions[current_index]["text"],
            "keywords": questions[current_index]["keywords"]
        }
    else:  # If index is out of bounds
        return {  # Return first question as fallback
            "text": questions[0]["text"] if questions else "",
            "keywords": questions[0]["keywords"] if questions else []
        }

def move_to_next_question(session_id):
    """Move to next question for a session"""
    questions = get_active_questions_for_session(session_id)  # Get session questions
    state = get_session_state(session_id)  # Get session state
    current_index = state['current_index']  # Get current question index
    
    if not questions or current_index + 1 >= len(questions):  # Check if next question exists
        return False  # Return False if no more questions
    
    # Mark current question as answered
    state['has_answered'].add(current_index)  # Track that current question was answered
    
    # Move to next question
    state['current_index'] = current_index + 1  # Increment question index
    set_session_state(session_id, state)  # Save updated state
    
    return True  # Return True if successfully moved to next question

def mark_question_answered(session_id, question_index):
    """Mark a question as answered for a session"""
    state = get_session_state(session_id)  # Get current session state
    state['has_answered'].add(question_index)  # Mark specific question as answered
    set_session_state(session_id, state)  # Save updated state

def get_question_status(session_id):
    """Get question status for a session"""
    state = get_session_state(session_id)  # Get current session state
    current_index = state['current_index']  # Get current question index
    
    return {  # Return question status information
        "has_answered": current_index in state['has_answered'],  # Check if current question was answered
        "current_index": current_index  # Return current question index
    } 