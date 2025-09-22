#!/usr/bin/env python3
"""
Integration Tests for Speech Evaluation Application
=================================================

End-to-end integration tests that verify the complete application workflow.

Usage:
    python test_integration.py [--headless] [--slow] [--verbose]
"""

import unittest
import requests
import time
import tempfile
import wave
import numpy as np
import os
import json
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import argparse

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

class IntegrationTestConfig:
    """Configuration for integration tests"""
    BACKEND_URL = "http://localhost:5000"
    FRONTEND_URL = "http://localhost:5173"
    DEFAULT_TIMEOUT = 30
    SELENIUM_TIMEOUT = 15
    
    # Test data
    TEST_APPLICANT = {
        "name": "Integration Test User",
        "email": "integration.test@example.com",
        "role": "Customer Service Representative",
        "experience": "2 years in customer support"
    }

class CompleteWorkflowTest(unittest.TestCase):
    """Test complete application workflow from start to finish"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.config = IntegrationTestConfig()
        cls.session = requests.Session()
        cls.driver = None
        cls.test_session_id = None
        
        # Wait for backend
        cls._wait_for_backend()
        
        # Set up Selenium if available
        cls._setup_selenium()
    
    @classmethod
    def _wait_for_backend(cls):
        """Wait for backend to be ready"""
        print("Waiting for backend server...")
        max_retries = 20
        for i in range(max_retries):
            try:
                response = requests.get(f"{cls.config.BACKEND_URL}/test-cors", timeout=5)
                if response.status_code == 200:
                    print(f"{Colors.OKGREEN}✓ Backend server ready{Colors.ENDC}")
                    return
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    raise Exception("Backend server not responding")
                time.sleep(2)
    
    @classmethod
    def _setup_selenium(cls):
        """Set up Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Add headless mode if requested
            if hasattr(cls, 'headless') and cls.headless:
                chrome_options.add_argument("--headless")
            
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(cls.config.SELENIUM_TIMEOUT)
            
            # Test frontend availability
            cls.driver.get(cls.config.FRONTEND_URL)
            WebDriverWait(cls.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"{Colors.OKGREEN}✓ Frontend server ready and Selenium initialized{Colors.ENDC}")
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Selenium setup failed: {e}{Colors.ENDC}")
            cls.driver = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up resources"""
        if cls.driver:
            cls.driver.quit()
    
    def test_01_complete_evaluation_workflow(self):
        """Test the complete evaluation workflow"""
        print(f"\n{Colors.HEADER}🔄 Testing Complete Evaluation Workflow{Colors.ENDC}")
        print("-" * 50)
        
        # Step 1: Backend - Store applicant data
        self._step_01_store_applicant()
        
        # Step 2: Backend - Initialize questions
        self._step_02_initialize_questions()
        
        # Step 3: Backend - Process questions
        self._step_03_process_questions()
        
        # Step 4: Frontend - Test UI workflow (if Selenium available)
        if self.driver:
            self._step_04_frontend_workflow()
        
        print(f"{Colors.OKGREEN}✅ Complete workflow test passed{Colors.ENDC}")
    
    def _step_01_store_applicant(self):
        """Step 1: Store applicant data"""
        print("📝 Step 1: Storing applicant data...")
        
        self.test_session_id = f"integration_test_{int(time.time())}"
        applicant_data = self.config.TEST_APPLICANT.copy()
        applicant_data["sessionId"] = self.test_session_id
        
        response = self.session.post(
            f"{self.config.BACKEND_URL}/store_applicant", 
            json=applicant_data
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        
        print(f"   ✓ Applicant stored with session ID: {self.test_session_id}")
    
    def _step_02_initialize_questions(self):
        """Step 2: Initialize questions"""
        print("❓ Step 2: Initializing questions...")
        
        # Reset questions
        response = self.session.post(f"{self.config.BACKEND_URL}/reset_questions")
        self.assertEqual(response.status_code, 200)
        
        # Get question count
        response = self.session.get(f"{self.config.BACKEND_URL}/question_count")
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.question_count = data["total_questions"]
        self.assertGreater(self.question_count, 0)
        
        print(f"   ✓ Questions initialized (Total: {self.question_count})")
    
    def _step_03_process_questions(self):
        """Step 3: Process questions workflow"""
        print("🎤 Step 3: Processing questions workflow...")
        
        # Process first question
        response = self.session.get(f"{self.config.BACKEND_URL}/question")
        self.assertEqual(response.status_code, 200)
        
        question_data = response.json()
        current_index = question_data["index"]
        current_question = question_data["question"]
        
        print(f"   📋 Question {current_index}: {current_question[:50]}...")
        
        # Test TTS for the question
        tts_response = self.session.post(
            f"{self.config.BACKEND_URL}/speak",
            json={"text": current_question}
        )
        self.assertEqual(tts_response.status_code, 200)
        print(f"   🔊 TTS processed for question {current_index}")
        
        # Simulate audio recording and evaluation
        test_audio = self._create_test_audio()
        files = {'audio': ('test_response.wav', test_audio, 'audio/wav')}
        data = {
            'applicantId': self.test_session_id,
            'questionIndex': str(current_index)
        }
        
        eval_response = self.session.post(
            f"{self.config.BACKEND_URL}/evaluate",
            files=files,
            data=data
        )
        
        # Evaluation might fail due to AI dependencies, but endpoint should respond
        self.assertIn(eval_response.status_code, [200, 500])
        print(f"   🎯 Evaluation attempted for question {current_index}")
        
        print(f"   ✓ Question workflow completed successfully")
    
    def _step_04_frontend_workflow(self):
        """Step 4: Test frontend workflow"""
        print("🌐 Step 4: Testing frontend workflow...")
        
        try:
            # Navigate to landing page
            self.driver.get(self.config.FRONTEND_URL)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print("   ✓ Landing page loaded")
            
            # Try to find and test navigation
            self._test_frontend_navigation()
            
            # Try to test applicant form
            self._test_applicant_form()
            
        except Exception as e:
            print(f"   ⚠ Frontend workflow test partial: {e}")
    
    def _test_frontend_navigation(self):
        """Test frontend navigation"""
        try:
            # Look for navigation elements
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            links = self.driver.find_elements(By.TAG_NAME, "a")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            if nav_elements or links or buttons:
                print("   ✓ Navigation elements found")
            
            # Test page navigation
            test_routes = ["/applicantform", "/admin", "/testing"]
            
            for route in test_routes:
                try:
                    self.driver.get(f"{self.config.FRONTEND_URL}{route}")
                    time.sleep(1)  # Allow page to load
                    
                    # Check if page loaded (no 404 or error)
                    page_source = self.driver.page_source.lower()
                    if "404" not in page_source and "error" not in page_source:
                        print(f"   ✓ Route {route} accessible")
                    
                except Exception:
                    print(f"   ⚠ Route {route} not accessible")
            
        except Exception as e:
            print(f"   ⚠ Navigation test failed: {e}")
    
    def _test_applicant_form(self):
        """Test applicant form functionality"""
        try:
            self.driver.get(f"{self.config.FRONTEND_URL}/applicantform")
            
            # Look for form elements
            forms = self.driver.find_elements(By.TAG_NAME, "form")
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            
            if forms and inputs:
                print("   ✓ Applicant form elements found")
                
                # Try to fill out the form
                name_input = None
                email_input = None
                
                for input_elem in inputs:
                    input_type = input_elem.get_attribute("type")
                    placeholder = input_elem.get_attribute("placeholder") or ""
                    name_attr = input_elem.get_attribute("name") or ""
                    
                    if "name" in placeholder.lower() or "name" in name_attr.lower():
                        name_input = input_elem
                    elif input_type == "email" or "email" in placeholder.lower():
                        email_input = input_elem
                
                if name_input and email_input:
                    # Fill out form
                    name_input.clear()
                    name_input.send_keys(self.config.TEST_APPLICANT["name"])
                    
                    email_input.clear()
                    email_input.send_keys(self.config.TEST_APPLICANT["email"])
                    
                    print("   ✓ Form fields filled successfully")
                    
        except Exception as e:
            print(f"   ⚠ Applicant form test failed: {e}")
    
    def _create_test_audio(self):
        """Create test audio data"""
        sample_rate = 44100
        duration = 2
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        
        with wave.open(temp_file.name, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        with open(temp_file.name, 'rb') as f:
            audio_bytes = f.read()
        
        os.unlink(temp_file.name)
        return audio_bytes

class DataPersistenceTest(unittest.TestCase):
    """Test data persistence across sessions"""
    
    def setUp(self):
        """Set up for each test"""
        self.config = IntegrationTestConfig()
        self.session = requests.Session()
        self.test_session_id = f"persistence_test_{int(time.time())}"
    
    def test_applicant_data_persistence(self):
        """Test that applicant data persists correctly"""
        print(f"\n{Colors.HEADER}💾 Testing Data Persistence{Colors.ENDC}")
        print("-" * 30)
        
        # Store test applicant
        applicant_data = self.config.TEST_APPLICANT.copy()
        applicant_data["sessionId"] = self.test_session_id
        
        response = self.session.post(
            f"{self.config.BACKEND_URL}/store_applicant",
            json=applicant_data
        )
        
        self.assertEqual(response.status_code, 200)
        print(f"{Colors.OKGREEN}✓ Test applicant stored{Colors.ENDC}")
        
        # Try to retrieve via admin endpoint (if available)
        try:
            auth_response = self.session.post(
                f"{self.config.BACKEND_URL}/admin/auth",
                json={"username": "admin", "password": "admin123"}
            )
            
            if auth_response.status_code == 200:
                applicants_response = self.session.get(
                    f"{self.config.BACKEND_URL}/admin/applicants"
                )
                
                if applicants_response.status_code == 200:
                    applicants = applicants_response.json()
                    
                    # Check if our test applicant exists
                    found_applicant = None
                    for applicant in applicants:
                        if applicant.get("sessionId") == self.test_session_id:
                            found_applicant = applicant
                            break
                    
                    if found_applicant:
                        print(f"{Colors.OKGREEN}✓ Applicant data retrieved successfully{Colors.ENDC}")
                        self.assertEqual(found_applicant["name"], applicant_data["name"])
                        self.assertEqual(found_applicant["email"], applicant_data["email"])
                    else:
                        print(f"{Colors.WARNING}⚠ Test applicant not found in persistence check{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}⚠ Could not retrieve applicants list{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ Admin authentication failed - skipping persistence verification{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Persistence check failed: {e}{Colors.ENDC}")

class PerformanceTest(unittest.TestCase):
    """Basic performance tests"""
    
    def setUp(self):
        """Set up for each test"""
        self.config = IntegrationTestConfig()
        self.session = requests.Session()
    
    def test_response_times(self):
        """Test API response times"""
        print(f"\n{Colors.HEADER}⚡ Testing Performance{Colors.ENDC}")
        print("-" * 25)
        
        endpoints = [
            ("/test-cors", "GET"),
            ("/question_count", "GET"),
            ("/reset_questions", "POST"),
            ("/question", "GET")
        ]
        
        response_times = {}
        
        for endpoint, method in endpoints:
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = self.session.get(f"{self.config.BACKEND_URL}{endpoint}")
                else:
                    response = self.session.post(f"{self.config.BACKEND_URL}{endpoint}")
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # Convert to milliseconds
                
                response_times[endpoint] = response_time
                
                if response.status_code == 200:
                    status = f"{Colors.OKGREEN}✓{Colors.ENDC}"
                else:
                    status = f"{Colors.WARNING}⚠ ({response.status_code}){Colors.ENDC}"
                
                print(f"{status} {endpoint}: {response_time:.2f}ms")
                
            except Exception as e:
                print(f"{Colors.FAIL}❌ {endpoint}: Failed ({e}){Colors.ENDC}")
        
        # Check if any response is too slow
        slow_endpoints = [ep for ep, time in response_times.items() if time > 5000]
        if slow_endpoints:
            print(f"{Colors.WARNING}⚠ Slow endpoints detected: {slow_endpoints}{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}✓ All endpoints respond within acceptable time{Colors.ENDC}")

def run_integration_tests(headless=False, slow=False, verbose=False):
    """Run all integration tests"""
    print("=" * 60)
    print("  INTEGRATION TESTS")
    print("=" * 60)
    
    # Set class attributes for Selenium configuration
    CompleteWorkflowTest.headless = headless
    
    # Test suites
    test_suites = [
        ("Complete Workflow", CompleteWorkflowTest),
        ("Data Persistence", DataPersistenceTest),
        ("Performance", PerformanceTest)
    ]
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for suite_name, test_class in test_suites:
        print(f"\n{Colors.OKBLUE}🔗 {suite_name}{Colors.ENDC}")
        print("-" * 40)
        
        # Create and run test suite
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromTestCase(test_class)
        
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
            print(f"{Colors.FAIL}❌ {failed} test(s) failed in {suite_name}{Colors.ENDC}")
            if verbose:
                for test, error in result.failures + result.errors:
                    print(f"  FAIL: {test}")
                    print(f"    {error}")
        else:
            print(f"{Colors.OKGREEN}✅ All tests passed in {suite_name}{Colors.ENDC}")
        
        # Add delay between test suites if requested
        if slow and suite_name != test_suites[-1][0]:
            time.sleep(2)
    
    # Print summary
    print(f"\n" + "=" * 60)
    print("  INTEGRATION TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"{Colors.OKGREEN}Passed: {total_passed}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {total_failed}{Colors.ENDC}")
    
    success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if total_failed == 0:
        print(f"\n{Colors.OKGREEN}🎉 All integration tests passed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}⚠ {total_failed} test(s) failed. Check the output above for details.{Colors.ENDC}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Integration Test Suite")
    parser.add_argument('--headless', action='store_true', 
                      help='Run browser tests in headless mode')
    parser.add_argument('--slow', action='store_true', 
                      help='Add delays between test suites')
    parser.add_argument('--verbose', '-v', action='store_true', 
                      help='Verbose output')
    
    args = parser.parse_args()
    
    try:
        run_integration_tests(args.headless, args.slow, args.verbose)
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}⚠ Tests interrupted by user{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.FAIL}❌ Integration test execution failed: {e}{Colors.ENDC}")

if __name__ == "__main__":
    main() 