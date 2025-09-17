#!/usr/bin/env python3
"""
Test Script to Verify Fixes for Speech Evaluation Questions and JSON Combination
This script tests if the recent fixes are working properly.
"""

import requests
import json
import time
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5000"

def test_current_state():
    """Test the current state of the system"""
    print("🔍 Testing Current System State...")
    
    try:
        # Test 1: Check if backend is running
        response = requests.get(f"{BASE_URL}/admin/applicants")
        if response.status_code == 200:
            print("✅ Backend is running")
        else:
            print("❌ Backend is not responding properly")
            return False
            
        # Test 2: Check current applicants
        applicants = response.json().get("applicants", [])
        print(f"📊 Found {len(applicants)} applicants in system")
        
        # Test 3: Check recent applicant structure
        if applicants:
            latest = applicants[-1]
            print(f"📋 Latest applicant: {latest.get('applicant_info', {}).get('fullName', 'Unknown')}")
            
            # Check if it has the new segmented structure
            if "speech_eval" in latest:
                print("✅ Has new segmented structure (speech_eval)")
                speech_count = len(latest.get("speech_eval", []))
                print(f"   - Speech evaluations: {speech_count}")
            else:
                print("❌ Missing new segmented structure (speech_eval)")
                
            if "listening_test" in latest:
                listening_count = len(latest.get("listening_test", []))
                print(f"   - Listening tests: {listening_count}")
            else:
                print("❌ Missing listening_test section")
                
            if "typing_test" in latest:
                typing_count = len(latest.get("typing_test", []))
                print(f"   - Typing tests: {typing_count}")
            else:
                print("❌ Missing typing_test section")
                
            # Check if it has questions in speech evaluations
            if "speech_eval" in latest and latest["speech_eval"]:
                first_speech = latest["speech_eval"][0]
                if "question" in first_speech:
                    print("✅ Speech evaluation has question field")
                    print(f"   - Question: {first_speech['question'][:50]}...")
                else:
                    print("❌ Speech evaluation missing question field")
                    
        return True
        
    except Exception as e:
        print(f"❌ Error testing current state: {e}")
        return False

def test_temp_files():
    """Check temporary evaluation files"""
    print("\n📁 Checking Temporary Evaluation Files...")
    
    data_dir = "data"
    if not os.path.exists(data_dir):
        print("❌ Data directory not found")
        return
        
    # Check both old location (data) and new location (temp_applicants)
    temp_files = []
    if os.path.exists(os.path.join(data_dir, "temp_applicants")):
        temp_applicants_dir = os.path.join(data_dir, "temp_applicants")
        temp_files.extend([f for f in os.listdir(temp_applicants_dir) if f.startswith("temp_evaluation_")])
    # Also check old location for backward compatibility
    temp_files.extend([f for f in os.listdir(data_dir) if f.startswith("temp_evaluation_")])
    print(f"📋 Found {len(temp_files)} temporary evaluation files")
    
    if temp_files:
        # Check the most recent one
        latest_temp = sorted(temp_files)[-1]
        # Check if file is in temp_applicants directory first
        temp_applicants_path = os.path.join(data_dir, "temp_applicants", latest_temp)
        if os.path.exists(temp_applicants_path):
            temp_path = temp_applicants_path
        else:
            temp_path = os.path.join(data_dir, latest_temp)
        
        try:
            with open(temp_path, 'r') as f:
                temp_data = json.load(f)
                
            print(f"📄 Latest temp file: {latest_temp}")
            
            # Check structure
            if "speech_eval" in temp_data:
                speech_count = len(temp_data.get("speech_eval", []))
                print(f"   - Speech evaluations: {speech_count}")
                
                if speech_count > 0:
                    first_speech = temp_data["speech_eval"][0]
                    if "question" in first_speech:
                        print("✅ Speech evaluation has question field")
                    else:
                        print("❌ Speech evaluation missing question field")
                        
            if "listening_test" in temp_data:
                listening_count = len(temp_data.get("listening_test", []))
                print(f"   - Listening tests: {listening_count}")
                
            if "typing_test" in temp_data:
                typing_count = len(temp_data.get("typing_test", []))
                print(f"   - Typing tests: {typing_count}")
                
        except Exception as e:
            print(f"❌ Error reading temp file: {e}")

def test_finish_evaluation_endpoint():
    """Test the finish_evaluation endpoint"""
    print("\n🚀 Testing Finish Evaluation Endpoint...")
    
    try:
        # Get current applicants to find a session ID
        response = requests.get(f"{BASE_URL}/admin/applicants")
        if response.status_code != 200:
            print("❌ Cannot get applicants list")
            return False
            
        applicants = response.json().get("applicants", [])
        if not applicants:
            print("❌ No applicants found to test with")
            return False
            
        # Find an applicant that might have temp files
        test_applicant = None
        for applicant in applicants:
            if applicant.get("completion_timestamp"):
                continue  # Skip completed ones
            test_applicant = applicant
            break
            
        if not test_applicant:
            print("❌ No incomplete applicants found to test with")
            return False
            
        session_id = test_applicant.get("id")
        print(f"🧪 Testing with session ID: {session_id}")
        
        # Test the finish_evaluation endpoint
        response = requests.post(f"{BASE_URL}/finish_evaluation", 
                               json={"session_id": session_id})
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Finish evaluation endpoint working")
                print(f"   - Message: {result.get('message')}")
            else:
                print("❌ Finish evaluation failed")
                print(f"   - Error: {result.get('message')}")
        else:
            print(f"❌ Finish evaluation endpoint error: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing finish evaluation: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Speech Evaluation and JSON Combination Fixes")
    print("=" * 60)
    
    # Test current state
    if not test_current_state():
        print("\n❌ System not ready for testing")
        return
        
    # Test temp files
    test_temp_files()
    
    # Test finish evaluation endpoint
    test_finish_evaluation_endpoint()
    
    print("\n" + "=" * 60)
    print("🏁 Testing Complete!")
    print("\n💡 Next Steps:")
    print("1. Complete a full evaluation (speech + listening + typing)")
    print("2. Check if questions are now recorded in speech evaluations")
    print("3. Verify that all test results are combined in applicants.json")
    print("4. Check admin panel for complete data display")

if __name__ == "__main__":
    main() 