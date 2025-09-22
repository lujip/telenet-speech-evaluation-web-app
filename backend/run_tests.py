#!/usr/bin/env python3
"""
Master Test Runner for Speech Evaluation Application
==================================================

This script runs all test suites for the speech evaluation application
including backend API tests, frontend tests, and integration tests.

Usage:
    python run_tests.py [OPTIONS]

Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py --quick           # Run only essential tests
    python run_tests.py --backend-only    # Run only backend tests
    python run_tests.py --frontend-only   # Run only frontend tests
    python run_tests.py --integration-only # Run only integration tests
    python run_tests.py --verbose         # Detailed output
    python run_tests.py --headless        # Run browser tests in headless mode
"""

import argparse
import subprocess
import sys
import time
import os
import requests
from pathlib import Path
from datetime import datetime
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class Colors:
    """ANSI color codes"""
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
    """Test configuration"""
    BACKEND_URL = "http://localhost:5000"
    FRONTEND_URL = "http://localhost:5173"
    TIMEOUT = 30
    
    # Paths (from backend directory)
    BACKEND_DIR = Path(__file__).parent
    PROJECT_ROOT = BACKEND_DIR.parent
    FRONTEND_DIR = PROJECT_ROOT / "src"

class TestRunner:
    """Main test runner class"""
    
    def __init__(self, args):
        self.args = args
        self.project_root = TestConfig.BACKEND_DIR  # We're running from backend
        self.results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'skipped_tests': 0,
            'test_suites': {}
        }
        self.start_time = None
    
    def run_all_tests(self):
        """Run all selected test suites"""
        self.start_time = datetime.now()
        
        print(f"{Colors.HEADER}")
        print("=" * 70)
        print("  SPEECH EVALUATION APPLICATION - COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print(f"{Colors.ENDC}")
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Pre-flight checks
            if not self.args.skip_checks:
                self._run_preflight_checks()
            
            # Run test suites based on arguments
            if self.args.quick:
                self._run_quick_tests()
            elif self.args.backend_only:
                self._run_backend_tests()
            elif self.args.frontend_only:
                self._run_frontend_tests()
            elif self.args.integration_only:
                self._run_integration_tests()
            else:
                # Run all tests
                self._run_all_test_suites()
            
        except KeyboardInterrupt:
            print(f"\n{Colors.WARNING}⚠ Test execution interrupted by user{Colors.ENDC}")
        except Exception as e:
            print(f"\n{Colors.FAIL}❌ Test execution failed: {e}{Colors.ENDC}")
        finally:
            self._print_final_summary()
    
    def _run_preflight_checks(self):
        """Run pre-flight checks before tests"""
        print(f"{Colors.HEADER}🔍 Pre-flight Checks{Colors.ENDC}")
        print("-" * 30)
        
        # Check Python dependencies
        self._check_dependencies()
        
        # Check server availability
        if not self.args.skip_servers:
            self._check_servers()
        
        # Check test files exist
        self._check_test_files()
        
        print()
    
    def _check_dependencies(self):
        """Check required Python dependencies"""
        required_packages = [
            'requests', 'numpy', 'selenium'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package}")
            except ImportError:
                missing_packages.append(package)
                print(f"❌ {package} - Not installed")
        
        if missing_packages:
            print(f"\n{Colors.WARNING}Missing packages detected. Install with:{Colors.ENDC}")
            print(f"pip install {' '.join(missing_packages)}")
            
            if not self.args.ignore_deps:
                print(f"{Colors.FAIL}Exiting due to missing dependencies. Use --ignore-deps to continue.{Colors.ENDC}")
                sys.exit(1)
    
    def _check_servers(self):
        """Check if backend and frontend servers are running"""
        print("🌐 Checking server availability...")
        
        # Check backend
        backend_ready = False
        try:
            response = requests.get(f"{TestConfig.BACKEND_URL}/test-cors", timeout=5)
            if response.status_code == 200:
                print(f"✓ Backend server ready at {TestConfig.BACKEND_URL}")
                backend_ready = True
            else:
                print(f"⚠ Backend server responding with status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"❌ Backend server not responding at {TestConfig.BACKEND_URL}")
            print("   Start with: python app.py (from backend directory)")
        
        # Check frontend
        frontend_ready = False
        try:
            response = requests.get(TestConfig.FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                print(f"✓ Frontend server ready at {TestConfig.FRONTEND_URL}")
                frontend_ready = True
            else:
                print(f"⚠ Frontend server responding with status {response.status_code}")
        except requests.exceptions.RequestException:
            print(f"❌ Frontend server not responding at {TestConfig.FRONTEND_URL}")
            print("   Start with: npm run dev (from project root)")
        
        if not backend_ready and not self.args.ignore_servers:
            print(f"{Colors.FAIL}Backend server required for testing. Use --ignore-servers to skip this check.{Colors.ENDC}")
            sys.exit(1)
    
    def _check_test_files(self):
        """Check that test files exist"""
        test_files = [
            'test_suite.py',
            'test_backend_api.py',
            'test_frontend_unit.py',
            'test_integration.py'
        ]
        
        missing_files = []
        for test_file in test_files:
            if (self.project_root / test_file).exists():
                print(f"✓ {test_file}")
            else:
                missing_files.append(test_file)
                print(f"❌ {test_file} - Not found")
        
        if missing_files:
            print(f"{Colors.WARNING}Some test files are missing. Tests may be incomplete.{Colors.ENDC}")
    
    def _run_quick_tests(self):
        """Run essential tests only"""
        print(f"{Colors.HEADER}⚡ Quick Test Mode{Colors.ENDC}")
        print("-" * 20)
        
        # Run essential backend tests
        self._run_single_test_suite("Backend API (Essential)", "test_backend_api.py", ["--endpoint", "CORS"])
        
        # Run basic frontend tests
        self._run_single_test_suite("Frontend (Basic)", "test_frontend_unit.py")
        
        print(f"{Colors.OKGREEN}✓ Quick tests completed{Colors.ENDC}")
    
    def _run_all_test_suites(self):
        """Run all test suites"""
        print(f"{Colors.HEADER}🧪 Running All Test Suites{Colors.ENDC}")
        print("-" * 30)
        
        # Backend tests
        self._run_backend_tests()
        
        # Frontend tests
        self._run_frontend_tests()
        
        # Integration tests
        self._run_integration_tests()
    
    def _run_backend_tests(self):
        """Run backend test suites"""
        print(f"\n{Colors.OKBLUE}🔧 Backend Test Suites{Colors.ENDC}")
        print("-" * 25)
        
        # API tests
        args = []
        if self.args.verbose:
            args.append("--verbose")
        
        self._run_single_test_suite("Backend API Tests", "test_backend_api.py", args)
    
    def _run_frontend_tests(self):
        """Run frontend test suites"""
        print(f"\n{Colors.OKBLUE}🌐 Frontend Test Suites{Colors.ENDC}")
        print("-" * 27)
        
        # Unit tests
        self._run_single_test_suite("Frontend Unit Tests", "test_frontend_unit.py")
        
        # Main test suite (includes Selenium)
        args = []
        if self.args.verbose:
            args.append("--verbose")
        if self.args.frontend_only:
            args.append("--frontend-only")
        
        self._run_single_test_suite("Frontend Integration", "test_suite.py", args)
    
    def _run_integration_tests(self):
        """Run integration test suites"""
        print(f"\n{Colors.OKBLUE}🔗 Integration Test Suites{Colors.ENDC}")
        print("-" * 30)
        
        args = []
        if self.args.verbose:
            args.append("--verbose")
        if self.args.headless:
            args.append("--headless")
        if self.args.slow:
            args.append("--slow")
        
        self._run_single_test_suite("Integration Tests", "test_integration.py", args)
    
    def _run_single_test_suite(self, suite_name, test_file, extra_args=None):
        """Run a single test suite"""
        print(f"\n📋 {suite_name}")
        print("-" * len(f"📋 {suite_name}"))
        
        test_path = self.project_root / test_file
        
        if not test_path.exists():
            print(f"{Colors.WARNING}⚠ Test file {test_file} not found - skipping{Colors.ENDC}")
            self.results['skipped_tests'] += 1
            self.results['test_suites'][suite_name] = {'status': 'skipped', 'reason': 'file not found'}
            return
        
        # Build command
        cmd = [sys.executable, str(test_path)]
        if extra_args:
            cmd.extend(extra_args)
        
        # Run test
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse output for summary information
            output_lines = result.stdout.split('\n') + result.stderr.split('\n')
            for line in output_lines:
                if ('✓' in line or '❌' in line or 'passed' in line.lower() or 
                    'failed' in line.lower() or 'working' in line.lower()):
                    print(line.strip())
            
            if result.returncode == 0:
                print(f"{Colors.OKGREEN}✅ {suite_name} completed successfully ({duration:.1f}s){Colors.ENDC}")
                self.results['test_suites'][suite_name] = {'status': 'passed', 'duration': duration}
                self.results['passed_tests'] += 1
            else:
                print(f"{Colors.FAIL}❌ {suite_name} failed ({duration:.1f}s){Colors.ENDC}")
                if self.args.verbose:
                    print("Error output:")
                    print(result.stderr)
                self.results['test_suites'][suite_name] = {'status': 'failed', 'duration': duration}
                self.results['failed_tests'] += 1
            
            self.results['total_tests'] += 1
            
        except Exception as e:
            print(f"{Colors.FAIL}❌ {suite_name} execution error: {e}{Colors.ENDC}")
            self.results['test_suites'][suite_name] = {'status': 'error', 'error': str(e)}
            self.results['failed_tests'] += 1
            self.results['total_tests'] += 1
    
    def _print_final_summary(self):
        """Print final test summary"""
        end_time = datetime.now()
        total_duration = end_time - self.start_time if self.start_time else 0
        
        print(f"\n{Colors.HEADER}")
        print("=" * 70)
        print("  FINAL TEST SUMMARY")
        print("=" * 70)
        print(f"{Colors.ENDC}")
        
        print(f"Started:  {self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else 'Unknown'}")
        print(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {total_duration.total_seconds():.1f} seconds")
        print()
        
        print(f"Total Test Suites: {self.results['total_tests']}")
        print(f"{Colors.OKGREEN}Passed: {self.results['passed_tests']}{Colors.ENDC}")
        print(f"{Colors.FAIL}Failed: {self.results['failed_tests']}{Colors.ENDC}")
        print(f"{Colors.WARNING}Skipped: {self.results['skipped_tests']}{Colors.ENDC}")
        
        if self.results['total_tests'] > 0:
            success_rate = (self.results['passed_tests'] / self.results['total_tests']) * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        # Print detailed results
        print(f"\n{Colors.HEADER}Detailed Results:{Colors.ENDC}")
        for suite_name, result in self.results['test_suites'].items():
            status = result['status']
            duration = result.get('duration', 0)
            
            if status == 'passed':
                status_icon = f"{Colors.OKGREEN}✅{Colors.ENDC}"
            elif status == 'failed':
                status_icon = f"{Colors.FAIL}❌{Colors.ENDC}"
            elif status == 'skipped':
                status_icon = f"{Colors.WARNING}⏭️{Colors.ENDC}"
            else:
                status_icon = f"{Colors.FAIL}💥{Colors.ENDC}"
            
            print(f"  {status_icon} {suite_name:<30} ({duration:.1f}s)")
        
        # Final status
        if self.results['failed_tests'] == 0:
            print(f"\n{Colors.OKGREEN}🎉 All test suites completed successfully!{Colors.ENDC}")
        else:
            print(f"\n{Colors.WARNING}⚠ {self.results['failed_tests']} test suite(s) failed.{Colors.ENDC}")
            print("Review the output above for details.")
        
        # Save results to file
        self._save_results()
        
        print(f"\n{Colors.HEADER}" + "=" * 70 + f"{Colors.ENDC}")
    
    def _save_results(self):
        """Save test results to JSON file"""
        try:
            results_file = self.project_root / "test_results.json"
            
            results_data = {
                'timestamp': datetime.now().isoformat(),
                'command_args': vars(self.args),
                'summary': {
                    'total_suites': self.results['total_tests'],
                    'passed_suites': self.results['passed_tests'],
                    'failed_suites': self.results['failed_tests'],
                    'skipped_suites': self.results['skipped_tests']
                },
                'test_suites': self.results['test_suites']
            }
            
            with open(results_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            
            print(f"📄 Test results saved to: {results_file}")
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Could not save test results: {e}{Colors.ENDC}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Master Test Runner for Speech Evaluation Application",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --quick           # Run only essential tests
  python run_tests.py --backend-only    # Run only backend tests
  python run_tests.py --frontend-only   # Run only frontend tests
  python run_tests.py --integration-only # Run only integration tests
  python run_tests.py --verbose         # Detailed output
  python run_tests.py --headless        # Run browser tests headless
        """
    )
    
    # Test selection
    parser.add_argument('--quick', action='store_true', 
                       help='Run only essential tests (faster)')
    parser.add_argument('--backend-only', action='store_true', 
                       help='Run only backend tests')
    parser.add_argument('--frontend-only', action='store_true', 
                       help='Run only frontend tests')
    parser.add_argument('--integration-only', action='store_true', 
                       help='Run only integration tests')
    
    # Test configuration
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Show detailed test output')
    parser.add_argument('--headless', action='store_true', 
                       help='Run browser tests in headless mode')
    parser.add_argument('--slow', action='store_true', 
                       help='Add delays between test suites')
    
    # Environment options
    parser.add_argument('--skip-checks', action='store_true', 
                       help='Skip pre-flight checks')
    parser.add_argument('--skip-servers', action='store_true', 
                       help='Skip server availability checks')
    parser.add_argument('--ignore-deps', action='store_true', 
                       help='Continue even if dependencies are missing')
    parser.add_argument('--ignore-servers', action='store_true', 
                       help='Continue even if servers are not responding')
    
    args = parser.parse_args()
    
    # Run tests
    runner = TestRunner(args)
    runner.run_all_tests()

if __name__ == "__main__":
    main() 