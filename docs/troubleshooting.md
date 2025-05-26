# OTA System Troubleshooting Guide

This document provides solutions for common issues encountered during deployment and operation of the OTA system.

## Common Issues and Solutions

### Dependency Issues

#### Missing PyYAML
```
Error: ModuleNotFoundError: No module named 'yaml'
```

**Solution:** Install PyYAML in the virtual environment
```bash
source ~/venv/bin/activate
pip install pyyaml
```

#### Missing structlog
```
Error: ModuleNotFoundError: No module named 'structlog'
```

**Solution:** Install structlog in the virtual environment
```bash
source ~/venv/bin/activate
pip install structlog
```

### Service Issues

#### Service Won't Start
```
Error: Failed to start ota.service: Unit ota.service not found.
```

**Solution:** Copy service file to the correct location
```bash
sudo cp ota.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start ota
```

#### Method Name Errors
```
Error: 'UpdateDetector' object has no attribute 'check_for_update'
```

**Solution:** Restart the OTA service to pick up code changes
```bash
sudo systemctl restart ota
```

This issue often occurs when code changes have been made but the running service is still using cached Python modules from the previous version.

### API Issues

#### API Endpoints Return Errors
```
Error: No pending update found
```

**Solution:** Ensure a valid manifest exists in the cache directory
```bash
sudo mkdir -p /var/lib/ota/cache
# Create a test manifest with higher version number than current version
```

#### API Key Authentication Failures
```
Error: 401 Unauthorized
```

**Solution:** Check API key configuration in config.yml and ensure you're passing the correct key
```bash
# Include the API key in requests
curl -H "X-API-Key: your-api-key" http://localhost:5000/api/v1/status
```

### Update Issues

#### Update Not Detected
```
Error: Update available: False
```

**Solution:** Verify manifest version is higher than current version and manifest is in correct location
```bash
# Check current version
cat /path/to/version/file

# Check manifest version in
cat /var/lib/ota/cache/latest_manifest.json
```

#### Update Download Fails
```
Error: Failed to download update package
```

**Solution:** Check network connectivity and ensure download URL is correct
```bash
# Test connectivity to update server
ping update-server.example.com

# Verify download URL in manifest
cat /var/lib/ota/cache/latest_manifest.json
```

## Logging and Debugging

### Viewing Logs
```bash
# View OTA service logs
sudo journalctl -u ota

# View recent logs
sudo journalctl -u ota -n 50

# Follow logs in real-time
sudo journalctl -u ota -f
```

### Debug Mode
To enable debug logging, edit the config.yml file and set the log level to DEBUG:
```yaml
logging:
  level: DEBUG
  file: /var/log/ota/daemon.log
```

Then restart the service:
```bash
sudo systemctl restart ota
```

## Systemd Service Management

### Basic Commands
```bash
# Start OTA service
sudo systemctl start ota

# Stop OTA service
sudo systemctl stop ota

# Restart OTA service
sudo systemctl restart ota

# Check status
sudo systemctl status ota

# Enable service to start on boot
sudo systemctl enable ota

# Disable service from starting on boot
sudo systemctl disable ota
```

## Configuration

### Main Configuration File
The main configuration file is located at `/etc/ota/config.yml`. Always restart the service after making changes:
```bash
sudo systemctl restart ota
``` 