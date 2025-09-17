#!/usr/bin/env python3
"""
Focused Test Script for Typing Test and Completion Status
This script specifically tests if typing test results are recorded and completion status is properly set.
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"
TEST_APPLICANT = {
    "fullName": "Typing Test User",
    "email": "typing.test@example.com",
    "role": "Data Entry Specialist",
    "phone": "+1234567890",
    "experience": "1-3",
    "currentCompany": "Test Company"
}

def print_step(step_num, description):
    """Print a formatted step description"""
    print(f"\n{'='*50}")
    print(f"STEP {step_num}: {description}")
    print(f"{'='*50}")

def print_status(message, success=True):
    """Print a formatted status message"""
    icon = "✅" if success else "❌"
    print(f"{icon} {message}")

def test_typing_test_endpoint():
    """Test the typing test endpoint directly"""
    print_step(1, "Testing Typing Test Endpoint")
    
    try:
        # Test data
        test_data = {
            "session_id": "typing_test_session",
            "wpm": 52,
            "accuracy": 96.8,
            "time_taken": 180,
            "total_words": 156,
            "correct_words": 151,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Sending test data: {json.dumps(test_data, indent=2)}")
        
        # Send to typing test endpoint
        response = requests.post(f"{BASE_URL}/typing/test", json=test_data)
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            print_status("Typing test endpoint responded successfully")
            return True
        else:
            print_status(f"Typing test endpoint failed: {response.status_code}", False)
            return False
            
    except Exception as e:
        print_status(f"Error testing typing test endpoint: {str(e)}", False)
        return False

def test_typing_test_save():
    """Test saving typing test results"""
    print_step(2, "Testing Typing Test Save")
    
    try:
        # Create a test session
        session_id = f"typing_session_{int(time.time())}"
        
        # Test typing result
        typing_result = {
            "session_id": session_id,
            "wpm": 48,
            "accuracy": 94.2,
            "time_taken": 150,
            "total_words": 120,
            "correct_words": 113,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"Saving typing test result for session: {session_id}")
        
        # Try to save the result
        response = requests.post(f"{BASE_URL}/typing/test", json=typing_result)
        
        print(f"Save response status: {response.status_code}")
        print(f"Save response body: {response.text}")
        
        if response.status_code == 200:
            print_status("Typing test result saved successfully")
            
            # Check if it was saved to the file
            time.sleep(1)  # Wait for file write
            
            typing_file = "data/typing_tests.json"
            if os.path.exists(typing_file):
                with open(typing_file, 'r') as f:
                    data = json.load(f)
                
                print(f"Typing tests file contains {len(data)} entries")
                
                # Look for our session
                found = False
                for entry in data:
                    if entry.get("session_id") == session_id:
                        found = True
                        print_status("Typing test result found in file")
                        print(f"   WPM: {entry.get('wpm')}")
                        print(f"   Accuracy: {entry.get('accuracy')}")
                        break
                
                if not found:
                    print_status("Typing test result not found in file", False)
            else:
                print_status("Typing tests file not found", False)
            
            return True
        else:
            print_status(f"Failed to save typing test: {response.status_code}", False)
            return False
            
    except Exception as e:
        print_status(f"Error testing typing test save: {str(e)}", False)
        return False

def test_completion_marking():
    """Test if completion status is properly marked"""
    print_step(3, "Testing Completion Status Marking")
    
    try:
        # Create a test applicant
        session_id = f"completion_test_{int(time.time())}"
        
        applicant_data = {
            "sessionId": session_id,
            "timestamp": datetime.now().isoformat(),
            "applicant": TEST_APPLICANT
        }
        
        print(f"Creating test applicant with session: {session_id}")
        
        # Store applicant
        response = requests.post(f"{BASE_URL}/store_applicant", json=applicant_data)
        
        if response.status_code != 200:
            print_status("Failed to create test applicant", False)
            return False
        
        print_status("Test applicant created")
        
        # Simulate completing all tests
        print("Simulating test completion...")
        
        # 1. Speech evaluation
        speech_result = {
            "session_id": session_id,
            "question_index": 0,
            "evaluation_data": {
                "question": "Test question",
                "transcript": "Test answer",
                "audio_metrics": {"duration": 10.0},
                "evaluation": {"score": 85},
                "comment": "Test evaluation"
            }
        }
        
        requests.post(f"{BASE_URL}/finish_evaluation", json=speech_result)
        print_status("Speech evaluation simulated")
        
        # 2. Typing test
        typing_result = {
            "session_id": session_id,
            "wpm": 50,
            "accuracy": 95.0,
            "time_taken": 120,
            "total_words": 100,
            "correct_words": 95
        }
        
        requests.post(f"{BASE_URL}/typing/test", json=typing_result)
        print_status("Typing test simulated")
        
        # Wait for processing
        time.sleep(2)
        
        # Check completion status
        print("Checking completion status...")
        
        # Check temp evaluation file
        temp_file = f"data/temp_applicants/temp_evaluation_{session_id}.json"
        if os.path.exists(temp_file):
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            print_status("Temporary evaluation file found")
            print(f"   Speech evaluations: {len(data.get('speech_eval', []))}")
            print(f"   Typing tests: {len(data.get('typing_test', []))}")
            
            # Check if typing test was recorded
            typing_tests = data.get('typing_test', [])
            if typing_tests:
                print_status("Typing test data found in temp file")
                for test in typing_tests:
                    print(f"   WPM: {test.get('wpm')}, Accuracy: {test.get('accuracy')}")
            else:
                print_status("No typing test data in temp file", False)
        else:
            print_status("Temporary evaluation file not found", False)
        
        # Check typing tests file
        typing_file = "data/typing_tests.json"
        if os.path.exists(typing_file):
            with open(typing_file, 'r') as f:
                data = json.load(f)
            
            print(f"Typing tests file contains {len(data)} entries")
            
            # Look for our session
            found = False
            for entry in data:
                if entry.get("session_id") == session_id:
                    found = True
                    print_status("Typing test found in main file")
                    break
            
            if not found:
                print_status("Typing test not found in main file", False)
        
        return True
        
    except Exception as e:
        print_status(f"Error testing completion marking: {str(e)}", False)
        return False

def check_admin_panel():
    """Check what's visible in the admin panel"""
    print_step(4, "Checking Admin Panel")
    
    try:
        # Get applicants list
        response = requests.get(f"{BASE_URL}/admin/applicants")
        
        if response.status_code == 200:
            applicants = response.json()
            print_status(f"Admin panel accessible, found {len(applicants)} applicants")
            
            # Look for our test applicants
            test_applicants = []
            for applicant in applicants:
                email = applicant.get("email", "")
                if "test" in email.lower() or "typing" in email.lower():
                    test_applicants.append(applicant)
            
            if test_applicants:
                print_status(f"Found {len(test_applicants)} test applicants")
                for applicant in test_applicants:
                    print(f"   {applicant.get('fullName')} - {applicant.get('email')}")
                    print(f"     Status: {applicant.get('status', 'N/A')}")
                    print(f"     Completion: {applicant.get('completionDate', 'N/A')}")
                    
                    # Check for typing test data
                    typing_test = applicant.get('typingTest')
                    if typing_test:
                        print(f"     Typing Test: WPM {typing_test.get('wpm')}, Accuracy {typing_test.get('accuracy')}")
                    else:
                        print("     Typing Test: Not found")
            else:
                print_status("No test applicants found in admin panel")
        else:
            print_status(f"Admin panel not accessible: {response.status_code}", False)
        
        return True
        
    except Exception as e:
        print_status(f"Error checking admin panel: {str(e)}", False)
        return False

def main():
    """Main test function"""
    print("🎯 TYPING TEST & COMPLETION STATUS TEST")
    print("Testing if typing test results are recorded and completion status is set")
    print(f"Starting test at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run the tests
    test_typing_test_endpoint()
    test_typing_test_save()
    test_completion_marking()
    check_admin_panel()
    
    print("\n🎯 TEST COMPLETED")
    print("\nNext steps:")
    print("1. Check the admin panel manually")
    print("2. Look for test applicants")
    print("3. Verify if typing test results are recorded")
    print("4. Check if completion status is properly set")
    print("\nIf issues persist, check the console logs for errors.")

if __name__ == "__main__":
    main() 