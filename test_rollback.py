#!/usr/bin/env python3
"""
Test script for the automatic rollback functionality.
"""
import os
import json
import time
from src.update.execution import UpdateExecutor
from src.update.backup.backup import BackupManager
from src.validation.validator import UpdateValidator

def main():
    """Test the automatic rollback functionality."""
    print("Testing Automatic Rollback")
    print("========================")
    
    # Create a simple config
    config = {
        'storage': {
            'download_dir': '/var/lib/ota/downloads',
            'backup_dir': '/var/lib/ota/backups'
        },
        'product': {
            'type': 'robot-ai-standard'
        },
        'validation': {
            'enabled': True,
            'timeout': 10,
            'critical_services': [
                {'name': 'nonexistent-service', 'type': 'systemd'}  # This will fail validation
            ]
        }
    }
    
    # Create necessary directories
    backup_dir = config['storage']['backup_dir']
    os.makedirs(backup_dir, exist_ok=True)
    
    # Create a test backup
    backup_manager = BackupManager(backup_dir, config)
    
    # Create a backup file that would be used for rollback
    backup_path = os.path.join(backup_dir, 'pre_update_backup.tar.gz')
    with open(backup_path, 'w') as f:
        f.write("Test backup file content")
    print(f"Created test backup at: {backup_path}")
    
    # Create a failed update scenario
    print("\nSimulating a failed update...")
    
    # Create an update info object
    update_info = {
        'version': '1.1.0',
        'product_type': 'robot-ai-standard',
        'update_path': '/var/lib/ota/downloads/robot-ai-standard-1.1.0.tar.gz',
        'backup_path': backup_path
    }
    
    # Create a validator that will fail validation
    validator = UpdateValidator(config)
    
    # Simulate the update process with validation failure
    print("1. Update installation completed")
    print("2. Running validation...")
    
    try:
        # This should fail because we specified a nonexistent service
        validation_result = validator.validate_update()
        print(f"   Validation result: {'SUCCESS' if validation_result else 'FAILED'}")
        
        if not validation_result:
            print("3. Validation failed, triggering rollback...")
            print("4. Restoring from backup...")
            
            # Restore from backup
            restore_result = backup_manager.restore_backup(backup_path)
            print(f"   Restore result: {'SUCCESS' if restore_result else 'FAILED'}")
            
            print("5. Automatic rollback completed")
    except Exception as e:
        print(f"Error during rollback test: {e}")
        
    print("\nAutomatic rollback test completed")

if __name__ == "__main__":
    main() 