"""
Face Recognition Biometric System - Main Application
Refactored version using blueprints for better organization
"""
from flask import Flask
import os
from utils.logger import setup_logger, get_logger
from config import (
    DATABASE, SECRET_KEY, DEBUG, HOST, PORT,
    SSL_CERT_PATH, SSL_KEY_PATH, LOG_FILE, LOG_LEVEL
)

# Setup logging
logger = setup_logger(__name__, LOG_FILE, LOG_LEVEL)

# Create Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['DEBUG'] = DEBUG

# Register blueprints
from blueprints import auth_bp, admin_bp, employee_bp, api_bp
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(employee_bp)
app.register_blueprint(api_bp)

logger.info("Flask application initialized with blueprints")


# ================= DATABASE CONNECTION =================
from db import get_db, close_db

@app.teardown_appcontext
def teardown_db(exception):
    """Close database connection at the end of request"""
    close_db(exception)


# ================= SERVER HEADER =================
@app.after_request
def hide_server_header(response):
    """Hide server information from HTTP headers for security"""
    response.headers['Server'] = 'SecureServer'
    return response


# ================= ERROR HANDLERS =================
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {error}")
    from flask import render_template
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {str(error)}", exc_info=True)
    from flask import render_template
    return render_template('errors/500.html'), 500


# ================= APPLICATION FACTORY (if needed) =================
def create_app(config=None):
    """Application factory pattern (for testing and flexibility)"""
    app_instance = Flask(__name__)
    app_instance.secret_key = SECRET_KEY
    app_instance.config['DEBUG'] = DEBUG
    
    if config:
        app_instance.config.update(config)
    
    # Register blueprints
    from blueprints import auth_bp, admin_bp, employee_bp, api_bp
    app_instance.register_blueprint(auth_bp)
    app_instance.register_blueprint(admin_bp)
    app_instance.register_blueprint(employee_bp)
    app_instance.register_blueprint(api_bp)
    
    # Register database function
    from db import close_db
    app_instance.teardown_appcontext(close_db)
    
    return app_instance


# ================= MAIN ENTRY POINT =================
if __name__ == "__main__":
    # Check if SSL certificates exist for HTTPS
    ssl_context = None
    
    if os.path.exists(SSL_CERT_PATH) and os.path.exists(SSL_KEY_PATH):
        ssl_context = (SSL_CERT_PATH, SSL_KEY_PATH)
        logger.info("=" * 50)
        logger.info("🔒 HTTPS Enabled - Using SSL certificates")
        logger.info("=" * 50)
        logger.info(f"Access the app via: https://YOUR_IP:{PORT}")
    else:
        logger.warning("=" * 50)
        logger.warning("⚠️  HTTP Mode - Camera may not work from remote devices")
        logger.warning("=" * 50)
        logger.warning("To enable HTTPS (required for camera access from IP address):")
        logger.warning("  1. Run: ./setup_https.sh")
        logger.warning("  2. Restart the app")
        logger.warning(f"  3. Access via: https://YOUR_IP:{PORT}")
        logger.warning("=" * 50)
    
    # Run with threading enabled to handle concurrent requests
    try:
        if ssl_context:
            logger.info(f"Starting Flask app with HTTPS on {HOST}:{PORT}")
            app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True, ssl_context=ssl_context)
        else:
            logger.info(f"Starting Flask app with HTTP on {HOST}:{PORT}")
            app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
    except Exception as e:
        logger.error(f"Error starting Flask app: {str(e)}", exc_info=True)
        raise