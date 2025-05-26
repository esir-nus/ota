#!/usr/bin/env python3
"""
Test script for configuring alternate product types.
"""
import os
import json
import yaml
from src.update.detection import UpdateDetector
from src.update.execution import UpdateExecutor

def main():
    """Test configuring for an alternate product type."""
    print("Testing Alternate Product Type Configuration")
    print("==========================================")
    
    # Create a config for the advanced product type
    config = {
        'product': {
            'type': 'robot-ai-advanced',  # Changed from standard to advanced
            'version_file': '/etc/robot-ai/version'
        },
        'storage': {
            'cache_dir': '/var/lib/ota/cache',
            'download_dir': '/var/lib/ota/downloads',
            'backup_dir': '/var/lib/ota/backups'
        },
        'validation': {
            'critical_services': [
                {'name': 'robot-ai-motion-advanced', 'type': 'systemd'},
                {'name': 'robot-ai-vision-advanced', 'type': 'systemd'},
                {'name': 'robot-ai-voice', 'type': 'systemd'}
            ],
            'critical_files': [
                {'path': '/opt/robot-ai/modules/motion/motion_advanced.py', 'permission': '755'},
                {'path': '/opt/robot-ai/modules/vision/vision_advanced.py', 'permission': '755'},
                {'path': '/opt/robot-ai/modules/voice/voice.py', 'permission': '755'}
            ]
        }
    }
    
    # Save the config to a file
    config_path = 'test_advanced_config.yml'
    with open(config_path, 'w') as f:
        yaml.dump(config, f)
    print(f"Created test config file at: {config_path}")
    
    # Create a test manifest for the advanced product
    advanced_manifest = {
        "product_type": "robot-ai-advanced",
        "version": "2.0.0",
        "release_date": "2025-05-22T18:00:00Z",
        "release_notes": "Test update for advanced product",
        "update_url": "https://example.com/updates/robot-ai-advanced-2.0.0.tar.gz",
        "checksum": "abc123checksum",
        "signature": "abc123signature",
        "dependencies": [],
        "compatibility": {
            "min_version": "1.0.0",
            "max_version": "1.9.9"
        },
        "created_by": "OTA Test System"
    }
    
    # Save the advanced manifest
    advanced_manifest_path = 'test_advanced_manifest.json'
    with open(advanced_manifest_path, 'w') as f:
        json.dump(advanced_manifest, f, indent=2)
    print(f"Created test advanced manifest at: {advanced_manifest_path}")
    
    # Save a copy to the cache directory for the product type
    cache_dir = config['storage']['cache_dir']
    os.makedirs(cache_dir, exist_ok=True)
    cache_manifest_path = os.path.join(cache_dir, 'latest_manifest_advanced.json')
    with open(cache_manifest_path, 'w') as f:
        json.dump(advanced_manifest, f, indent=2)
    print(f"Created cached advanced manifest at: {cache_manifest_path}")
    
    # Instantiate detector with the new config
    detector = UpdateDetector(config)
    
    # Check if the product type is correctly configured
    print(f"\nConfigured product type: {config['product']['type']}")
    
    # Create the necessary directories for this product type
    download_dir = os.path.join(config['storage']['download_dir'], config['product']['type'])
    os.makedirs(download_dir, exist_ok=True)
    print(f"Created product-specific download directory: {download_dir}")
    
    backup_dir = os.path.join(config['storage']['backup_dir'], config['product']['type'])
    os.makedirs(backup_dir, exist_ok=True)
    print(f"Created product-specific backup directory: {backup_dir}")
    
    # Create a test update package
    update_package_path = os.path.join(download_dir, f"{advanced_manifest['product_type']}-{advanced_manifest['version']}.tar.gz")
    with open(update_package_path, 'w') as f:
        f.write("Test advanced product update package content")
    print(f"Created test update package at: {update_package_path}")
    
    print("\nAlternate product type configuration completed successfully")

if __name__ == "__main__":
    main() 