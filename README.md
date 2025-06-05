 # OTA (Over-The-Air) Update System
Version: 1.2.3
Last Updated: 2024

## Overview
The OTA Update System is a robust, secure, and flexible solution for managing over-the-air updates for embedded systems and IoT devices. It provides a comprehensive framework for update detection, download, verification, and installation, with support for rollback mechanisms and real-time monitoring.

## Key Features
- Secure update package creation and verification
- Real-time update status monitoring via WebSocket
- Automatic update scheduling and execution
- Robust rollback mechanisms
- System resource monitoring
- GUI tools for update management
- Comprehensive logging and error handling
- Support for both manual and automatic updates

## System Requirements
- Python 3.8 or higher
- Ubuntu Linux (tested on Ubuntu 22.04 LTS)
- Systemd for service management
- D-Bus for system service communication
- Network connectivity for update server communication

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/esir-nus/ota.git
   cd ota
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Project Structure
```
ota/
├── config/           # Configuration files
├── docs/            # Documentation
├── src/             # Source code
├── tools/           # Utility tools and GUI applications
│   └── gui/        # GUI tools for update management
├── venv/            # Virtual environment
└── tests/           # Test files
```

## Core Components
1. Update Detection System
   - Monitors for available updates
   - Version comparison and compatibility checking
   - Update scheduling

2. Update Execution Engine
   - Secure package download
   - Integrity verification
   - Installation process management
   - Rollback support

3. Monitoring and Management
   - Real-time status updates via WebSocket
   - System resource monitoring
   - Comprehensive logging
   - GUI management tools

## Usage
### Basic Update Process
1. Create update package using the GUI tool:
   ```bash
   python tools/gui/update_generator.py
   ```

2. Monitor and manage updates using the daemon manager:
   ```bash
   python tools/gui/daemon_manager.py
   ```

### Configuration
- Main configuration: `config/config.yml`
- Product-specific settings: `config/product_config.yml`
- Update manifest: `config/manifest.json`

## Testing
Run the test suite:
```bash
pytest
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Support
For issues and feature requests, please use the GitHub issue tracker.

## Changelog
See CHANGELOG.md for detailed version history and changes.

## Acknowledgments
- ESIR-NUS team for development and testing
- Contributors and maintainers
- Open source community

---
For more information, visit: https://github.com/esir-nus/ota.git