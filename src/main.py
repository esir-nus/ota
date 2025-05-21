#!/usr/bin/env python3
"""
OTA Daemon Main Entry Point (MVP Version)
Initializes and runs the OTA update daemon.
"""

import os
import sys
import signal
import argparse
import logging
import yaml
import structlog
from typing import Dict, Any

# Import core components
from src.update.detection import UpdateDetector
from src.update.execution import UpdateExecutor
from src.update.backup.backup import BackupManager
from src.scheduler.scheduler import UpdateScheduler
from src.validation.validator import UpdateValidator
from src.api.endpoints import init_api, run_api_server

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=False
)

logger = structlog.get_logger()

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict with configuration
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info("Loaded configuration", path=config_path)
        return config
    except Exception as e:
        logger.error("Failed to load configuration", path=config_path, error=str(e))
        sys.exit(1)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    def handle_signal(signum, frame):
        logger.info("Received shutdown signal", signal=signum)
        # Cleanup and exit
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    logger.info("Signal handlers configured")

def main():
    """Main entry point for the OTA daemon."""
    parser = argparse.ArgumentParser(description="OTA Update Daemon")
    parser.add_argument("--config", default="/etc/ota/config.yml", help="Path to configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--host", default="0.0.0.0", help="API server host")
    parser.add_argument("--port", type=int, default=5000, help="API server port")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.debug:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG)
        )
        logger.info("Debug mode enabled")
    
    # Set up signal handlers
    setup_signal_handlers()
    
    # Load configuration
    config = load_config(args.config)
    
    try:
        # Initialize API and components
        logger.info("Initializing OTA daemon components")
        
        # Create backup directory if it doesn't exist
        backup_dir = config.get('storage', {}).get('backup_dir', '/var/lib/ota/backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create downloads directory if it doesn't exist
        download_dir = config.get('storage', {}).get('download_dir', '/var/lib/ota/downloads')
        os.makedirs(download_dir, exist_ok=True)
        
        # Create cache directory if it doesn't exist
        cache_dir = config.get('storage', {}).get('cache_dir', '/var/lib/ota/cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        # Create db directory if it doesn't exist
        db_dir = os.path.dirname(config.get('storage', {}).get('db_path', '/var/lib/ota/scheduler.db'))
        os.makedirs(db_dir, exist_ok=True)
        
        # Initialize API with all components
        init_api(config)
        
        # Start API server
        logger.info("Starting OTA daemon API server", 
                  host=args.host, 
                  port=args.port)
        run_api_server(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
    except KeyboardInterrupt:
        logger.info("OTA daemon shutting down")
    except Exception as e:
        logger.error("OTA daemon error", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    main() 