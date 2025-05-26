#!/usr/bin/env python3
"""
Test script for the UpdateDetector class.
"""

import os
import json
from src.update.detection import UpdateDetector

def main():
    """Test the UpdateDetector implementation."""
    print("Testing UpdateDetector class")
    print("===========================")
    
    # Create a basic config
    config = {
        'storage': {
            'cache_dir': '/var/lib/ota/cache'
        },
        'product': {
            'version_file': '/tmp/version.txt'
        }
    }
    
    # Create a test version file
    with open('/tmp/version.txt', 'w') as f:
        f.write('1.0.0')
    
    # Create a test manifest
    manifest_dir = config['storage']['cache_dir']
    os.makedirs(manifest_dir, exist_ok=True)
    
    with open(os.path.join(manifest_dir, 'latest_manifest.json'), 'w') as f:
        json.dump({
            'version': '1.1.0',
            'release_notes': 'Test update',
            'download_url': 'http://example.com/update.zip'
        }, f)
    
    # Initialize detector
    detector = UpdateDetector(config)
    
    # Test check_for_updates method
    print("\nTesting check_for_updates() method:")
    result = detector.check_for_updates()
    print(f"Update available: {result}")
    
    # Test check_for_update method
    print("\nTesting check_for_update() method:")
    available, info = detector.check_for_update()
    print(f"Update available: {available}")
    print(f"Update info: {info}")
    
    # Clean up
    os.remove('/tmp/version.txt')

if __name__ == "__main__":
    main() 