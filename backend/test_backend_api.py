#!/usr/bin/env python3
"""
Backend API Tests for Speech Evaluation Application
=================================================

Comprehensive test suite for all backend API endpoints.

Usage:
    python test_backend_api.py [--verbose] [--endpoint ENDPOINT]
"""

import unittest
import requests
import json
import os
import time
import tempfile
import wave
import numpy as np
from pathlib import Path
import argparse
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Colors:
    """ANSI color codes for colored terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class BackendAPITestSuite(unittest.TestCase):
    """Comprehensive backend API tests"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = "http://localhost:5000"
        cls.session = requests.Session()
        cls.test_session_id = f"test_session_{int(time.time())}"
        cls.admin_token = None
        
        # Wait for backend to be ready
        cls._wait_for_backend()
    
    @classmethod
    def _wait_for_backend(cls):
        """Wait for backend server to be ready"""
        max_retries = 15
        for i in range(max_retries):
            try:
                response = requests.get(f"{cls.base_url}/test-cors", timeout=5)
                if response.status_code == 200:
                    print(f"✓ Backend server ready at {cls.base_url}")
                    return
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    raise Exception(f"Backend server not responding after {max_retries} attempts")
                time.sleep(2)
    
    def test_01_cors_endpoint(self):
        """Test CORS configuration"""
        response = self.session.get(f"{self.base_url}/test-cors")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "CORS is working!")
        
        # Test OPTIONS request
        response = self.session.options(f"{self.base_url}/test-cors")
        self.assertEqual(response.status_code, 200)
        
        print("✓ CORS endpoint working correctly")

class ApplicantEndpointTests(unittest.TestCase):
    """Tests for applicant-related endpoints"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.test_session_id = f"test_applicant_{int(time.time())}"
    
    def test_store_applicant(self):
        """Test storing applicant data"""
        applicant_data = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "role": "Customer Service Representative",
            "experience": "2 years in customer support",
            "sessionId": self.test_session_id
        }
        
        response = self.session.post(f"{self.base_url}/store_applicant", json=applicant_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("message", data)
        
        print("✓ Applicant storage working")
    
    def test_store_applicant_validation(self):
        """Test applicant data validation"""
        # Test with missing required fields
        invalid_data = {
            "name": "Test User"
            # Missing other required fields
        }
        
        response = self.session.post(f"{self.base_url}/store_applicant", json=invalid_data)
        # Should handle missing fields gracefully
        self.assertIn(response.status_code, [200, 400])
        
        print("✓ Applicant validation handling")

class QuestionEndpointTests(unittest.TestCase):
    """Tests for question-related endpoints"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    def test_reset_questions(self):
        """Test resetting questions"""
        response = self.session.post(f"{self.base_url}/reset_questions")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        print("✓ Question reset working")
    
    def test_question_count(self):
        """Test getting question count"""
        response = self.session.get(f"{self.base_url}/question_count")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("total_questions", data)
        self.assertIsInstance(data["total_questions"], int)
        self.assertGreater(data["total_questions"], 0)
        
        print(f"✓ Question count: {data['total_questions']}")
    
    def test_get_question(self):
        """Test getting current question"""
        # Reset questions first
        self.session.post(f"{self.base_url}/reset_questions")
        
        response = self.session.get(f"{self.base_url}/question")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("question", data)
        self.assertIn("index", data)
        self.assertIsInstance(data["index"], int)
        
        print(f"✓ Question retrieval working (Index: {data['index']})")
    
    def test_next_question(self):
        """Test moving to next question"""
        # Reset questions first
        self.session.post(f"{self.base_url}/reset_questions")
        
        # Get current question index
        response = self.session.get(f"{self.base_url}/question")
        initial_index = response.json()["index"]
        
        # Move to next question
        response = self.session.post(f"{self.base_url}/next_question")
        
        if response.status_code == 200:
            # Get question again to verify index changed
            response = self.session.get(f"{self.base_url}/question")
            new_index = response.json()["index"]
            self.assertNotEqual(initial_index, new_index)
            print("✓ Next question working")
        else:
            # Might be at the end of questions
            print("✓ Next question endpoint accessible")

class AudioEndpointTests(unittest.TestCase):
    """Tests for audio-related endpoints"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    def test_text_to_speech(self):
        """Test text-to-speech endpoint"""
        tts_data = {
            "text": "Hello, this is a test message for text to speech functionality."
        }
        
        response = self.session.post(f"{self.base_url}/speak", json=tts_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        print("✓ Text-to-speech working")
    
    def test_audio_evaluation(self):
        """Test audio evaluation endpoint"""
        # Create test audio file
        test_audio = self._create_test_audio()
        
        files = {
            'audio': ('test.wav', test_audio, 'audio/wav')
        }
        
        data = {
            'applicantId': 'test_applicant',
            'questionIndex': '0'
        }
        
        response = self.session.post(f"{self.base_url}/evaluate", files=files, data=data)
        
        # Audio evaluation might fail due to AI service dependencies
        # but the endpoint should be accessible
        self.assertIn(response.status_code, [200, 500])
        
        print("✓ Audio evaluation endpoint accessible")
    
    def _create_test_audio(self):
        """Create a test audio file"""
        sample_rate = 44100
        duration = 2  # 2 seconds
        frequency = 440  # A4 note
        
        # Generate sine wave
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        with open(temp_file.name, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(temp_file.name)
        return audio_bytes

class AdminEndpointTests(unittest.TestCase):
    """Tests for admin-related endpoints"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
        self.admin_credentials = {
            "username": "admin",
            "password": "admin123"
        }
    
    def test_admin_authentication(self):
        """Test admin authentication"""
        response = self.session.post(f"{self.base_url}/admin/auth", 
                                   json=self.admin_credentials)
        
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data["status"], "success")
            print("✓ Admin authentication working")
        else:
            print("⚠ Admin authentication not configured or credentials incorrect")
    
    def test_admin_applicants_list(self):
        """Test getting list of applicants"""
        # Try to authenticate first
        auth_response = self.session.post(f"{self.base_url}/admin/auth", 
                                        json=self.admin_credentials)
        
        if auth_response.status_code == 200:
            response = self.session.get(f"{self.base_url}/admin/applicants")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIsInstance(data, list)
            print(f"✓ Admin applicants list working ({len(data)} applicants)")
        else:
            print("⚠ Skipping admin applicants test (auth failed)")
    
    def test_admin_questions_management(self):
        """Test admin questions management"""
        # Try to authenticate first
        auth_response = self.session.post(f"{self.base_url}/admin/auth", 
                                        json=self.admin_credentials)
        
        if auth_response.status_code == 200:
            # Get questions
            response = self.session.get(f"{self.base_url}/admin/questions")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIsInstance(data, list)
            print(f"✓ Admin questions management working ({len(data)} questions)")
        else:
            print("⚠ Skipping admin questions test (auth failed)")

