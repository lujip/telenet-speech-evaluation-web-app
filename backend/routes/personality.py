from flask import Blueprint, jsonify, request
import json
import random
from datetime import datetime
from utils.file_ops import (
    save_temp_evaluation, load_temp_evaluation, load_personality_test_questions, save_personality_test_questions
)

personality_bp = Blueprint('personality', __name__)

@personality_bp.route("/personality/questions", methods=["GET"])
def get_personality_test_questions():
    """Get personality test questions"""
    try:
        # Load all questions from MongoDB
        all_questions = load_personality_test_questions()
        
        # Filter active questions
        active_questions = [q for q in all_questions if q.get("active", True)]
        
        # Remove any sensitive data from response (personality tests don't have "correct" answers)
        questions_for_frontend = []
        for question in active_questions:
            question_copy = {
                "id": question["id"],
                "type": question.get("type", "multiple_choice"),
                "question": question["question"],
                "options": question["options"],
                "category": question.get("category", "personality")
            }
            questions_for_frontend.append(question_copy)
            
        return jsonify({
            "success": True,
            "questions": questions_for_frontend
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@personality_bp.route("/personality/submit", methods=["POST"])
def submit_personality_test():
    """Submit personality test answers and analyze traits"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        answers = data.get('answers')  # {question_id: answer_index}
        
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
        
        # Load all questions to analyze responses
        all_questions = load_personality_test_questions()
        
        # Create a lookup for questions by ID
        questions_lookup = {q["id"]: q for q in all_questions}
        
        # Analyze personality categories
        total_questions = len(answers)
        question_results = []
        category_analysis = {}
        
        for question_id, selected_option_index in answers.items():
            question_id = int(question_id)
            question = questions_lookup.get(question_id)
            
            if not question:
                continue
                
            # Get the selected option text
            options = question.get("options", [])
            selected_option = options[selected_option_index] if selected_option_index < len(options) else "Invalid answer"
            
            # Get category and correct answer
            category = question.get("category", "GENERAL")
            correct_answer = question.get("correct_answer", 0)
            is_correct = selected_option_index == correct_answer
            
            # Initialize category if not exists
            if category not in category_analysis:
                category_analysis[category] = {
                    "total_questions": 0,
                    "correct_answers": 0,
                    "score": 0,
                    "percentage": 0,
                    "passed": False
                }
            
            # Update category statistics
            category_analysis[category]["total_questions"] += 1
            if is_correct:
                category_analysis[category]["correct_answers"] += 1
                
            question_results.append({
                "question_id": question_id,
                "question": question["question"],
                "selected_option_index": selected_option_index,
                "selected_option": selected_option,
                "correct_answer_index": correct_answer,
                "correct_answer": options[correct_answer] if correct_answer < len(options) else "Unknown",
                "is_correct": is_correct,
                "category": category
            })
        
        # Calculate final scores and pass/fail for each category
        for category in category_analysis:
            total = category_analysis[category]["total_questions"]
            correct = category_analysis[category]["correct_answers"]
            score = correct
            percentage = (correct / total * 100) if total > 0 else 0
            passed = score >= 8  # Pass if score >= 8 out of 10
            
            category_analysis[category]["score"] = score
            category_analysis[category]["percentage"] = round(percentage, 1)
            category_analysis[category]["passed"] = passed
        
        # Prepare evaluation data for storage
        personality_result = {
            "type": "personality",
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "total_questions": total_questions,
            "question_results": question_results,
            "category_analysis": category_analysis,
            "completion_time": data.get('completion_time', 0)  # Time taken in seconds
        }
        
        # Load existing temporary evaluations for this session
        temp_evaluations = load_temp_evaluation(session_id)
        if not temp_evaluations:
            temp_evaluations = {
                "speech_eval": [],
                "listening_test": [],
                "written_test": [],
                "typing_test": [],
                "personality_test": []
            }
        
        # Ensure personality_test exists in temp_evaluations
        if "personality_test" not in temp_evaluations:
            temp_evaluations["personality_test"] = []
        
        # Add personality test result to personality_test section
        temp_evaluations["personality_test"].append(personality_result)
        
        # Save back to temporary file
        if not save_temp_evaluation(temp_evaluations, session_id):
            return jsonify({
                "success": False,
                "message": "Failed to save evaluation results"
            }), 500
        
        # Mark personality test as completed
        from utils.session import mark_test_completed
        mark_test_completed(session_id, 'personality')
        
        return jsonify({
            "success": True,
            "message": "Personality test results saved successfully",
            "results": {
                "total_questions": total_questions,
                "category_analysis": category_analysis
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error submitting personality test: {str(e)}"
        }), 500

 