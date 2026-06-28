# CortexFDM - Development Log

## 2026-06-28 - Phase 0: Project Initialization

### Git Setup
- Initialized git repo in project directory
- Added remote origin: https://github.com/Amitk003/CortexFDM.git
- Command: git remote add origin https://github.com/Amitk003/CortexFDM.git

### Python Environment
- Python version: 3.11.9
- pip version: 24.0
- Created virtual environment: python -m venv venv
- Installed dependencies from requirements.txt via pip install
- Packages installed: pyserial 3.5, opencv-python 4.13, cerebras-cloud-sdk 1.67, rich 15.0, python-dotenv 1.2.2
  (plus transitive deps: numpy, httpx, pydantic, anyio, etc.)

### TCP Socket instead of Virtual Serial Port
- Originally planned to use com0com for virtual serial ports
- com0com had driver issues ("Error" status) on this system
- Switched to TCP sockets (localhost:9999) - no driver needed, works cross-platform
- Removed pyserial from requirements.txt

### Project Structure Created
- Created directories: controller/, mock_printer/, sample_images/, config/, config/prompts/, docs/
- Removed old markdown files (not part of this project)

### Files Created
- .gitignore - excludes __pycache__, .env, sample images, etc.
- .env.example - template for API key config
- requirements.txt - Python package dependencies
- README.md - project overview in simple English
- DOCUMENTATION.md - full project documentation
- LOG.md (this file) - development log
- IMAGE_REQUIREMENTS.md - specs for sample images needed
- config/settings.py - all configuration constants
- config/system_prompt.txt - AI system prompt
- config/tool_schema.json - execute_remediation tool definition
- config/prompts/ (empty, for future use)
- controller/__init__.py
- mock_printer/__init__.py
- mock_printer/firmware.py - TCP-based mock 3D printer (Phase 1a)
- docs/architecture.md - system architecture overview
- docs/setup.md - step-by-step setup guide
- docs/usage.md - how to run the system

### Phase 3b: Closed-Loop Main Controller (feat/closed-loop branch)
- Written controller/main.py
  - Full closed-loop orchestration: Camera -> Cerebras -> Translator -> Printer
  - Initializes all components with proper error handling
  - Loop: capture image, query telemetry, AI diagnosis, translate to G-code, send to printer
  - Graceful shutdown on Ctrl+C
  - All error cases handled with clear console messages
- Verified: camera loads images, connects to mock printer, Cerebras client init reports missing key correctly
- Ready to test with real API once .env is configured

### Phase 2a: Mock Camera (feat/mock-camera branch)
- Written controller/camera.py
  - MockCamera class with automatic image scanning
  - get_next_frame() - reads, resizes (384x384), encodes to JPEG, returns base64 data URI
  - raw=True returns dict with filename, base64, data_uri, dimensions, size_bytes
  - Automatic cycling through sorted images (loops back after last)
  - Supports .jpg, .jpeg, .png files
- Updated config/settings.py: IMAGE_WIDTH/HEIGHT changed from 512 to 384 (token optimized)
- Generated 4 test images in sample_images/ (placeholder graphics)
- Tested: 6 reads from 4-image pool correctly cycles back to start
### Phase 1a: Mock Printer (feat/mock-printer branch)
- Written mock_printer/firmware.py - TCP socket server on 127.0.0.1:9999
- Supports: M104, M140, M220, M84, G91, G90, G28, G1, M105, M114
- Maintains state: extruder_temp, bed_temp, position, speed_factor, relative_mode
- Tested successfully with all commands
  - M105 -> "ok T:200/200 B:60/60"
  - M104 S215 -> "ok" (temp updated to 215)
  - M220 S75 -> "ok" (speed set to 75%)
  - G91 / G1 Z10 -> position updated to Z:10.0
  - G28 X Y -> position reset to X:0.0 Y:0.0 Z:0.0
  - M114 -> "ok X:0.0 Y:0.0 Z:0.0"

### Refactoring: Codebase review and fixes
- README.md: Removed outdated com0com reference
- DOCUMENTATION.md: Replaced "virtual serial port" with "TCP connection"
- docs/architecture.md: Fixed mixed virtual serial port references
- mock_printer/firmware.py: Major refactoring
- mock_printer/firmware.py: Major refactoring (on feat/mock-printer branch)
  - Converted global mutable dict to PrinterState class with attributes
  - Separated GCodeParser into its own class
  - Created MockPrinter class with start/stop/run lifecycle
  - Added proper error handling for type conversions
  - Used settings.py values instead of hardcoded temps
  - Better graceful shutdown on disconnect
  - All 9 test commands still pass after refactor

### Phase 1b: Serial Bridge (feat/serial-bridge branch)
- Written controller/serial_bridge.py - TCP client for mock printer
  - SerialBridge class with connect/disconnect/context manager
  - send_gcode() / send_multiple() - sends commands, reads responses
  - query_temperature() - parses M105 response
  - query_position() - parses M114 response
  - Buffer-based response reader handles partial TCP reads
- Tested successfully: all commands and parsing work correctly
