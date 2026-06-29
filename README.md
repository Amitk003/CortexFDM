# CortexFDM

CortexFDM is an autonomous closed-loop AI system that monitors and fixes FDM 3D printing failures in real time.

It uses a multimodal AI model (Gemma 4 31B) to visually inspect a 3D print, detect defects like under-extrusion or total failure, and automatically send corrective G-code commands to the printer.

This is a PC-only setup. No physical printer hardware is needed. The system uses:
- A mock printer script that simulates a real 3D printer firmware over TCP
- Sample images as a mock camera feed
- The Cerebras API for fast AI inference

## Project Structure

```
CortexFDM/
  controller/         - Main controller script and modules
  mock_printer/       - Mock printer firmware simulator
  sample_images/      - Place your sample 3D print images here
  config/             - Settings, prompts, and tool schemas
  docs/               - Documentation files
```

## Quick Start

1. Install Python dependencies: `pip install -r requirements.txt`
2. Place sample images in `sample_images/`
3. Set your API key in `.env`
4. Run mock printer: `python -m mock_printer.firmware`
5. Run controller: `python -m controller.main`

See `docs/setup.md` for detailed setup instructions.

lol, didn't saw the time region and started working on the project at 10:00 AM "IST"