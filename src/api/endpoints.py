"""
API Endpoints Module (MVP Version)
Provides REST API for OTA update system integration.

This module implements the REST API endpoints for the OTA system, providing 
external services (including the robot-ai system) with access to OTA functionality
without requiring modifications to their code.

Key features:
- Status checking and monitoring
- Manual update triggering
- Update history retrieval
- Real-time notifications via WebSockets
- API key-based authentication and authorization
"""

import os
import json
import datetime
import secrets
import structlog
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, abort, Response
from flask_socketio import SocketIO
from functools import wraps

# Import from other modules
from src.update.detection import UpdateDetector
from src.update.execution import UpdateExecutor
from src.scheduler.scheduler import UpdateScheduler

logger = structlog.get_logger()

# Create Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('OTA_API_SECRET_KEY', secrets.token_hex(16))
socketio = SocketIO(app, cors_allowed_origins="*")

# Global objects (will be set during initialization)
update_detector = None
update_executor = None
update_scheduler = None

# Store for API keys (in-memory for MVP, would use a database in production)
# This should be replaced with proper authentication in a full implementation
api_keys = {}


def init_api(config: Dict[str, Any]) -> None:
    """Initialize the API with configuration.
    
    Args:
        config: Configuration dictionary
    """
    global update_detector, update_executor, update_scheduler
    
    # Initialize components
    update_detector = UpdateDetector(config)
    update_executor = UpdateExecutor(config)
    update_scheduler = UpdateScheduler(config)
    
    # Start scheduler
    update_scheduler.start()
    
    # Set up API keys from configuration
    setup_api_keys(config)
    
    logger.info("API endpoints initialized")


def setup_api_keys(config: Dict[str, Any]) -> None:
    """Set up API keys from configuration.
    
    Args:
        config: Configuration dictionary
    """
    global api_keys
    
    # Get API keys from config
    configured_keys = config.get('api', {}).get('keys', {})
    
    # Store API keys with their permissions
    for key_id, key_info in configured_keys.items():
        api_key = key_info.get('key')
        permissions = key_info.get('permissions', ['status'])
        
        if api_key:
            api_keys[api_key] = {
                'id': key_id,
                'permissions': permissions
            }
    
    # Generate a default key if none exists (for MVP only)
    if not api_keys:
        default_key = secrets.token_hex(16)
        api_keys[default_key] = {
            'id': 'default',
            'permissions': ['status', 'check', 'apply']
        }
        logger.warning("No API keys configured, generated default key", key=default_key)


