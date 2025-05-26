"""
Validation Module (MVP Version)
Handles post-update system validation and rollback decisions.
"""

import os
import json
import time
import socket
import shutil
import hashlib
import subprocess
import structlog
from typing import Dict, Any, List, Tuple, Optional, Set, Callable
from pathlib import Path

logger = structlog.get_logger()

class UpdateValidator:
    """Validates system integrity after an update."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the validator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.product_type = config.get('product', {}).get('type', 'robot-ai-standard')
        self.critical_services = config.get('validation', {}).get('critical_services', [])
        self.critical_files = config.get('validation', {}).get('critical_files', [])
        self.config_files = config.get('validation', {}).get('config_files', [])
        self.version_file = config.get('product', {}).get('version_file', '/etc/robot-ai/version')
        self.validation_timeout = config.get('validation', {}).get('timeout', 300)  # 5 minutes
        
        # Load product-specific validation rules
        self._load_product_validation_rules()
    
    def _load_product_validation_rules(self):
        """Load validation rules specific to the current product type."""
        try:
            # Try to load product-specific validation from config
            product_validation = self.config.get('validation', {}).get('products', {}).get(self.product_type, {})
            
            # Add product-specific services
            product_services = product_validation.get('critical_services', [])
            if product_services:
                self.critical_services.extend(product_services)
            
            # Add product-specific critical files
            product_files = product_validation.get('critical_files', [])
            if product_files:
                self.critical_files.extend(product_files)
            
            # Add product-specific config files
            product_configs = product_validation.get('config_files', [])
            if product_configs:
                self.config_files.extend(product_configs)
            
            logger.info("Loaded product validation rules", 
                      product=self.product_type,
                      services=len(self.critical_services),
                      files=len(self.critical_files),
                      configs=len(self.config_files))
                      
        except Exception as e:
            logger.error("Error loading product validation rules", error=str(e))
    
    def _run_command(self, cmd: List[str]) -> Tuple[bool, str, str]:
        """Run a command and capture output.
        
        Args:
            cmd: Command to run as a list of arguments
            
        Returns:
            Tuple of (success, stdout, stderr)
        """
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )
            return process.returncode == 0, process.stdout, process.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists.
        
        Args:
            file_path: Path to file
            
        Returns:
            bool: True if file exists, False otherwise
        """
        return os.path.exists(file_path)
    
    def _check_file_permissions(self, file_path: str, expected_permission: Optional[str] = None) -> bool:
        """Check if a file has the expected permissions.
        
        Args:
            file_path: Path to file
            expected_permission: Expected permission string (e.g., '644')
            
        Returns:
            bool: True if permissions match or no expected permission, False otherwise
        """
        if not os.path.exists(file_path):
            return False
            
        if not expected_permission:
            return True
            
        # Get octal permission
        try:
            stat_info = os.stat(file_path)
            octal_permission = oct(stat_info.st_mode)[-3:]
            return octal_permission == expected_permission
        except Exception as e:
            logger.error("Error checking file permissions", 
                       file=file_path, 
                       error=str(e))
            return False
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA256 hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            str: SHA256 hash as hexadecimal string, or None on error
        """
        try:
            if not os.path.exists(file_path):
                return None
                
            hash_sha256 = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error("Error calculating file hash", 
                       file=file_path, 
                       error=str(e))
            return None
    
    def _check_systemd_service(self, service_name: str) -> bool:
        """Check if a systemd service is active and running.
        
        Args:
            service_name: Name of the service
            
        Returns:
            bool: True if service is active, False otherwise
        """
        success, stdout, stderr = self._run_command(
            ['systemctl', 'is-active', '--quiet', service_name]
        )
        return success
    
    def _check_process_running(self, process_name: str) -> bool:
        """Check if a process is running.
        
        Args:
            process_name: Name of the process
            
        Returns:
            bool: True if process is running, False otherwise
        """
        success, stdout, stderr = self._run_command(
            ['pgrep', '-f', process_name]
        )
        return success
    
    def _check_socket_connection(self, host: str, port: int, timeout: int = 5) -> bool:
        """Check if a socket connection can be established.
        
        Args:
            host: Host to connect to
            port: Port to connect to
            timeout: Connection timeout in seconds
            
        Returns:
            bool: True if connection succeeds, False otherwise
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception as e:
            logger.error("Error checking socket connection", 
                       host=host, 
                       port=port, 
                       error=str(e))
            return False
    
    def _validate_json_file(self, file_path: str) -> bool:
        """Validate that a file contains valid JSON.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            bool: True if file contains valid JSON, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'r') as f:
                json.load(f)
            return True
        except Exception as e:
            logger.error("Invalid JSON file", 
                       file=file_path, 
                       error=str(e))
            return False
    
    def _validate_yaml_file(self, file_path: str) -> bool:
        """Validate that a file contains valid YAML.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            bool: True if file contains valid YAML, False otherwise
        """
        try:
            import yaml
            
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True
        except ImportError:
            logger.warning("YAML validation not available (PyYAML not installed)")
            return True  # Assume valid if we can't check
        except Exception as e:
            logger.error("Invalid YAML file", 
                       file=file_path, 
                       error=str(e))
            return False
    
    def validate_system_files(self) -> Dict[str, Any]:
        """Validate critical system files and permissions.
        
        Returns:
            Dict with validation results
        """
        logger.info("Validating system files")
        results = {
            'success': True,
            'missing_files': [],
            'permission_errors': [],
            'details': {}
        }
        
        # Check each critical file
        for file_info in self.critical_files:
            # Handle both string and dict formats
            if isinstance(file_info, str):
                file_path = file_info
                expected_permission = None
            else:
                file_path = file_info.get('path', '')
                expected_permission = file_info.get('permission')
            
            # Skip empty paths
            if not file_path:
                continue
                
            file_result = {
                'exists': self._check_file_exists(file_path),
                'correct_permissions': False
            }
            
            # Check permissions if file exists
            if file_result['exists']:
                file_result['correct_permissions'] = self._check_file_permissions(
                    file_path, expected_permission
                )
            else:
                results['missing_files'].append(file_path)
                results['success'] = False
            
            # Record permission errors
            if file_result['exists'] and not file_result['correct_permissions']:
                results['permission_errors'].append(file_path)
                results['success'] = False
            
            # Store detailed result
            results['details'][file_path] = file_result
        
        if results['success']:
            logger.info("System file validation successful")
        else:
            logger.error("System file validation failed", 
                       missing_files=results['missing_files'],
                       permission_errors=results['permission_errors'])
            
        return results
    
    def validate_services(self) -> Dict[str, Any]:
        """Validate critical services are running.
        
        Returns:
            Dict with validation results
        """
        logger.info("Validating system services")
        results = {
            'success': True,
            'failed_services': [],
            'details': {}
        }
        
        # Check each critical service
        for service_info in self.critical_services:
            # Handle both string and dict formats
            if isinstance(service_info, str):
                service_name = service_info
                service_type = 'systemd'
            else:
                service_name = service_info.get('name', '')
                service_type = service_info.get('type', 'systemd')
            
            # Skip empty names
            if not service_name:
                continue
                
            # Initialize service result
            service_result = {
                'name': service_name,
                'type': service_type,
                'running': False
            }
            
            # Check service based on type
            if service_type == 'systemd':
                service_result['running'] = self._check_systemd_service(service_name)
            elif service_type == 'process':
                service_result['running'] = self._check_process_running(service_name)
            elif service_type == 'socket':
                # Parse host:port format
                if ':' in service_name:
                    host, port_str = service_name.split(':', 1)
                    try:
                        port = int(port_str)
                        service_result['running'] = self._check_socket_connection(host, port)
                    except ValueError:
                        service_result['running'] = False
                else:
                    service_result['running'] = False
            
            # Record failed services
            if not service_result['running']:
                results['failed_services'].append(service_name)
                results['success'] = False
            
            # Store detailed result
            results['details'][service_name] = service_result
        
        if results['success']:
            logger.info("Service validation successful")
        else:
            logger.error("Service validation failed", 
                       failed_services=results['failed_services'])
            
        return results
    
    def validate_version(self, expected_version: Optional[str] = None) -> Dict[str, Any]:
        """Validate system version matches expected version.
        
        Args:
            expected_version: Expected version (if None, skip comparison)
            
        Returns:
            Dict with validation results
        """
        logger.info("Validating system version")
        results = {
            'success': True,
            'version_file_exists': False,
            'current_version': None,
            'expected_version': expected_version,
            'version_match': False
        }
        
        # Check if version file exists
        if not os.path.exists(self.version_file):
            logger.error("Version file not found", file=self.version_file)
            results['success'] = False
            return results
            
        results['version_file_exists'] = True
        
        # Read current version
        try:
            with open(self.version_file, 'r') as f:
                current_version = f.read().strip()
                results['current_version'] = current_version
                
            # Compare versions if expected version provided
            if expected_version:
                results['version_match'] = (current_version == expected_version)
                results['success'] = results['version_match']
                
                if not results['version_match']:
                    logger.error("Version mismatch", 
                               current=current_version, 
                               expected=expected_version)
        except Exception as e:
            logger.error("Error reading version file", 
                       file=self.version_file, 
                       error=str(e))
            results['success'] = False
        
        if results['success']:
            logger.info("Version validation successful", version=results['current_version'])
            
        return results
    
    def validate_configs(self) -> Dict[str, Any]:
        """Validate configuration files.
        
        Returns:
            Dict with validation results
        """
        logger.info("Validating configuration files")
        results = {
            'success': True,
            'missing_configs': [],
            'invalid_configs': [],
            'details': {}
        }
        
        # Check each config file
        for config_info in self.config_files:
            # Handle both string and dict formats
            if isinstance(config_info, str):
                config_path = config_info
                config_type = config_path.split('.')[-1].lower()  # Infer type from extension
            else:
                config_path = config_info.get('path', '')
                config_type = config_info.get('type', 'unknown')
            
            # Skip empty paths
            if not config_path:
                continue
                
            # Initialize config result
            config_result = {
                'exists': self._check_file_exists(config_path),
                'valid': False,
                'type': config_type
            }
            
            # Check if config exists
            if not config_result['exists']:
                results['missing_configs'].append(config_path)
                results['success'] = False
                results['details'][config_path] = config_result
                continue
            
            # Validate config based on type
            if config_type == 'json':
                config_result['valid'] = self._validate_json_file(config_path)
            elif config_type in ['yaml', 'yml']:
                config_result['valid'] = self._validate_yaml_file(config_path)
            else:
                # For unknown types, just check existence
                config_result['valid'] = True
            
            # Record invalid configs
            if not config_result['valid']:
                results['invalid_configs'].append(config_path)
                results['success'] = False
            
            # Store detailed result
            results['details'][config_path] = config_result
        
        if results['success']:
            logger.info("Configuration validation successful")
        else:
            logger.error("Configuration validation failed", 
                       missing=results['missing_configs'],
                       invalid=results['invalid_configs'])
            
        return results
    
    def validate_system(self, expected_version: Optional[str] = None) -> Dict[str, Any]:
        """Run all validation checks and determine if system is valid.
        
        Args:
            expected_version: Expected version after update
            
        Returns:
            Dict with validation results and rollback decision
        """
        logger.info("Starting system validation")
        start_time = time.time()
        
        # Run all validation checks
        file_results = self.validate_system_files()
        service_results = self.validate_services()
        version_results = self.validate_version(expected_version)
        config_results = self.validate_configs()
        
        # Determine overall success
        overall_success = (
            file_results['success'] and 
            service_results['success'] and 
            version_results['success'] and 
            config_results['success']
        )
        
        # Calculate validation time
        validation_time = time.time() - start_time
        
        # Build complete results
        results = {
            'timestamp': time.time(),
            'success': overall_success,
            'needs_rollback': not overall_success,
            'validation_time': validation_time,
            'product_type': self.product_type,
            'version': version_results.get('current_version'),
            'expected_version': expected_version,
            'file_validation': file_results,
            'service_validation': service_results,
            'version_validation': version_results,
            'config_validation': config_results
        }
        
        if overall_success:
            logger.info("System validation successful", 
                      validation_time=f"{validation_time:.2f}s")
        else:
            logger.error("System validation failed, rollback recommended", 
                       validation_time=f"{validation_time:.2f}s")
            
            # Log specific failures for easier troubleshooting
            if not file_results['success']:
                logger.error("File validation failures", 
                           missing=file_results['missing_files'],
                           permissions=file_results['permission_errors'])
                           
            if not service_results['success']:
                logger.error("Service validation failures", 
                           failed=service_results['failed_services'])
                           
            if not version_results['success']:
                logger.error("Version validation failure", 
                           current=version_results.get('current_version'),
                           expected=expected_version)
                           
            if not config_results['success']:
                logger.error("Config validation failures", 
                           missing=config_results['missing_configs'],
                           invalid=config_results['invalid_configs'])
        
        return results
    
    def validate_update(self, expected_version: Optional[str] = None) -> bool:
        """Validate the system after an update.
        
        This method checks critical services, files, and configurations
        to determine if the update was successful.
        
        Args:
            expected_version: Expected version after update
            
        Returns:
            bool: True if validation passes, False otherwise
        """
        logger.info("Validating system after update", expected_version=expected_version)
        
        # Run comprehensive system validation
        validation_results = self.validate_system(expected_version)
        
        # Check if validation passed
        validation_passed = validation_results.get('success', False)
        
        if validation_passed:
            logger.info("System validation passed")
        else:
            logger.error("System validation failed", failures=validation_results.get('failures', []))
        
        return validation_passed 