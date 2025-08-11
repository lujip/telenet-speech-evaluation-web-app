import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File paths
APPLICANTS_FILE = "data/applicants.json"
RECORDINGS_DIR = "recordings"
QUESTIONS_FILE = "data/questions.json"
TYPING_TESTS_FILE = "data/typing_tests.json"

# Admin credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Flask configuration
FLASK_PORT = 5000
FLASK_DEBUG = True

# Session management
MAX_QUESTIONS_PER_SESSION = 5 