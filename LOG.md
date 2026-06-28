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
- docs/architecture.md - system architecture overview
- docs/setup.md - step-by-step setup guide
- docs/usage.md - how to run the system
