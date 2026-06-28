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

### Phase 2b: Cerebras Client (feat/cerebras-client branch)
- Written controller/cerebras_client.py
  - CerebrasClient class loads API key from .env or constructor param
  - Loads system prompt from config/system_prompt.txt
  - Loads tool schema from config/tool_schema.json
  - diagnose(image_base64, telemetry) - sends multimodal payload to Cerebras API
  - Constructs proper OpenAI-compatible messages array with text + image_url
  - Returns structured dict with defect_type, action_required, optional params
  - Error handling for missing API key, file not found, API failures
- Tested module structure: system prompt (799 chars), tool schema, telemetry formatting all working

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
