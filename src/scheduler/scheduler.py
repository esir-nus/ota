"""
Scheduler Module (MVP Version)
Manages automated update checking and scheduling.
"""

import os
import json
import time
import random
import datetime
import sqlite3
import threading
import logging
import structlog
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

# Import update detection
from src.update.detection import UpdateDetector
from src.update.execution import UpdateExecutor

logger = structlog.get_logger()

class UpdateScheduler:
    """Manages scheduling of update checks and installations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the update scheduler.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.scheduler = BackgroundScheduler()
        self.db_path = config.get('storage', {}).get('db_path', '/var/lib/ota/scheduler.db')
        self.check_hour = random.randint(3, 4)  # Random hour between 3-4 AM
        self.check_minute = random.randint(0, 59)  # Random minute
        self.detector = UpdateDetector(config)
        self.executor = UpdateExecutor(config)
        self.backoff_factor = 1  # Initial backoff factor
        self.max_backoff = 64  # Maximum backoff factor (approx. 2 months with daily checks)
        
        # Create storage directory if needed
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Configure job listeners
        self.scheduler.add_listener(self._job_listener, 
                                  EVENT_JOB_ERROR | EVENT_JOB_EXECUTED)
    
    def _init_database(self):
        """Initialize the SQLite database for storing scheduler state."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create scheduler state table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scheduler_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create update history table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS update_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    check_type TEXT,
                    update_available BOOLEAN,
                    update_executed BOOLEAN,
                    version TEXT,
                    success BOOLEAN,
                    error_message TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("Scheduler database initialized", path=self.db_path)
        except Exception as e:
            logger.error("Failed to initialize scheduler database", error=str(e))
    
    def _store_state(self, key: str, value: Any):
        """Store a state value in the database.
        
        Args:
            key: State key
            value: State value (will be JSON serialized)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            serialized_value = json.dumps(value)
            
            cursor.execute('''
                INSERT OR REPLACE INTO scheduler_state (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, serialized_value))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to store scheduler state", key=key, error=str(e))
    
    def _get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value from the database.
        
        Args:
            key: State key
            default: Default value if key doesn't exist
            
        Returns:
            The state value, or the default if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM scheduler_state WHERE key = ?', (key,))
            result = cursor.fetchone()
            
            conn.close()
            
            if result:
                return json.loads(result[0])
            return default
        except Exception as e:
            logger.error("Failed to get scheduler state", key=key, error=str(e))
            return default
    
    def _log_update_check(self, check_type: str, available: bool, executed: bool, 
                         version: Optional[str] = None, success: bool = True, 
                         error_message: Optional[str] = None):
        """Log an update check to the history database.
        
        Args:
            check_type: Type of check ('scheduled' or 'manual')
            available: Whether an update was available
            executed: Whether an update was executed
            version: Version number if an update was available
            success: Whether the operation was successful
            error_message: Error message if the operation failed
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO update_history 
                (check_type, update_available, update_executed, version, success, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (check_type, available, executed, version, success, error_message))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error("Failed to log update check", error=str(e))
    
    def _job_listener(self, event):
        """Handle scheduler job events.
        
        Args:
            event: Scheduler event
        """
        if hasattr(event, 'exception') and event.exception:
            logger.error("Scheduled update check failed", 
                       job_id=event.job_id, 
                       error=str(event.exception))
            
            # Increase backoff factor for failed jobs (exponential backoff)
            self.backoff_factor = min(self.backoff_factor * 2, self.max_backoff)
            self._store_state('backoff_factor', self.backoff_factor)
            
            # Reschedule with backoff
            if event.job_id == 'scheduled_check':
                self._schedule_next_check()
        else:
            # On successful execution, reset backoff factor
            if event.job_id == 'scheduled_check':
                self.backoff_factor = 1
                self._store_state('backoff_factor', self.backoff_factor)
                
                # Schedule next check at regular interval
                self._schedule_next_check()
    
    def _schedule_next_check(self):
        """Schedule the next update check with appropriate backoff."""
        # Remove existing job if it exists
        self.scheduler.remove_job('scheduled_check', jobstore='default', ignore_conflicts=True)
        
        # Apply backoff if needed
        if self.backoff_factor > 1:
            # Calculate next check date based on backoff factor
            next_check = datetime.datetime.now() + datetime.timedelta(days=self.backoff_factor)
            logger.info("Scheduling next check with backoff", 
                      backoff_factor=self.backoff_factor,
                      next_check=next_check.strftime('%Y-%m-%d %H:%M:%S'))
            
            # Schedule at the same hour/minute but on a future date
            trigger = CronTrigger(
                year=next_check.year,
                month=next_check.month, 
                day=next_check.day,
                hour=self.check_hour,
                minute=self.check_minute
            )
        else:
            # Regular schedule (every day at the selected hour/minute)
            logger.info("Scheduling regular daily check", 
                      hour=self.check_hour, 
                      minute=self.check_minute)
            
            trigger = CronTrigger(
                hour=self.check_hour,
                minute=self.check_minute
            )
        
        # Add the job with the calculated trigger
        self.scheduler.add_job(
            func=self._run_scheduled_check,
            trigger=trigger,
            id='scheduled_check',
            name='Scheduled Update Check',
            replace_existing=True
        )
        
        next_run = self.scheduler.get_job('scheduled_check').next_run_time
        logger.info("Next update check scheduled", next_run=next_run.strftime('%Y-%m-%d %H:%M:%S'))
    
    def _run_scheduled_check(self):
        """Run a scheduled update check."""
        logger.info("Running scheduled update check")
        try:
            # Check for update
            update_available, update_info = self.detector.check_for_update()
            
            if update_available and update_info:
                version = update_info.get('version', 'unknown')
                logger.info("Update available in scheduled check", version=version)
                self._log_update_check('scheduled', True, False, version)
                
                # In MVP, we automatically download and apply the update
                # Future versions might implement user confirmation
                success = self.executor.execute_update(update_info)
                
                if success:
                    logger.info("Scheduled update applied successfully", version=version)
                    self._log_update_check('scheduled', True, True, version, True)
                else:
                    logger.error("Failed to apply scheduled update", version=version)
                    self._log_update_check('scheduled', True, True, version, False, 
                                        "Failed to apply update")
            else:
                logger.info("No update available in scheduled check")
                self._log_update_check('scheduled', False, False)
                
        except Exception as e:
            logger.error("Error during scheduled update check", error=str(e))
            self._log_update_check('scheduled', False, False, None, False, str(e))
            raise  # Re-raise to trigger backoff
    
    def check_now(self) -> Dict[str, Any]:
        """Check for updates immediately.
        
        Returns:
            Dict with update check results
        """
        logger.info("Running immediate update check")
        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'success': False,
            'update_available': False,
            'version': None,
            'error': None
        }
        
        try:
            # Check for update
            update_available, update_info = self.detector.check_for_update()
            
            result['success'] = True
            result['update_available'] = update_available
            
            if update_available and update_info:
                version = update_info.get('version', 'unknown')
                result['version'] = version
                logger.info("Update available in immediate check", version=version)
                self._log_update_check('manual', True, False, version)
                
                # Store the update info for later installation
                self._store_state('pending_update', update_info)
            else:
                logger.info("No update available in immediate check")
                self._log_update_check('manual', False, False)
                
        except Exception as e:
            error_message = str(e)
            logger.error("Error during immediate update check", error=error_message)
            self._log_update_check('manual', False, False, None, False, error_message)
            
            result['success'] = False
            result['error'] = error_message
        
        return result
    
    def apply_pending_update(self) -> Dict[str, Any]:
        """Apply a pending update that was previously found.
        
        Returns:
            Dict with update application results
        """
        logger.info("Applying pending update")
        result = {
            'timestamp': datetime.datetime.now().isoformat(),
            'success': False,
            'version': None,
            'error': None
        }
        
        try:
            # Get pending update info
            update_info = self._get_state('pending_update')
            
            if not update_info:
                error_message = "No pending update found"
                logger.error(error_message)
                result['error'] = error_message
                return result
            
            version = update_info.get('version', 'unknown')
            result['version'] = version
            
            # Execute the update
            success = self.executor.execute_update(update_info)
            
            if success:
                logger.info("Pending update applied successfully", version=version)
                self._log_update_check('manual', True, True, version, True)
                self._store_state('pending_update', None)  # Clear pending update
                result['success'] = True
            else:
                error_message = "Failed to apply update"
                logger.error(error_message, version=version)
                self._log_update_check('manual', True, True, version, False, error_message)
                result['error'] = error_message
                
        except Exception as e:
            error_message = str(e)
            logger.error("Error applying pending update", error=error_message)
            result['error'] = error_message
        
        return result
    
    def get_update_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get update check history.
        
        Args:
            limit: Maximum number of records to return
            
        Returns:
            List of update history records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM update_history
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            history = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return history
        except Exception as e:
            logger.error("Failed to get update history", error=str(e))
            return []
    
    def start(self):
        """Start the scheduler."""
        try:
            # Load persisted state if it exists
            persisted_backoff = self._get_state('backoff_factor', 1)
            if persisted_backoff:
                self.backoff_factor = persisted_backoff
            
            # Schedule initial check
            self._schedule_next_check()
            
            # Start the scheduler
            self.scheduler.start()
            logger.info("Update scheduler started", 
                      check_hour=self.check_hour, 
                      check_minute=self.check_minute,
                      backoff_factor=self.backoff_factor)
                      
        except Exception as e:
            logger.error("Failed to start scheduler", error=str(e))
    
    def stop(self):
        """Stop the scheduler."""
        try:
            self.scheduler.shutdown()
            logger.info("Update scheduler stopped")
        except Exception as e:
            logger.error("Error shutting down scheduler", error=str(e))
    
    def get_status(self) -> Dict[str, Any]:
        """Get current scheduler status.
        
        Returns:
            Dict with scheduler status information
        """
        status = {
            'active': self.scheduler.running,
            'next_check': None,
            'backoff_factor': self.backoff_factor,
            'pending_update': self._get_state('pending_update')
        }
        
        # Get next scheduled run time
        scheduled_job = self.scheduler.get_job('scheduled_check')
        if scheduled_job and scheduled_job.next_run_time:
            status['next_check'] = scheduled_job.next_run_time.isoformat()
        
        return status 