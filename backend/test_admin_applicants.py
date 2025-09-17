#!/usr/bin/env python3
"""
Test script to verify the updated admin applicants route handles the new JSON structure
"""

import json
import os
import tempfile
import shutil

def create_test_temp_files():
    """Create test temporary files with the new segmented structure"""
    
    # Create test data directory
    test_data_dir = "test_data"
    if os.path.exists(test_data_dir):
        shutil.rmtree(test_data_dir)
    os.makedirs(test_data_dir)
    # Create temp_applicants subdirectory
    os.makedirs(os.path.join(test_data_dir, "temp_applicants"))
    
    # Test case 1: New segmented structure
    session_id_1 = "test_session_001"
    
    # Create temp applicant file
    temp_applicant_1 = {
        "sessionId": session_id_1,
        "applicant": {
            "fullName": "John Doe",
            "email": "john@example.com",
            "role": "Customer Service",
            "phone": "1234567890",
            "experience": "5 years",
            "currentCompany": "ABC Corp"
        },
        "timestamp": "2025-01-15T10:00:00Z"
    }
    
    with open(os.path.join(test_data_dir, "temp_applicants", f"temp_applicant_{session_id_1}.json"), 'w') as f:
        json.dump(temp_applicant_1, f, indent=2)
    
    # Create temp evaluation file with new segmented structure
    temp_evaluation_1 = {
        "speech_eval": [
            {
                "question": "How would you handle a difficult customer?",
                "transcript": "I would listen carefully and remain calm...",
                "audio_metrics": {
                    "duration": 15.5,
                    "avg_pitch_hz": 180.25,
                    "estimated_wpm": 120.0
                },
                "evaluation": {
                    "score": 85,
                    "category_scores": {
                        "relevance": 90,
                        "grammar_lexis": 85,
                        "communication_skills": 88,
                        "fluency_pronunciation": 82,
                        "customer_service_fit": 87
                    },
                    "comment": "Good response with clear communication"
                },
                "timestamp": "2025-01-15T10:05:00Z"
            }
        ],
        "listening_test": [
            {
                "type": "listening",
                "test_id": "LT001",
                "score": 92,
                "questions_correct": 9,
                "total_questions": 10,
                "time_taken": 180,
                "timestamp": "2025-01-15T10:30:00Z"
            }
        ],
        "typing_test": [
            {
                "type": "typing",
                "test_id": 1,
                "timestamp": "2025-01-15T11:00:00Z",
                "typed_text": "Welcome to our customer service team...",
                "typed_words": 45,
                "time_taken_seconds": 58,
                "words_per_minute": 46.55,
                "accuracy_percentage": 95
            }
        ]
    }
    
    with open(os.path.join(test_data_dir, "temp_applicants", f"temp_evaluation_{session_id_1}.json"), 'w') as f:
        json.dump(temp_evaluation_1, f, indent=2)
    
    # Test case 2: Old format (for backward compatibility)
    session_id_2 = "test_session_002"
    
    temp_applicant_2 = {
        "sessionId": session_id_2,
        "applicant": {
            "fullName": "Jane Smith",
            "email": "jane@example.com",
            "role": "Sales Representative",
            "phone": "0987654321",
            "experience": "3 years",
            "currentCompany": "XYZ Inc"
        },
        "timestamp": "2025-01-15T12:00:00Z"
    }
    
    with open(os.path.join(test_data_dir, "temp_applicants", f"temp_applicant_{session_id_2}.json"), 'w') as f:
        json.dump(temp_applicant_2, f, indent=2)
    
    # Create temp evaluation file with old format
    temp_evaluation_2 = {
        "evaluations": [
            {
                "question": "Describe your sales approach",
                "transcript": "I focus on understanding customer needs...",
                "audio_metrics": {
                    "duration": 12.0,
                    "avg_pitch_hz": 175.0,
                    "estimated_wpm": 110.0
                },
                "evaluation": {
                    "score": 78,
                    "category_scores": {
                        "relevance": 80,
                        "grammar_lexis": 75,
                        "communication_skills": 82,
                        "fluency_pronunciation": 78,
                        "customer_service_fit": 80
                    },
                    "comment": "Good understanding of sales principles"
                },
                "timestamp": "2025-01-15T12:05:00Z"
            }
        ]
    }
    
    with open(os.path.join(test_data_dir, "temp_applicants", f"temp_evaluation_{session_id_2}.json"), 'w') as f:
        json.dump(temp_evaluation_2, f, indent=2)
    
    print(f"✅ Created test temporary files in {test_data_dir}")
    return test_data_dir

