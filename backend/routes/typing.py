from flask import Blueprint, jsonify, request
import json
import os
from datetime import datetime
from config import TYPING_TESTS_FILE
from utils.file_ops import (
    load_typing_tests, save_typing_tests, save_temp_evaluation, load_temp_evaluation
)

typing_bp = Blueprint('typing', __name__)

@typing_bp.route("/typing/test", methods=["GET"])
def get_typing_test():
    """Get a random typing test for the applicant from MongoDB"""
    try:
        typing_tests = load_typing_tests()
        if not typing_tests:
            return jsonify({"success": False, "message": "Typing tests not available"}), 404
        import random
        selected_test = random.choice(typing_tests)
        return jsonify({
            "success": True,
            "test": {
                "id": selected_test["id"],
                "title": selected_test["title"],
                "text": selected_test["text"],
                "word_count": selected_test["word_count"],
                "difficulty": selected_test["difficulty"],
                "category": selected_test["category"]
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error retrieving typing test: {str(e)}"}), 500

@typing_bp.route("/typing/submit", methods=["POST"])
def submit_typing_test():
    """Submit typing test results and calculate WPM"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400
        
        # Extract required fields
        session_id = data.get("session_id")
        test_id = data.get("test_id")
        typed_text = data.get("typed_text", "")
        time_taken = data.get("time_taken", 60)  # in seconds
        accuracy = data.get("accuracy", 0)
        
        if not session_id or not test_id:
            return jsonify({"success": False, "message": "Session ID and test ID required"}), 400
        
        # Calculate words per minute
        # Count words in typed text (split by spaces and filter empty strings)
        typed_words = len([word for word in typed_text.split() if word.strip()])
        
        # Convert time to minutes for WPM calculation
        time_minutes = time_taken / 60.0
        wpm = round(typed_words / time_minutes, 2) if time_minutes > 0 else 0
        
        # Create typing test result
        typing_result = {
            "type": "typing",
            "test_id": test_id,
            "timestamp": datetime.now().isoformat(),
            "typed_text": typed_text,
            "typed_words": typed_words,
            "time_taken_seconds": time_taken,
            "words_per_minute": wpm,
            "accuracy_percentage": accuracy
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
        
        # Add typing test result to typing_test section
        temp_evaluations["typing_test"].append(typing_result)
        
        # Save back to temporary file
        if not save_temp_evaluation(temp_evaluations, session_id):
            return jsonify({
                "success": False,
                "message": "Failed to save evaluation results"
            }), 500
        
        return jsonify({
            "success": True,
            "message": "Typing test results saved successfully",
            "result": {
                "wpm": wpm,
                "accuracy": accuracy,
                "words_typed": typed_words,
                "time_taken": time_taken
            }
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error submitting typing test: {str(e)}"}), 500 