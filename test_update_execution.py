#!/usr/bin/env python3
"""
Test script for the UpdateExecutor class.
"""
import os
import json
from src.update.execution import UpdateExecutor

def main():
    """Test the UpdateExecutor implementation."""
    print("Testing Update Executor")
    print("=====================")
    
    # Create a simple config
    config = {
        'storage': {
            'download_dir': '/var/lib/ota/downloads',
            'backup_dir': '/var/lib/ota/backups'
        },
        'product': {
            'type': 'robot-ai-standard'
        }
    }
    
    # Create necessary directories
    download_dir = config['storage']['download_dir']
    os.makedirs(download_dir, exist_ok=True)
    
    # Load test manifest
    try:
        with open('test_manifest.json', 'r') as f:
            update_info = json.load(f)
        
        print(f"Loaded test manifest for version: {update_info.get('version')}")
        
        # Create a dummy update package file
        update_package_path = os.path.join(download_dir, f"{update_info.get('product_type')}-{update_info.get('version')}.tar.gz")
        with open(update_package_path, 'w') as f:
            f.write("Test update package content")
        print(f"Created test update package at: {update_package_path}")
        
        # Instantiate the update executor
        executor = UpdateExecutor(config)
        
        # Test executing an update
        print("\nExecuting update...")
        success = executor.execute_update(update_info)
        
        if success:
            print("Update executed successfully")
            print("New version would be:", update_info.get('version'))
        else:
            print("Update execution failed")
        
    except Exception as e:
        print(f"Error during update execution test: {e}")

if __name__ == "__main__":
    main() 