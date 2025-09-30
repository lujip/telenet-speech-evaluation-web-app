from flask import Flask
from flask_cors import CORS
from config import FLASK_PORT, FLASK_DEBUG, FLASK_ENV
import os

# Import blueprints
from routes.applicant import applicant_bp
from routes.admin import admin_bp
from routes.questions import questions_bp
from routes.audio import audio_bp
from routes.typing import typing_bp
from routes.written import written_bp
from routes.personality import personality_bp
from routes.users import users_bp

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    # Simple CORS configuration
    CORS(app, origins=[
    "https://localhost:5173",
    "https://192.168.77.123:5173",
    "https://192.168.77.74:5173", # ← tele mongo https
    "https://localhost:3000",
    "https://192.168.77.123:3000",
    "http://localhost:3000",           # ← Add this
    "http://192.168.77.74:5173",         # ← tele mongo http
    "http://192.168.77.123:3000"], supports_credentials=True)
    
    # Enable Flask's built-in reloader
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Register blueprints
    app.register_blueprint(applicant_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(questions_bp)
    app.register_blueprint(audio_bp)
    app.register_blueprint(typing_bp)
    app.register_blueprint(written_bp)
    app.register_blueprint(personality_bp)
    app.register_blueprint(users_bp)
    
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
    print(f"🏗️  Environment: {FLASK_ENV}")
    
    if FLASK_DEBUG:
        print("\n⚠️  PERFORMANCE NOTICE:")
        print("   Debug mode can consume high CPU/RAM due to file watching")
        print("   To improve performance:")
        print("   1. Set FLASK_ENV=production in your environment, OR")
        print("   2. Uncomment FLASK_DEBUG=False in config.py, OR")
        print("   3. Run: set FLASK_ENV=production && python app.py")
        print("   4. Use: python app.py --no-reload (if supported)")
        
    print("\n" + "="*50)
    print("="*50 + "\n")
    
    # Use threaded mode for better performance
    app.run(
        host='0.0.0.0', 
        port=FLASK_PORT, 
       # debug=FLASK_DEBUG,
       # threaded=True,
       # use_reloader=FLASK_DEBUG,  # Only use reloader in debug mode
        ssl_context=("cert.pem", "key.pem")
    )
