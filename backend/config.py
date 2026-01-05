import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# File paths
APPLICANTS_FILE = "data/applicants.json"
RECORDINGS_DIR = "recordings"
RESUME_DIR = "data/resume"
QUESTIONS_FILE = "data/questions/questions.json"
LISTENING_TEST_QUESTIONS_FILE = "data/questions/listening_test_questions.json"
TYPING_TESTS_FILE = "data/questions/typing_tests.json"
WRITTEN_TEST_QUESTIONS_FILE = "data/questions/written_test_questions.json"
USERS_FILE = "data/users.json"

# Legacy admin credentials (for migration/fallback) - DEPRECATED
# Use MongoDB to create admin users or API calls instead
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Default super admin credentials removed for security
# Create admin users directly via MongoDB or use the API endpoint
DEFAULT_SUPER_ADMIN = None

# User roles and permissions
USER_ROLES = {
    "super_admin": {
        "name": "Super Admin",
        "permissions": ["*"]  # All permissions
    },
    "admin": {
        "name": "Admin", 
        "permissions": [
            "view_applicants", "edit_applicants", "delete_applicants",
            "view_questions", "edit_questions", "delete_questions",
            "view_evaluations", "edit_evaluations",
            "add_comments", "delete_comments",
            "view_analytics", "manage_users", "view_users"
        ]
    },
    "evaluator": {
        "name": "Evaluator",
        "permissions": [
            "view_applicants", "view_questions", "view_evaluations", 
            "edit_evaluations", "add_comments", "view_users", "edit_own_profile"
        ]
    },
    "viewer": {
        "name": "Viewer",
        "permissions": [
            "view_applicants", "view_questions", "view_evaluations"
        ]
    }
}

# Flask configuration
FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

# Environment-based debug setting
# Set FLASK_ENV=production in environment to disable debug mode
FLASK_ENV = os.getenv("FLASK_ENV", "production")
FLASK_DEBUG = FLASK_ENV == "development"

# Alternative: Uncomment the line below to force disable debug mode for better performance
# FLASK_DEBUG = False

# Session management
MAX_QUESTIONS_PER_SESSION = 5

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY environment variable must be set in .env file")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24")) 
