#!/usr/bin/env python3
"""
Test script for the BackupManager class.
"""
import os
import datetime
from src.update.backup.backup import BackupManager

def main():
    """Test the BackupManager implementation."""
    print("Testing Backup Manager")
    print("=====================")
    
    # Create a simple config
    config = {
        'storage': {
            'backup_dir': '/var/lib/ota/backups',
            'max_backups': 2
        },
        'product': {
            'type': 'robot-ai-standard'
        }
    }
    
    # Create the backup directory if it doesn't exist
    backup_dir = config['storage']['backup_dir']
    os.makedirs(backup_dir, exist_ok=True)
    
    # Instantiate the backup manager
    backup_manager = BackupManager(backup_dir, config)
    
    # Test creating a backup
    print("\nCreating backup...")
    success = backup_manager.create_backup()
    
    if success:
        print("Backup created successfully")
    else:
        print("Backup creation failed")
    
    # Check if any files were created in the backup directory
    print("\nChecking backup directory...")
    if os.path.exists(backup_dir):
        files = os.listdir(backup_dir)
        if files:
            print(f"Files in backup directory: {files}")
        else:
            print("No files found in backup directory")
    else:
        print(f"Backup directory does not exist: {backup_dir}")
    
    # Create a test backup file to test restore functionality
    test_backup_path = os.path.join(backup_dir, f"test_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz")
    try:
        with open(test_backup_path, 'w') as f:
            f.write("Test backup file content")
        print(f"\nCreated test backup file: {test_backup_path}")
        
        # Test restoring from the test backup
        print("\nTesting restore functionality...")
        restore_success = backup_manager.restore_backup(test_backup_path)
        
        if restore_success:
            print("Restore completed successfully")
        else:
            print("Restore failed")
    except Exception as e:
        print(f"Error creating test backup file: {e}")

if __name__ == "__main__":
    main() 