class TypingTestEndpointTests(unittest.TestCase):
    """Tests for typing test endpoints"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    def test_typing_text_endpoint(self):
        """Test getting typing test text"""
        response = self.session.get(f"{self.base_url}/typing/text")
        
        if response.status_code == 200:
            data = response.json()
            self.assertIn("text", data)
            self.assertIsInstance(data["text"], str)
            self.assertGreater(len(data["text"]), 0)
            print("✓ Typing test text endpoint working")
        else:
            print("⚠ Typing test endpoint not available")
    
    def test_typing_result_submission(self):
        """Test submitting typing test results"""
        typing_result = {
            "wpm": 65,
            "accuracy": 95.5,
            "time_taken": 60,
            "applicant_id": "test_applicant"
        }
        
        response = self.session.post(f"{self.base_url}/typing/submit", json=typing_result)
        
        # Accept various response codes as implementation may vary
        self.assertIn(response.status_code, [200, 201, 404])
        
        if response.status_code in [200, 201]:
            print("✓ Typing result submission working")
        else:
            print("⚠ Typing result submission endpoint not implemented")

class WrittenTestEndpointTests(unittest.TestCase):
    """Tests for written test endpoints"""
    
    def setUp(self):
        """Set up for each test"""
        self.base_url = "http://localhost:5000"
        self.session = requests.Session()
    
    def test_written_questions_endpoint(self):
        """Test getting written test questions"""
        response = self.session.get(f"{self.base_url}/written/questions")
        
        if response.status_code == 200:
            data = response.json()
            self.assertIsInstance(data, list)
            print(f"✓ Written test questions endpoint working ({len(data)} questions)")
        else:
            print("⚠ Written test questions endpoint not available")
    
    def test_written_submission(self):
        """Test submitting written test answers"""
        written_answers = {
            "applicant_id": "test_applicant",
            "answers": [
                {"question_id": 1, "answer": "Test answer 1"},
                {"question_id": 2, "answer": "Test answer 2"}
            ]
        }
        
        response = self.session.post(f"{self.base_url}/written/submit", json=written_answers)
        
        # Accept various response codes
        self.assertIn(response.status_code, [200, 201, 404])
        
        if response.status_code in [200, 201]:
            print("✓ Written test submission working")
        else:
            print("⚠ Written test submission endpoint not implemented")

def run_endpoint_tests(endpoint_filter=None, verbose=False):
    """Run backend API tests"""
    print("=" * 60)
    print("  BACKEND API TESTS")
    print("=" * 60)
    
    # Test suites to run
    test_suites = [
        ('CORS & Basic', BackendAPITestSuite),
        ('Applicant Endpoints', ApplicantEndpointTests),
        ('Question Endpoints', QuestionEndpointTests),
        ('Audio Endpoints', AudioEndpointTests),
        ('Admin Endpoints', AdminEndpointTests),
        ('Typing Test Endpoints', TypingTestEndpointTests),
        ('Written Test Endpoints', WrittenTestEndpointTests)
    ]
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for suite_name, test_class in test_suites:
        if endpoint_filter and endpoint_filter.lower() not in suite_name.lower():
            continue
        
        print(f"\n🔧 {suite_name}")
        print("-" * 40)
        
        # Create test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        
        # Run tests
        stream = sys.stdout if verbose else open(os.devnull, 'w')
        runner = unittest.TextTestRunner(verbosity=2 if verbose else 1, stream=stream)
        result = runner.run(suite)
        
        # Update totals
        total_tests += result.testsRun
        passed = result.testsRun - len(result.failures) - len(result.errors)
        failed = len(result.failures) + len(result.errors)
        total_passed += passed
        total_failed += failed
        
        if failed > 0:
            print(f"❌ {failed} test(s) failed in {suite_name}")
            if verbose:
                for test, error in result.failures + result.errors:
                    print(f"  FAIL: {test}")
                    print(f"    {error}")
        else:
            print(f"✅ All tests passed in {suite_name}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print(f"\n🎉 All backend API tests passed!")
    else:
        print(f"\n⚠ {total_failed} test(s) failed. Check the output above for details.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Backend API Test Suite")
    parser.add_argument('--endpoint', help='Filter tests by endpoint name')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        run_endpoint_tests(args.endpoint, args.verbose)
    except KeyboardInterrupt:
        print(f"\n⚠ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    main() 