def require_api_key(permission: str = None):
    """Decorator to require API key for endpoint access.
    
    Args:
        permission: Required permission
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get API key from header or query parameter
            api_key = request.headers.get('X-API-Key')
            if not api_key:
                api_key = request.args.get('api_key')
            
            # Check if API key exists and has permission
            if api_key not in api_keys:
                logger.warning("Invalid API key", 
                             remote_addr=request.remote_addr)
                abort(401)  # Unauthorized
                
            if permission and permission not in api_keys[api_key]['permissions']:
                logger.warning("Insufficient permissions", 
                             key_id=api_keys[api_key]['id'],
                             required=permission)
                abort(403)  # Forbidden
                
            # Add key info to request
            request.api_key_id = api_keys[api_key]['id']
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Define API endpoints
@app.route('/api/v1/status', methods=['GET'])
@require_api_key('status')
def get_status():
    """Get OTA system status.
    
    Returns the current system status including version information,
    scheduler state, and last check time.
    
    Returns:
        JSON object with:
        - status: 'ok' or 'error'
        - current_version: The currently installed version
        - scheduler: Current scheduler status information
        - last_check: Timestamp of the last update check
        
    HTTP Status:
        - 200: Success
        - 500: Internal error
    """
    try:
        current_version = update_detector.get_current_version()
        
        status = {
            'status': 'ok',
            'current_version': current_version,
            'scheduler': update_scheduler.get_status() if update_scheduler else None,
            'last_check': None
        }
        
        # Get last check from history
        history = update_scheduler.get_update_history(1) if update_scheduler else []
        if history:
            status['last_check'] = history[0]
        
        return jsonify(status)
    except Exception as e:
        logger.error("Error getting status", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/v1/check', methods=['POST'])
@require_api_key('check')
def check_update():
    """Check for updates.
    
    Initiates an immediate check for updates from the configured update server.
    This is an asynchronous operation - the API returns immediately while
    the check happens in the background.
    
    Returns:
        JSON object with:
        - status: 'ok' or 'error'
        - message: Description of the operation status
        
    Also triggers a WebSocket 'update_check_complete' event when finished.
    
    HTTP Status:
        - 200: Check initiated successfully
        - 500: Internal error
    """
    try:
        result = update_scheduler.check_now()
        
        # Emit WebSocket event
        socketio.emit('update_check_complete', result)
        
        return jsonify(result)
    except Exception as e:
        logger.error("Error checking for updates", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/v1/apply', methods=['POST'])
@require_api_key('apply')
def apply_update():
    """Apply pending update.
    
    Initiates the installation of a pending update if one is available.
    This is an asynchronous operation - the API returns immediately while
    the update process happens in the background.
    
    Returns:
        JSON object with:
        - status: 'ok' or 'error'
        - message: Description of the operation status
        
    Also triggers a WebSocket 'update_applied' event when finished.
    
    HTTP Status:
        - 200: Update process initiated successfully
        - 500: Internal error
    """
    try:
        result = update_scheduler.apply_pending_update()
        
        # Emit WebSocket event
        socketio.emit('update_applied', result)
        
        return jsonify(result)
    except Exception as e:
        logger.error("Error applying update", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/v1/history', methods=['GET'])
@require_api_key('status')
def get_history():
    """Get update history.
    
    Retrieves the history of update checks and installations.
    
    Query Parameters:
        - limit: Maximum number of history entries to return (default: 10)
    
    Returns:
        JSON object with:
        - history: List of history entries, each containing:
            - timestamp: When the event occurred
            - type: 'check' or 'update'
            - status: Result status
            - details: Additional information
    
    HTTP Status:
        - 200: Success
        - 500: Internal error
    """
    try:
        limit = request.args.get('limit', default=10, type=int)
        history = update_scheduler.get_update_history(limit)
        
        return jsonify({
            'history': history
        })
    except Exception as e:
        logger.error("Error getting update history", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/v1/scheduler/status', methods=['GET'])
@require_api_key('status')
def get_scheduler_status():
    """Get scheduler status.
    
    Retrieves the current status of the update scheduler including:
    - Next scheduled update check time
    - Whether updates are currently enabled
    - Current scheduler state
    
    Returns:
        JSON object with scheduler status details
    
    HTTP Status:
        - 200: Success
        - 500: Internal error
    """
    try:
        status = update_scheduler.get_status()
        return jsonify(status)
    except Exception as e:
        logger.error("Error getting scheduler status", error=str(e))
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    logger.info("Client connected to WebSocket", sid=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logger.info("Client disconnected from WebSocket", sid=request.sid)


# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'status': 'error',
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(401)
def unauthorized(error):
    """Handle 401 errors."""
    return jsonify({
        'status': 'error',
        'error': 'Unauthorized'
    }), 401


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    return jsonify({
        'status': 'error',
        'error': 'Forbidden'
    }), 403


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    logger.error("Unhandled server error", error=str(error))
    return jsonify({
        'status': 'error',
        'error': 'Internal server error'
    }), 500


def run_api_server(host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
    """Run the API server.
    
    Starts the Flask web server with the configured endpoints.
    This function blocks until the server is stopped.
    
    Args:
        host: Host to bind the server to (default: '0.0.0.0')
        port: Port to listen on (default: 5000)
        debug: Whether to enable debug mode (default: False)
    """
    logger.info("Starting API server", host=host, port=port)
    socketio.run(app, host=host, port=port, debug=debug) 