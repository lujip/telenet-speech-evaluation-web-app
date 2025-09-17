import requests
import json
import time
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_SESSION_ID = f"test_written_{int(time.time())}"

def test_written_test_integration():
    """Test the complete written test integration"""
    print("🧪 Testing Written Test Integration")
    print(f"Session ID: {TEST_SESSION_ID}")
    print("=" * 50)
    
    try:
        # Step 1: Create a test applicant
        print("1. Creating test applicant...")
        applicant_data = {
            "sessionId": TEST_SESSION_ID,
            "timestamp": datetime.now().isoformat(),
            "applicant": {
                "positionApplied": "Test Agent",
                "lastName": "Test",
                "firstName": "User",
                "dateOfBirth": "1990-01-01",
                "gender": "Male",
                "civilStatus": "Single",
                "email": "test@example.com"
            }
        }
        
        response = requests.post(f"{BASE_URL}/store_applicant", json=applicant_data)
        if response.status_code == 200:
            print("✅ Test applicant created successfully")
        else:
            print(f"❌ Failed to create test applicant: {response.status_code}")
            return False
        
        # Step 2: Get written test questions
        print("\n2. Fetching written test questions...")
        response = requests.get(f"{BASE_URL}/written/questions")
        if response.status_code == 200:
            questions_data = response.json()
            if questions_data.get("success"):
                questions = questions_data["questions"]
                print(f"✅ Retrieved {len(questions)} questions")
            else:
                print(f"❌ Failed to get questions: {questions_data.get('message')}")
                return False
        else:
            print(f"❌ Failed to fetch questions: {response.status_code}")
            return False
        
        # Step 3: Submit written test answers
        print("\n3. Submitting written test answers...")
        
        # Create test answers (all correct for testing)
        test_answers = {}
        for question in questions:
            # For testing, let's answer the first option (index 0) for all questions
            test_answers[str(question["id"])] = 0
        
        submit_data = {
            "session_id": TEST_SESSION_ID,
            "answers": test_answers,
            "completion_time": 120  # 2 minutes
        }
        
        response = requests.post(f"{BASE_URL}/written/submit", json=submit_data)
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get("success"):
                results = result_data["results"]
                print(f"✅ Written test submitted successfully")
                print(f"   Score: {results['score_percentage']}%")
                print(f"   Correct: {results['correct_answers']}/{results['total_questions']}")
            else:
                print(f"❌ Failed to submit test: {result_data.get('message')}")
                return False
        else:
            print(f"❌ Failed to submit test: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Step 4: Check if data was saved in temp file
        print("\n4. Checking temporary evaluation file...")
        try:
            temp_file = f"data/temp_applicants/temp_evaluation_{TEST_SESSION_ID}.json"
            with open(temp_file, 'r') as f:
                temp_data = json.load(f)
            
            print("✅ Temporary evaluation file found")
            print(f"   Speech evaluations: {len(temp_data.get('speech_eval', []))}")
            print(f"   Listening tests: {len(temp_data.get('listening_test', []))}")
            print(f"   Written tests: {len(temp_data.get('written_test', []))}")
            print(f"   Typing tests: {len(temp_data.get('typing_test', []))}")
            
            # Check written test data specifically
            written_tests = temp_data.get('written_test', [])
            if written_tests:
                print("✅ Written test data found in temp file")
                written_test = written_tests[0]
                print(f"   Type: {written_test.get('type')}")
                print(f"   Score: {written_test.get('score_percentage')}%")
                print(f"   Questions: {written_test.get('total_questions')}")
                print(f"   Completion time: {written_test.get('completion_time')} seconds")
            else:
                print("❌ No written test data found in temp file")
                return False
                
        except FileNotFoundError:
            print("❌ Temporary evaluation file not found")
            return False
        except Exception as e:
            print(f"❌ Error reading temp file: {e}")
            return False
        
        # Step 5: Test finish evaluation
        print("\n5. Testing finish evaluation...")
        response = requests.post(f"{BASE_URL}/finish_evaluation", 
                               json={"session_id": TEST_SESSION_ID})
        
        if response.status_code == 200:
            result_data = response.json()
            if result_data.get("success"):
                print("✅ Finish evaluation completed successfully")
            else:
                print(f"❌ Finish evaluation failed: {result_data.get('message')}")
                return False
        else:
            print(f"❌ Finish evaluation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # Step 6: Check final applicants.json
        print("\n6. Checking final applicants.json...")
        response = requests.get(f"{BASE_URL}/admin/applicants")
        if response.status_code == 200:
            applicants_data = response.json()
            if applicants_data.get("success"):
                applicants = applicants_data["applicants"]
                
                # Find our test applicant
                test_applicant = None
                for applicant in applicants:
                    if applicant.get("id") == TEST_SESSION_ID:
                        test_applicant = applicant
                        break
                
                if test_applicant:
                    print("✅ Test applicant found in final data")
                    written_tests = test_applicant.get("written_test", [])
                    if written_tests:
                        print("✅ Written test data preserved in final applicant record")
                        print(f"   Score: {written_tests[0].get('score_percentage')}%")
                    else:
                        print("❌ Written test data missing from final applicant record")
                        return False
                else:
                    print("❌ Test applicant not found in final data")
                    return False
            else:
                print(f"❌ Failed to get applicants: {applicants_data.get('message')}")
                return False
        else:
            print(f"❌ Failed to fetch applicants: {response.status_code}")
            return False
        
        print("\n🎉 All tests passed! Written test integration is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_written_test_integration()
    exit(0 if success else 1) 