#!/usr/bin/env python3
"""
Test script for the UpdateDetector class.
"""
import os
import json
from src.update.detection import UpdateDetector

def main():
    """Test the UpdateDetector implementation."""
    print("Testing Update Detector")
    print("======================")
    
    # Create a simple config
    config = {
        'storage': {
            'cache_dir': '/var/lib/ota/cache',
        },
        'product': {
            'type': 'robot-ai-standard',
            'version_file': '/etc/robot-ai/version',
        }
    }
    
    # Instantiate the detector
    detector = UpdateDetector(config)
    
    # Test getting current version
    current_version = detector.get_current_version()
    print(f"Current version: {current_version}")
    
    # Test checking for updates
    print("\nChecking for updates...")
    update_available, update_info = detector.check_for_update()
    
    if update_available:
        print(f"Update available: {update_info.get('version')}")
        print(f"Release notes: {update_info.get('release_notes')}")
        print(f"Update URL: {update_info.get('update_url')}")
    else:
        print("No update available")
        
    # Also verify the manifest file exists
    manifest_path = os.path.join('/var/lib/ota/cache', 'latest_manifest.json')
    if os.path.exists(manifest_path):
        print(f"\nManifest file exists at: {manifest_path}")
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            print(f"Manifest version: {manifest.get('version')}")
    else:
        print(f"\nManifest file does not exist at: {manifest_path}")

if __name__ == "__main__":
    main() 