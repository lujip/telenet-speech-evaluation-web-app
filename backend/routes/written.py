from flask import Blueprint, jsonify, request
import json
import random
from datetime import datetime
from config import WRITTEN_TEST_QUESTIONS_FILE
from utils.file_ops import (
    save_temp_evaluation, load_temp_evaluation, load_written_test_questions, save_written_test_questions
)
from utils.session import get_active_written_test_questions_for_session

written_bp = Blueprint('written', __name__)

@written_bp.route("/written/questions", methods=["GET"])
def get_written_test_questions():
    """Get a random set of written test questions for the session (20 out of 47)"""
    try:
        # Get session ID from query parameters
        session_id = request.args.get("session_id")
        
        if not session_id:
            return jsonify({
                "success": False,
                "message": "Session ID is required"
            }), 400
        
        # Get session-specific questions (randomized 20 out of 47, cached per session)
        session_questions = get_active_written_test_questions_for_session(session_id)
        
        # Remove correct answers from response (only send to frontend for display)
        questions_for_frontend = []
        for question in session_questions:
            question_copy = {
                "id": question["id"],
                "type": question.get("type", "multiple_choice"),
                "question": question["question"],
                "category": question["category"],
                "difficulty": question["difficulty"]
            }
            if question.get("type") == "input":
                question_copy["input_type"] = question.get("input_type", "text")
                question_copy["placeholder"] = question.get("placeholder", "Enter your answer")
            else:
                question_copy["options"] = question["options"]
            questions_for_frontend.append(question_copy)
        
        print(f"DEBUG: Session {session_id} - Loaded {len(questions_for_frontend)} written test questions")
        
        return jsonify({
            "success": True,
            "questions": questions_for_frontend
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@written_bp.route("/written/submit", methods=["POST"])
def submit_written_test():
    """Submit written test answers and calculate score"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        answers = data.get('answers')  # {question_id: answer_value}
        
        if not session_id:
            return jsonify({
                "success": False,
                "message": "Session ID is required"
            }), 400
            
        if not answers:
            return jsonify({
                "success": False,
                "message": "Answers are required"
            }), 400
        
        # Get the session-specific questions (the same ones the user saw)
        session_questions = get_active_written_test_questions_for_session(session_id)
        
        # Create a lookup for questions by ID
        questions_lookup = {q["id"]: q for q in session_questions}
        
        # Calculate score
        total_questions = len(answers)
        correct_count = 0
        question_results = []
        
        for question_id, submitted_answer in answers.items():
            question_id = int(question_id)
            question = questions_lookup.get(question_id)
            
            if not question:
                continue
                
            is_correct = False
            correct_answer_display = ""
            submitted_answer_display = ""
            
            # Handle different question types
            if question.get("type") == "input":
                # Input question - check against multiple possible correct answers
                correct_answers = question.get("correct_answer", [])
                submitted_answer_str = str(submitted_answer).strip()
                
                # Check if submitted answer matches any of the correct answers (case-insensitive for text)
                if question.get("input_type") == "number":
                    # For numbers, convert to float for comparison
                    try:
                        submitted_num = float(submitted_answer_str)
                        is_correct = any(float(correct) == submitted_num for correct in correct_answers)
                    except ValueError:
                        is_correct = False
                else:
                    # For text, do case-insensitive comparison
                    is_correct = any(submitted_answer_str.lower() == correct.lower() for correct in correct_answers)
                
                correct_answer_display = " / ".join(correct_answers)
                submitted_answer_display = submitted_answer_str
                
            else:
                # Multiple choice question
                correct_answer_index = question.get("correct_answer")
                is_correct = correct_answer_index == submitted_answer
                
                # Get the actual text of the selected and correct answers
                options = question.get("options", [])
                submitted_answer_display = options[submitted_answer] if submitted_answer < len(options) else "Invalid answer"
                correct_answer_display = options[correct_answer_index] if correct_answer_index < len(options) else "Invalid answer"
            
            if is_correct:
                correct_count += 1
            
            question_results.append({
                "question_id": question_id,
                "question": question["question"],
                "type": question.get("type", "multiple_choice"),
                "submitted_answer": submitted_answer,
                "submitted_answer_display": submitted_answer_display,
                "correct_answer_display": correct_answer_display,
                "is_correct": is_correct,
                "category": question.get("category", ""),
                "difficulty": question.get("difficulty", "")
            })
        
        # Calculate percentage score
        score_percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Prepare evaluation data for storage
        written_result = {
            "type": "written",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "score_percentage": round(score_percentage, 2),
            "question_results": question_results,
            "completion_time": data.get('completion_time', 0)  # Time taken in seconds
        }
        
        # Load existing temporary evaluations for this session
        temp_evaluations = load_temp_evaluation(session_id)
        if not temp_evaluations:
            temp_evaluations = {
                "speech_eval": [],
                "listening_test": [],
                "written_test": [],
                "typing_test": []
            }
        
        # Add written test result to written_test section
        temp_evaluations["written_test"].append(written_result)
        
        # Save back to temporary file
        if not save_temp_evaluation(temp_evaluations, session_id):
            return jsonify({
                "success": False,
                "message": "Failed to save evaluation results"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Written test results saved successfully",
            "results": {
                "score_percentage": round(score_percentage, 2),
                "correct_answers": correct_count,
                "total_questions": total_questions,
                "question_results": question_results
            }
        }), 200
        
    except FileNotFoundError:
        return jsonify({
            "success": False,
            "message": "Written test questions file not found"
        }), 404
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error submitting written test: {str(e)}"
        }), 500 