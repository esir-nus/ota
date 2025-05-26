#!/usr/bin/env python3
"""
Script to create a test manifest file for OTA update testing.
"""

import os
import json
import datetime

def create_test_manifest():
    """Create a test manifest file in the cache directory."""
    # Define the manifest content
    manifest = {
        "product_type": "robot-ai-standard",
        "version": "1.1.0",
        "release_date": datetime.datetime.now().isoformat(),
        "release_notes": "Test update for OTA system testing",
        "update_url": "https://example.com/updates/robot-ai-standard-1.1.0.tar.gz",
        "checksum": "abc123checksum",
        "signature": "abc123signature",
        "dependencies": [],
        "compatibility": {
            "min_version": "1.0.0",
            "max_version": "1.0.0"
        },
        "created_by": "OTA Test System"
    }
    
    # Create the cache directory if it doesn't exist
    cache_dir = "/var/lib/ota/cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Write the manifest file
    manifest_path = os.path.join(cache_dir, "latest_manifest.json")
    try:
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Created test manifest at {manifest_path}")
        
        # For testing, also create a local copy we can access
        local_path = "test_manifest.json"
        with open(local_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"Created local test manifest at {local_path}")
        
        return True
    except Exception as e:
        print(f"Error creating manifest: {e}")
        return False

if __name__ == "__main__":
    create_test_manifest() 