from flask import Flask
from flask_cors import CORS
from config import FLASK_PORT, FLASK_DEBUG

# Import blueprints
from routes.applicant import applicant_bp
from routes.admin import admin_bp
from routes.questions import questions_bp
from routes.audio import audio_bp
from routes.typing import typing_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(applicant_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(typing_bp)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=FLASK_PORT, debug=FLASK_DEBUG)
