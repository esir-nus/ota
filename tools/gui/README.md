# OTA GUI Testing Tools

This directory contains GUI applications for testing and managing the OTA system.

## Prerequisites

- Python 3.x with Tkinter support
- X11 display (GUI environment)
- Virtual environment with required packages

## Tools

### 1. Update Generator (`update_generator.py`)

A GUI tool for creating test update packages and manifests.

**Features:**
- Create ZIP update packages from selected files
- Generate manifest files with proper metadata
- Upload manifests directly to the test server
- Support for multiple product types
- Version validation and release notes editing

**Usage:**
```bash
cd /home/robot/ota/ota
source venv/bin/activate
python tools/gui/update_generator.py
```

**Tabs:**
- **Create Package**: Select files and create ZIP packages
- **Generate Manifest**: Create and upload manifest files

### 2. Daemon Manager (`daemon_manager.py`)

A GUI tool for monitoring and controlling the OTA daemon.

**Features:**
- Real-time status monitoring
- Manual update checking and installation
- System log viewing
- WebSocket event monitoring
- Update history display
- Configuration management

**Usage:**
```bash
cd /home/robot/ota/ota
source venv/bin/activate
python tools/gui/daemon_manager.py
```

**Tabs:**
- **Status**: Real-time daemon status and system information
- **Updates**: Manual update control and progress monitoring
- **Logs**: System log viewer with refresh capability
- **Settings**: API configuration and WebSocket events

## Testing Workflow

### Using Update Generator

1. **Create a Test Package:**
   - Open Update Generator
   - Go to "Create Package" tab
   - Select product type and version
   - Add files to include in the update
   - Click "Create Update Package"

2. **Generate Test Manifest:**
   - Go to "Generate Manifest" tab
   - Fill in version, download URL, and release notes
   - Click "Generate Manifest"
   - Click "Upload to Test Server" to make it available to the daemon

### Using Daemon Manager

1. **Monitor Status:**
   - Open Daemon Manager
   - Check "Status" tab for connection and daemon status
   - Verify WebSocket connectivity

2. **Test Updates:**
   - Go to "Updates" tab
   - Click "Check for Updates" to detect new manifests
   - Click "Install Update" to apply available updates
   - Monitor progress and view history

3. **View Logs:**
   - Go to "Logs" tab
   - Click "Refresh Logs" to view recent daemon activity
   - Monitor WebSocket events in "Settings" tab

## Configuration

### API Settings

The Daemon Manager uses these default settings:
- API URL: `http://localhost:5000/api/v1`
- API Key: `admin-key-example`

You can modify these in the Settings tab of the Daemon Manager.

### File Permissions

Some operations require sudo privileges:
- Uploading manifests to `/var/lib/ota/cache`
- Viewing system logs with `journalctl`

## Troubleshooting

### Display Issues
```bash
# If you get display errors
export DISPLAY=:0
```

### Permission Issues
```bash
# Ensure OTA cache directory is accessible
sudo chown -R $USER:$USER /var/lib/ota/cache
```

### Dependencies
```bash
# Install missing GUI dependencies
pip install python-socketio requests websocket-client
```

## Integration with Test Tasks

These tools support the test tasks outlined in Test_Task.md:

- **Update Generator Core Testing**: Create and validate test packages
- **Daemon Manager Core Testing**: Monitor connectivity and functionality
- **Manifest Generation**: Generate proper manifest files for testing
- **Real-time Monitoring**: WebSocket event tracking

## Screenshots

(Note: Screenshots would be included here in a full documentation)

- Update Generator interface showing package creation
- Daemon Manager status display with real-time updates
- Log viewer showing system activity
- WebSocket events display 