from flask import Flask
from flask_cors import CORS
from config import FLASK_PORT, FLASK_DEBUG

# Import blueprints
from routes.applicant import applicant_bp
from routes.admin import admin_bp
from routes.questions import questions_bp
from routes.audio import audio_bp
from routes.typing import typing_bp
from routes.written import written_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Simple CORS configuration
    CORS(app, origins=["http://localhost:5173"], supports_credentials=True)
    
    # Enable Flask's built-in reloader
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Register blueprints
    app.register_blueprint(applicant_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(typing_bp)
    app.register_blueprint(written_bp)
    
    # Add a simple test route to verify CORS
    @app.route('/test-cors', methods=['GET', 'OPTIONS'])
    def test_cors():
        from flask import request, jsonify
        if request.method == 'OPTIONS':
            return jsonify({"message": "CORS preflight OK"})
        return jsonify({"message": "CORS is working!", "status": "success"})
    
    return app

if __name__ == "__main__":
    app = create_app()
    
    print(f"🚀 Starting Flask server on port {FLASK_PORT}")
    print(f"🌐 Server will be available at: http://localhost:{FLASK_PORT}")
    print(f"🔧 Debug mode: {'ON' if FLASK_DEBUG else 'OFF'}")
    print(f"📱 CORS enabled for: http://localhost:5173")
    print("\n" + "="*50)
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=FLASK_DEBUG)