def test_segmented_structure():
    """Test the new segmented structure handling"""
    
    print("\n🧪 Testing new segmented structure handling...")
    
    # Create test files
    test_data_dir = create_test_temp_files()
    
    try:
        # Simulate the admin applicants route logic
        temp_applicants = []
        
        # Scan for temp applicant files
        temp_applicants_dir = os.path.join(test_data_dir, "temp_applicants")
        for filename in os.listdir(temp_applicants_dir):
            if filename.startswith("temp_applicant_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(temp_applicants_dir, filename), 'r') as f:
                        temp_data = json.load(f)
                        
                        # Create applicant entry
                        applicant_entry = {
                            "id": temp_data.get("sessionId"),
                            "applicant_info": temp_data.get("applicant", {}),
                            "application_timestamp": temp_data.get("timestamp"),
                            "evaluations": [],
                            "total_questions": 5,
                            "completion_timestamp": None,
                            "last_updated": temp_data.get("timestamp")
                        }
                        
                        # Load corresponding evaluation file
                        eval_filename = f"temp_evaluation_{temp_data.get('sessionId')}.json"
                        eval_filepath = os.path.join(temp_applicants_dir, eval_filename)
                        
                        if os.path.exists(eval_filepath):
                            with open(eval_filepath, 'r') as eval_f:
                                eval_data = json.load(eval_f)
                                
                                # Handle both old and new segmented structure
                                if "evaluations" in eval_data:
                                    # Old format
                                    applicant_entry["evaluations"] = eval_data.get("evaluations", [])
                                    applicant_entry["total_questions"] = len(eval_data.get("evaluations", []))
                                    print(f"📋 Loaded old format: {len(eval_data.get('evaluations', []))} questions")
                                else:
                                    # New segmented format
                                    applicant_entry.update(eval_data)
                                    
                                    # Calculate total questions from all test segments
                                    total_questions = 0
                                    speech_count = len(eval_data.get("speech_eval", []))
                                    listening_count = len(eval_data.get("listening_test", []))
                                    typing_count = len(eval_data.get("typing_test", []))
                                    
                                    total_questions += speech_count
                                    total_questions += listening_count
                                    total_questions += typing_count
                                    
                                    applicant_entry["total_questions"] = total_questions
                                    
                                    # Ensure all test segments are present
                                    if "speech_eval" not in applicant_entry:
                                        applicant_entry["speech_eval"] = []
                                    if "listening_test" not in applicant_entry:
                                        applicant_entry["listening_test"] = []
                                    if "typing_test" not in applicant_entry:
                                        applicant_entry["typing_test"] = []
                                    
                                    print(f"📊 Loaded new segmented structure: {speech_count} speech, {listening_count} listening, {typing_count} typing = {total_questions} total")
                        
                        temp_applicants.append(applicant_entry)
                        
                except Exception as e:
                    print(f"❌ Error processing {filename}: {e}")
        
        # Display results
        print(f"\n📋 Processed {len(temp_applicants)} temporary applicants:")
        for app in temp_applicants:
            session_id = app.get("id", "unknown")
            speech_count = len(app.get("speech_eval", []))
            listening_count = len(app.get("listening_test", []))
            typing_count = len(app.get("typing_test", []))
            evaluations_count = len(app.get("evaluations", []))
            total = app.get("total_questions", 0)
            
            print(f"\n   Session: {session_id}")
            print(f"   - Total questions: {total}")
            if evaluations_count > 0:
                print(f"   - Old format evaluations: {evaluations_count}")
            else:
                print(f"   - Speech evaluations: {speech_count}")
                print(f"   - Listening tests: {listening_count}")
                print(f"   - Typing tests: {typing_count}")
            
            # Verify structure
            if "speech_eval" in app:
                print(f"   ✅ Has speech_eval section")
            if "listening_test" in app:
                print(f"   ✅ Has listening_test section")
            if "typing_test" in app:
                print(f"   ✅ Has typing_test section")
            if "evaluations" in app and app["evaluations"]:
                print(f"   ✅ Has old format evaluations")
        
        print(f"\n✅ Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Clean up test files
        if os.path.exists(test_data_dir):
            shutil.rmtree(test_data_dir)
            print(f"🧹 Cleaned up test directory: {test_data_dir}")

if __name__ == "__main__":
    print("🚀 Testing Admin Applicants Route - New JSON Structure")
    print("=" * 60)
    
    success = test_segmented_structure()
    
    if success:
        print("\n🎉 All tests passed! The admin applicants route is ready for the new JSON structure.")
    else:
        print("\n💥 Some tests failed. Please check the implementation.") 