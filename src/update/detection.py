# UpdateDetector module for OTA daemon
import os
import json
from typing import Dict, Any, Tuple, Optional
import structlog

logger = structlog.get_logger()

class UpdateDetector:
    """Handles update detection and notification."""
    
    def __init__(self, config=None):
        self.available_updates = []
        self.config = config or {}
        self.cache_dir = self.config.get('storage', {}).get('cache_dir', '/var/lib/ota/cache')
        self.manifest_path = os.path.join(self.cache_dir, "latest_manifest.json")
    
    def check_for_updates(self) -> bool:
        """Check for available updates."""
        try:
            # Check if manifest exists
            if not os.path.exists(self.manifest_path):
                logger.info("No manifest file found", path=self.manifest_path)
                return False
            
            # Read manifest
            with open(self.manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Get current version
            current_version = self.get_current_version()
            manifest_version = manifest.get('version')
            
            # Compare versions
            if manifest_version > current_version:
                logger.info("Update available", 
                          current_version=current_version,
                          new_version=manifest_version)
                self.available_updates = [manifest]
                return True
            else:
                logger.info("No update available", 
                          current_version=current_version,
                          manifest_version=manifest_version)
                return False
        except Exception as e:
            logger.error("Error checking for updates", error=str(e))
            return False
    
    def check_for_update(self) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check for update and return manifest info if available."""
        update_available = self.check_for_updates()
        
        if update_available and self.available_updates:
            return True, self.available_updates[0]
        
        return False, None
    
    def get_available_updates(self):
        """Get list of available updates."""
        return self.available_updates
        
    def get_current_version(self):
        """Get the currently installed version."""
        if self.config and 'product' in self.config:
            version_file = self.config.get('product', {}).get('version_file')
            if version_file and os.path.exists(version_file):
                try:
                    with open(version_file, 'r') as f:
                        return f.read().strip()
                except Exception as e:
                    logger.error("Error reading version file", 
                                path=version_file, 
                                error=str(e))
        
        # Default version for testing
        return "1.0.0"
