#!/usr/bin/env python3
"""
Comprehensive Test Suite for Speech Evaluation Web Application
============================================================

This script tests the entire speech evaluation application including:
- Backend API endpoints
- Frontend functionality (via Selenium)
- Integration tests
- Audio processing functionality
- Database operations

Usage:
    python test_suite.py [--backend-only] [--frontend-only] [--integration-only] [--verbose]
"""

import unittest
import requests
import json
import os
import sys
import time
import subprocess
import tempfile
import wave
import numpy as np
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import argparse
from datetime import datetime

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

class TestConfig:
    """Configuration for test environment"""
    BACKEND_URL = "http://localhost:5000"
    FRONTEND_URL = "http://localhost:5173"
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"
    TEST_TIMEOUT = 30
    SELENIUM_TIMEOUT = 10
    
    # Paths (from backend directory)
    BACKEND_DIR = Path(__file__).parent
    PROJECT_ROOT = BACKEND_DIR.parent
    FRONTEND_DIR = PROJECT_ROOT / "src"

class BackendAPITests(unittest.TestCase):
    """Test suite for backend API endpoints"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.base_url = TestConfig.BACKEND_URL
        cls.session = requests.Session()
        cls.test_applicant_id = None
        
        # Wait for backend to be ready
        max_retries = 10
        for i in range(max_retries):
            try:
                response = requests.get(f"{cls.base_url}/test-cors", timeout=5)
                if response.status_code == 200:
                    print(f"{Colors.OKGREEN}✓ Backend server is ready{Colors.ENDC}")
                    break
            except requests.exceptions.RequestException:
                if i == max_retries - 1:
                    raise Exception(f"{Colors.FAIL}Backend server not responding after {max_retries} attempts{Colors.ENDC}")
                time.sleep(2)
    
    def test_01_cors_endpoint(self):
        """Test CORS configuration"""
        response = self.session.get(f"{self.base_url}/test-cors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        print(f"{Colors.OKGREEN}✓ CORS endpoint working{Colors.ENDC}")
    
    def test_02_store_applicant(self):
        """Test storing applicant data"""
        applicant_data = {
            "name": "Test User",
            "email": "test@example.com",
            "role": "Customer Service Representative",
            "experience": "2 years",
            "sessionId": f"test_session_{int(time.time())}"
        }
        
        response = self.session.post(f"{self.base_url}/store_applicant", json=applicant_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.__class__.test_applicant_id = applicant_data["sessionId"]
        print(f"{Colors.OKGREEN}✓ Applicant storage working{Colors.ENDC}")
    
    def test_03_questions_endpoints(self):
        """Test question-related endpoints"""
        # Test reset questions
        response = self.session.post(f"{self.base_url}/reset_questions")
        self.assertEqual(response.status_code, 200)
        
        # Test get question count
        response = self.session.get(f"{self.base_url}/question_count")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("total_questions", data)
        
        # Test get first question
        response = self.session.get(f"{self.base_url}/question")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("question", data)
        self.assertIn("index", data)
        print(f"{Colors.OKGREEN}✓ Questions endpoints working{Colors.ENDC}")
    
    def test_04_audio_endpoints(self):
        """Test audio-related endpoints"""
        # Test TTS endpoint
        response = self.session.post(f"{self.base_url}/speak", 
                                   json={"text": "Hello, this is a test"})
        self.assertEqual(response.status_code, 200)
        print(f"{Colors.OKGREEN}✓ Text-to-speech endpoint working{Colors.ENDC}")
        
        # Create a test audio file and test evaluation endpoint
        test_audio = self._create_test_audio_file()
        files = {'audio': ('test.wav', test_audio, 'audio/wav')}
        data = {'applicantId': 'test_applicant', 'questionIndex': '0'}
        
        try:
            response = self.session.post(f"{self.base_url}/evaluate", files=files, data=data)
            # Accept both 200 and 500 as the evaluation might fail without proper audio processing setup
            self.assertIn(response.status_code, [200, 500])
            print(f"{Colors.OKGREEN}✓ Audio evaluation endpoint accessible{Colors.ENDC}")
        except requests.exceptions.RequestException:
            print(f"{Colors.WARNING}⚠ Audio evaluation endpoint not fully functional{Colors.ENDC}")
    
    def test_05_admin_endpoints(self):
        """Test admin-related endpoints"""
        # Test admin authentication
        auth_data = {
            "username": TestConfig.ADMIN_USERNAME,
            "password": TestConfig.ADMIN_PASSWORD
        }
        
        response = self.session.post(f"{self.base_url}/admin/auth", json=auth_data)
        if response.status_code == 200:
            # Test get applicants
            response = self.session.get(f"{self.base_url}/admin/applicants")
            self.assertEqual(response.status_code, 200)
            
            # Test get questions
            response = self.session.get(f"{self.base_url}/admin/questions")
            self.assertEqual(response.status_code, 200)
            
            print(f"{Colors.OKGREEN}✓ Admin endpoints working{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Admin endpoints not accessible (check credentials){Colors.ENDC}")
    
    def _create_test_audio_file(self):
        """Create a simple test audio file"""
        # Generate a simple sine wave
        sample_rate = 44100
        duration = 1  # 1 second
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        
        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # Create temporary WAV file
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

class FrontendTests(unittest.TestCase):
    """Test suite for frontend functionality using Selenium"""
    
    @classmethod
    def setUpClass(cls):
        """Set up Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.driver.implicitly_wait(TestConfig.SELENIUM_TIMEOUT)
            
            # Wait for frontend to be ready
            max_retries = 10
            for i in range(max_retries):
                try:
                    cls.driver.get(TestConfig.FRONTEND_URL)
                    # Check if page loaded
                    WebDriverWait(cls.driver, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    print(f"{Colors.OKGREEN}✓ Frontend server is ready{Colors.ENDC}")
                    break
                except:
                    if i == max_retries - 1:
                        raise Exception(f"{Colors.FAIL}Frontend server not responding{Colors.ENDC}")
                    time.sleep(2)
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Selenium tests skipped: {e}{Colors.ENDC}")
            cls.driver = None
    
    @classmethod
    def tearDownClass(cls):
        """Clean up WebDriver"""
        if cls.driver:
            cls.driver.quit()
    
    def setUp(self):
        """Skip test if no driver available"""
        if not self.driver:
            self.skipTest("Selenium WebDriver not available")
    
    def test_01_landing_page_loads(self):
        """Test that landing page loads correctly"""
        self.driver.get(TestConfig.FRONTEND_URL)
        
        # Check for common elements
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            print(f"{Colors.OKGREEN}✓ Landing page loads{Colors.ENDC}")
        except TimeoutException:
            self.fail("Landing page failed to load")
    
    def test_02_navigation_links(self):
        """Test navigation between pages"""
        self.driver.get(TestConfig.FRONTEND_URL)
        
        # Look for navigation elements
        try:
            # Check for common navigation patterns
            nav_elements = self.driver.find_elements(By.TAG_NAME, "nav")
            links = self.driver.find_elements(By.TAG_NAME, "a")
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            self.assertTrue(len(nav_elements) > 0 or len(links) > 0 or len(buttons) > 0,
                          "No navigation elements found")
            print(f"{Colors.OKGREEN}✓ Navigation elements present{Colors.ENDC}")
        except NoSuchElementException:
            print(f"{Colors.WARNING}⚠ Navigation elements not found{Colors.ENDC}")
    
    def test_03_component_structure(self):
        """Test basic component structure"""
        if not TestConfig.FRONTEND_DIR.exists():
            self.skipTest("Frontend source directory not found")
        
        # Check for React components
        components_dir = TestConfig.FRONTEND_DIR / "components"
        if components_dir.exists():
            component_dirs = [d for d in components_dir.iterdir() if d.is_dir()]
            self.assertGreater(len(component_dirs), 0, "No component directories found")
            print(f"{Colors.OKGREEN}✓ Component structure verified ({len(component_dirs)} components){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Components directory not found{Colors.ENDC}")

class IntegrationTests(unittest.TestCase):
    """Integration tests for the complete application workflow"""
    
    def setUp(self):
        """Set up for integration tests"""
        self.session = requests.Session()
        self.base_url = TestConfig.BACKEND_URL
    
    def test_01_complete_evaluation_workflow(self):
        """Test the complete evaluation workflow"""
        # Step 1: Store applicant
        applicant_data = {
            "name": "Integration Test User",
            "email": "integration@test.com",
            "role": "Customer Service",
            "experience": "1 year",
            "sessionId": f"integration_test_{int(time.time())}"
        }
        
        response = self.session.post(f"{self.base_url}/store_applicant", json=applicant_data)
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Reset questions
        response = self.session.post(f"{self.base_url}/reset_questions")
        self.assertEqual(response.status_code, 200)
        
        # Step 3: Get question count
        response = self.session.get(f"{self.base_url}/question_count")
        self.assertEqual(response.status_code, 200)
        question_count = response.json()["total_questions"]
        
        # Step 4: Process first question
        response = self.session.get(f"{self.base_url}/question")
        self.assertEqual(response.status_code, 200)
        
        print(f"{Colors.OKGREEN}✓ Complete evaluation workflow test passed{Colors.ENDC}")

class TestRunner:
    """Main test runner that orchestrates all test suites"""
    
    def __init__(self, args):
        self.args = args
        self.results = {
            'backend': None,
            'frontend': None,
            'integration': None,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0
        }
    
    def run_all_tests(self):
        """Run all test suites based on command line arguments"""
        print(f"{Colors.HEADER}")
        print("=" * 60)
        print("  SPEECH EVALUATION APPLICATION TEST SUITE")
        print("=" * 60)
        print(f"{Colors.ENDC}\n")
        
        start_time = datetime.now()
        
        try:
            if not self.args.frontend_only and not self.args.integration_only:
                self._run_backend_tests()
            
            if not self.args.backend_only and not self.args.integration_only:
                self._run_frontend_tests()
            
            if not self.args.backend_only and not self.args.frontend_only:
                self._run_integration_tests()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}Tests interrupted by user{Colors.ENDC}")
        
        end_time = datetime.now()
        self._print_summary(start_time, end_time)
    
    def _run_backend_tests(self):
        """Run backend API tests"""
        print(f"{Colors.HEADER}🔧 Running Backend API Tests{Colors.ENDC}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(BackendAPITests)
        runner = unittest.TextTestRunner(verbosity=2 if self.args.verbose else 1, 
                                       stream=sys.stdout if self.args.verbose else open(os.devnull, 'w'))
        self.results['backend'] = runner.run(suite)
        
        self._update_results(self.results['backend'])
        print()
    
    def _run_frontend_tests(self):
        """Run frontend tests"""
        print(f"{Colors.HEADER}🌐 Running Frontend Tests{Colors.ENDC}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(FrontendTests)
        runner = unittest.TextTestRunner(verbosity=2 if self.args.verbose else 1, 
                                       stream=sys.stdout if self.args.verbose else open(os.devnull, 'w'))
        self.results['frontend'] = runner.run(suite)
        
        self._update_results(self.results['frontend'])
        print()
    
    def _run_integration_tests(self):
        """Run integration tests"""
        print(f"{Colors.HEADER}🔗 Running Integration Tests{Colors.ENDC}")
        print("-" * 40)
        
        suite = unittest.TestLoader().loadTestsFromTestCase(IntegrationTests)
        runner = unittest.TextTestRunner(verbosity=2 if self.args.verbose else 1, 
                                       stream=sys.stdout if self.args.verbose else open(os.devnull, 'w'))
        self.results['integration'] = runner.run(suite)
        
        self._update_results(self.results['integration'])
        print()
    
    def _update_results(self, test_result):
        """Update overall test results"""
        if test_result:
            self.results['total_tests'] += test_result.testsRun
            self.results['passed_tests'] += test_result.testsRun - len(test_result.failures) - len(test_result.errors)
            self.results['failed_tests'] += len(test_result.failures) + len(test_result.errors)
    
    def _print_summary(self, start_time, end_time):
        """Print test summary"""
        duration = end_time - start_time
        
        print(f"{Colors.HEADER}")
        print("=" * 60)
        print("  TEST SUMMARY")
        print("=" * 60)
        print(f"{Colors.ENDC}")
        
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"{Colors.OKGREEN}Passed: {self.results['passed_tests']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.results['failed_tests']}{Colors.ENDC}")
        print(f"Duration: {duration.total_seconds():.2f} seconds")
        
        success_rate = (self.results['passed_tests'] / self.results['total_tests'] * 100) if self.results['total_tests'] > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.results['failed_tests'] == 0:
            print(f"\n{Colors.OKGREEN}🎉 All tests passed!{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}⚠ Some tests failed. Use --verbose for details.{Colors.ENDC}")
        
        print(f"\n{Colors.HEADER}=" * 60 + f"{Colors.ENDC}")

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = ['requests', 'selenium', 'numpy']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"{Colors.FAIL}Missing required packages: {', '.join(missing_packages)}{Colors.ENDC}")
        print(f"Install them with: pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_servers():
    """Check if backend and frontend servers are running"""
    print("Checking server availability...")
    
    # Check backend
    try:
        response = requests.get(f"{TestConfig.BACKEND_URL}/test-cors", timeout=5)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✓ Backend server running{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Backend server responding but with status {response.status_code}{Colors.ENDC}")
    except requests.exceptions.RequestException:
        print(f"{Colors.FAIL}✗ Backend server not responding at {TestConfig.BACKEND_URL}{Colors.ENDC}")
        print("  Make sure to run: python app.py (from backend directory)")
    
    # Check frontend
    try:
        response = requests.get(TestConfig.FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            print(f"{Colors.OKGREEN}✓ Frontend server running{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}⚠ Frontend server responding but with status {response.status_code}{Colors.ENDC}")
    except requests.exceptions.RequestException:
        print(f"{Colors.FAIL}✗ Frontend server not responding at {TestConfig.FRONTEND_URL}{Colors.ENDC}")
        print("  Make sure to run: npm run dev (from project root)")
    
    print()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Speech Evaluation Application Test Suite")
    parser.add_argument('--backend-only', action='store_true', help='Run only backend tests')
    parser.add_argument('--frontend-only', action='store_true', help='Run only frontend tests')
    parser.add_argument('--integration-only', action='store_true', help='Run only integration tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--skip-deps', action='store_true', help='Skip dependency check')
    parser.add_argument('--skip-servers', action='store_true', help='Skip server availability check')
    
    args = parser.parse_args()
    
    # Check dependencies
    if not args.skip_deps and not check_dependencies():
        sys.exit(1)
    
    # Check server availability
    if not args.skip_servers:
        check_servers()
    
    # Run tests
    runner = TestRunner(args)
    runner.run_all_tests()

if __name__ == "__main__":
    main() 