"""HTTP-specific error handles for Flask routes"""
from flask import jsonify

def register_error_handlers(app):
    """REgister all error handlers with the Flask app"""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle bad request errors"""
        #logging the details
        app.logger.warning(f"Bad request: {error}")
        return jsonify({"error": "Bad request",
                        "message": str(error.description)
                        if hasattr(error, 'description')
                        else "Invalid request"}), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle not found errors"""
        app.logger.warning(f"Resource not found: {error}")

        return jsonify({"error": "Not found", "message": str(error.description)
                        if hasattr(error, 'description')
                        else "Resource not found"}), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle wrong HTTP method"""
        app.logger.warning(f"Method not allowed: {error}")
        return jsonify({"error": "Method not allowed"}), 405
    
    @app.errorhandler(409)
    def conflict_error(error):
        """Handle conflict errors"""
        app.logger.warning(f"Conflict error: {error}")
        return jsonify({"error": "Conflict error"}), 409
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle server errors"""
        app.logger.exception("Internal server error occurred")
        return jsonify({"error": "server error", "message": "An internal error ocurred"}), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catch-all for unexpected errors"""
        app.logger.exception(f"Unexpected error occurred: {type(error).__name__} - {str(error)}")
        return jsonify({"error": "server error", "message": "Unexpected error occurred"}), 500
 