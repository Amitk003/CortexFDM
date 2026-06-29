# CortexFDM

CortexFDM is an autonomous closed-loop system that monitors and fixes FDM 3D printing failures in real time. It uses the Gemma 4 31B model on Cerebras API for fast multimodal AI inference.

The system takes a photo of a 3D print, sends it to the AI for visual defect detection, and automatically sends G-code commands to fix the issue. No physical printer is needed for testing. The project uses:
- A mock printer over TCP (simulates firmware)
- Sample images as camera feed
- Gemma 4 31B on Cerebras API for AI
- Rich terminal UI for live monitoring

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Add sample images to `sample_images/`
3. Create `.env` with `CEREBRAS_API_KEY=your_key_here`
4. Start mock printer: `python -m mock_printer.firmware`
5. Start controller: `python -m controller.main`

Use the virtual environment if available:
```
.\venv\Scripts\Activate.ps1
python -m mock_printer.firmware
python -m controller.main
```

## Project Structure

```
CortexFDM/
  controller/
    main.py             - Main closed loop
    camera.py           - Mock camera (reads images, resizes to 384x384)
    cerebras_client.py  - Cerebras API integration
    serial_bridge.py    - TCP client to mock printer
    gcode_translator.py - Defect diagnosis to G-code commands
    safety.py           - Temperature and speed clamping
    ui.py               - Rich terminal dashboard
  mock_printer/
    firmware.py         - TCP server on port 9999 simulating printer
  config/
    settings.py         - All configuration constants
    system_prompt.txt   - AI system prompt
    tool_schema.json    - AI function schema
  sample_images/        - Place 3D print images here
```

## How It Works

The closed loop runs every 3 seconds:

1. Camera captures an image and resizes it to 384x384 (center cropped to preserve aspect ratio)
2. Printer telemetry is queried (temperature, position)
3. Image + telemetry is sent to Gemma 4 31B on Cerebras
4. AI describes the print quality in natural language
5. Defect type is extracted from the description using keyword matching
6. G-code commands are generated based on the defect
7. Commands are sent to the printer via TCP
8. Dashboard updates with results

## Defects Detected

| Image Shows | AI Detects | Action Taken |
|---|---|---|
| Normal printing | nominal | No action |
| Tangled plastic in air (spaghetti) | spaghetti | Emergency stop, disable motors |
| Gaps in layers | under_extrusion | Increase nozzle temp by 5-10C |
| Layers shifted sideways | layer_shift | Reduce print speed to 70% |

## What We Tried and What Failed

### Image Resize Approaches

- **Squish resize**: First approach. Images stretched to fit 384x384. Distorted features, AI got confused.
- **Letterbox padding**: Second try. Added black bars to preserve aspect ratio. Up to 43% of pixels were black bars, wasting the image budget. AI could barely see the defects.
- **Center crop (final)**: Current approach. Crops to a square from the center, then resizes. Every pixel is actual image content. Works best.

### AI Response Formats

- **Tool calling**: First approach. Used Cerebras function calling with strict schema. API required `additionalProperties: false` and other schema constraints. Model gave systematically inverted answers (perfect -> spaghetti, spaghetti -> nominal).
- **JSON response format**: Second try. Used `response_format: json_object` to get clean JSON. Some APIs drop image processing when structured output is enabled. Answers were still wrong.
- **Natural language + keyword extraction (final)**: Current approach. Model describes the print in free text. We extract defect type by matching keywords like "spaghetti", "layer shift", or "gaps". This works because the model describes images accurately when not forced into a category.

### Results

The description + keyword matching approach gives nearly accurate results. The model sees and describes defects correctly. The system works well for severe defects like spaghetti disasters and major layer shifts. Minor imperfections are treated as normal (beginner-friendly).

## Future Improvements

If we had more time, we would fine-tune the model on a dataset of 3D print images with labeled defects. Gemma 4 31B is a general model. A fine-tuned version would be more accurate at distinguishing subtle defects from normal print artifacts. We could also add more defect types and corrective actions.

## Built For

This project was built for the Cerebras x Gemma API hackathon. It demonstrates how fast multimodal AI inference can be used for real-time industrial monitoring and closed-loop control.

## Notes

- The system uses TCP sockets (localhost:9999) instead of a virtual serial port. Com0com was tried first but had driver issues on Windows.
- Sample images should be photos of actual 3D prints. Bright lighting and centered framing help the AI.
- The run.log file in controller/ saves all AI responses for debugging.
