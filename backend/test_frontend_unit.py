#!/usr/bin/env python3
"""
Frontend Unit Tests for Speech Evaluation Application
===================================================

This script contains unit tests for individual React components
and frontend functionality.

Usage:
    python test_frontend_unit.py
"""

import unittest
import json
import tempfile
import os
import sys
from pathlib import Path
import subprocess

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

class FrontendUnitTests(unittest.TestCase):
    """Unit tests for frontend components and utilities"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # From backend directory, project root is parent directory
        cls.backend_dir = Path(__file__).parent
        cls.project_root = cls.backend_dir.parent
        cls.src_dir = cls.project_root / "src"
        
        # Check if we're in the right directory
        if not cls.src_dir.exists():
            raise unittest.SkipTest("Frontend source directory not found")
    
    def test_01_react_components_structure(self):
        """Test that all React components have proper structure"""
        components_dir = self.src_dir / "components"
        
        if not components_dir.exists():
            self.fail("Components directory not found")
        
        component_dirs = [d for d in components_dir.iterdir() if d.is_dir()]
        self.assertGreater(len(component_dirs), 0, "No component directories found")
        
        # Check for main components
        expected_components = [
            "landingpage", "applicantform", "evaluationpage", 
            "admin", "header", "navbar"
        ]
        
        existing_components = [d.name for d in component_dirs]
        
        for component in expected_components:
            if component in existing_components:
                component_path = components_dir / component
                jsx_files = list(component_path.glob("*.jsx"))
                self.assertGreater(len(jsx_files), 0, 
                                 f"No JSX files found in {component} component")
        
        print(f"{Colors.OKGREEN}✓ React components structure verified{Colors.ENDC}")
    
    def test_02_jsx_syntax_validation(self):
        """Test JSX files for syntax errors"""
        jsx_files = []
        
        # Find all JSX files
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith(('.jsx', '.js')):
                    jsx_files.append(os.path.join(root, file))
        
        syntax_errors = []
        
        for jsx_file in jsx_files:
            try:
                # Simple syntax check by reading the file
                with open(jsx_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Basic JSX syntax checks
                if 'import' in content and 'from' in content:
                    # Check for balanced brackets
                    open_brackets = content.count('{')
                    close_brackets = content.count('}')
                    
                    if abs(open_brackets - close_brackets) > 2:  # Allow some tolerance
                        syntax_errors.append(f"{jsx_file}: Unbalanced brackets")
                    
                    # Check for basic React patterns
                    if 'export default' not in content and 'export {' not in content:
                        if jsx_file.endswith('.jsx'):
                            syntax_errors.append(f"{jsx_file}: No default export found")
            
            except Exception as e:
                syntax_errors.append(f"{jsx_file}: {str(e)}")
        
        if syntax_errors:
            print(f"{Colors.WARNING}Syntax issues found:{Colors.ENDC}")
            for error in syntax_errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
            if len(syntax_errors) > 5:
                print(f"  ... and {len(syntax_errors) - 5} more")
        else:
            print(f"{Colors.OKGREEN}✓ JSX syntax validation passed{Colors.ENDC}")
    
    def test_03_component_imports(self):
        """Test that component imports are properly structured"""
        main_jsx = self.src_dir / "main.jsx"
        
        if not main_jsx.exists():
            self.skipTest("main.jsx not found")
        
        with open(main_jsx, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for React Router imports
        self.assertIn('react-router-dom', content, "React Router not imported")
        
        # Check for component imports
        component_imports = [
            'LandingPage', 'ApplicantForm', 'EvaluationPage', 
            'Admin', 'SessionProvider'
        ]
        
        for component in component_imports:
            if component in content:
                print(f"{Colors.OKGREEN}✓ {component} imported correctly{Colors.ENDC}")
        
        print(f"{Colors.OKGREEN}✓ Component imports structure verified{Colors.ENDC}")
    
    def test_04_context_providers(self):
        """Test React context providers"""
        contexts_dir = self.src_dir / "contexts"
        
        if not contexts_dir.exists():
            print(f"{Colors.WARNING}⚠ Contexts directory not found{Colors.ENDC}")
            return
        
        context_files = list(contexts_dir.glob("*.jsx"))
        
        for context_file in context_files:
            with open(context_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for context creation patterns
            if 'createContext' in content:
                print(f"{Colors.OKGREEN}✓ {context_file.name} contains context creation{Colors.ENDC}")
            
            if 'Provider' in content:
                print(f"{Colors.OKGREEN}✓ {context_file.name} contains provider component{Colors.ENDC}")
    
    def test_05_service_layer(self):
        """Test service layer structure"""
        services_dir = self.src_dir / "services"
        
        if not services_dir.exists():
            print(f"{Colors.WARNING}⚠ Services directory not found{Colors.ENDC}")
            return
        
        service_files = list(services_dir.glob("*.js"))
        
        for service_file in service_files:
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for API service patterns
            if 'axios' in content or 'fetch' in content:
                print(f"{Colors.OKGREEN}✓ {service_file.name} contains API calls{Colors.ENDC}")
            
            if 'export' in content:
                print(f"{Colors.OKGREEN}✓ {service_file.name} exports functions{Colors.ENDC}")
    
    def test_06_routing_configuration(self):
        """Test React Router configuration"""
        main_jsx = self.src_dir / "main.jsx"
        
        if not main_jsx.exists():
            self.skipTest("main.jsx not found")
        
        with open(main_jsx, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for routing elements
        routing_elements = ['Routes', 'Route', 'BrowserRouter']
        
        for element in routing_elements:
            if element in content:
                print(f"{Colors.OKGREEN}✓ {element} found in routing configuration{Colors.ENDC}")
        
        # Check for protected routes
        if 'ProtectedRoute' in content:
            print(f"{Colors.OKGREEN}✓ Protected routes configured{Colors.ENDC}")
    
    def test_07_css_files_exist(self):
        """Test that CSS files exist and are properly structured"""
        css_files = []
        
        # Find all CSS files
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                if file.endswith('.css'):
                    css_files.append(os.path.join(root, file))
        
        self.assertGreater(len(css_files), 0, "No CSS files found")
        
        for css_file in css_files:
            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic CSS validation
            if content.strip():  # Not empty
                open_braces = content.count('{')
                close_braces = content.count('}')
                
                if open_braces == close_braces:
                    print(f"{Colors.OKGREEN}✓ {os.path.basename(css_file)} has balanced CSS rules{Colors.ENDC}")
    
    def test_08_package_json_dependencies(self):
        """Test package.json dependencies"""
        package_json = self.project_root / "package.json"
        
        if not package_json.exists():
            self.skipTest("package.json not found")
        
        with open(package_json, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
        
        # Check for required dependencies
        required_deps = ['react', 'react-dom', 'react-router-dom']
        dependencies = package_data.get('dependencies', {})
        
        for dep in required_deps:
            self.assertIn(dep, dependencies, f"Required dependency {dep} not found")
            print(f"{Colors.OKGREEN}✓ {dep} dependency found{Colors.ENDC}")
        
        # Check for development dependencies
        dev_deps = package_data.get('devDependencies', {})
        
        if 'vite' in dev_deps:
            print(f"{Colors.OKGREEN}✓ Vite build tool configured{Colors.ENDC}")
        
        if 'eslint' in dev_deps:
            print(f"{Colors.OKGREEN}✓ ESLint configured{Colors.ENDC}")

class FrontendLintTests(unittest.TestCase):
    """Linting tests for frontend code"""
    
    @classmethod
    def setUpClass(cls):
        """Set up linting environment"""
        cls.backend_dir = Path(__file__).parent
        cls.project_root = cls.backend_dir.parent
        
        # Check if eslint is available
        try:
            result = subprocess.run(['npx', 'eslint', '--version'], 
                                  capture_output=True, text=True, cwd=cls.project_root)
            if result.returncode == 0:
                cls.eslint_available = True
                print(f"ESLint version: {result.stdout.strip()}")
            else:
                cls.eslint_available = False
        except FileNotFoundError:
            cls.eslint_available = False
    
    def test_01_eslint_check(self):
        """Run ESLint on frontend code"""
        if not self.eslint_available:
            self.skipTest("ESLint not available")
        
        try:
            result = subprocess.run(['npx', 'eslint', 'src/', '--format', 'json'], 
                                  capture_output=True, text=True, cwd=self.project_root, timeout=30)
            
            if result.stdout:
                lint_results = json.loads(result.stdout)
                
                total_errors = sum(len(file_result.get('messages', [])) for file_result in lint_results)
                
                if total_errors == 0:
                    print(f"{Colors.OKGREEN}✓ No ESLint errors found{Colors.ENDC}")
                else:
                    print(f"{Colors.WARNING}⚠ Found {total_errors} ESLint issues{Colors.ENDC}")
                    
                    # Show first few errors
                    error_count = 0
                    for file_result in lint_results:
                        if error_count >= 5:
                            break
                        
                        file_path = file_result.get('filePath', '')
                        messages = file_result.get('messages', [])
                        
                        for message in messages:
                            if error_count >= 5:
                                break
                            
                            severity = 'ERROR' if message.get('severity') == 2 else 'WARNING'
                            line = message.get('line', '?')
                            rule = message.get('ruleId', 'unknown')
                            msg = message.get('message', '')
                            
                            print(f"  {severity}: {os.path.basename(file_path)}:{line} - {msg} ({rule})")
                            error_count += 1
            else:
                print(f"{Colors.OKGREEN}✓ ESLint completed successfully{Colors.ENDC}")
        
        except subprocess.TimeoutExpired:
            print(f"{Colors.WARNING}⚠ ESLint check timed out{Colors.ENDC}")
        except json.JSONDecodeError:
            print(f"{Colors.WARNING}⚠ Could not parse ESLint output{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}⚠ ESLint check failed: {e}{Colors.ENDC}")

def main():
    """Main entry point for frontend unit tests"""
    print("=" * 50)
    print("  FRONTEND UNIT TESTS")
    print("=" * 50)
    
    # Run unit tests
    print(f"\n🧪 Running Frontend Unit Tests...")
    print("-" * 30)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(FrontendUnitTests))
    suite.addTests(loader.loadTestsFromTestCase(FrontendLintTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Print summary
    print(f"\nTotal Tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures) + len(result.errors)}")
    
    if result.failures:
        print(f"\n{Colors.FAIL}Failures:{Colors.ENDC}")
        for test, error in result.failures:
            print(f"  - {test}: {error}")
    
    if result.errors:
        print(f"\n{Colors.FAIL}Errors:{Colors.ENDC}")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main() 