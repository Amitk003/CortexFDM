# Usage Guide

## Running the System

You need two terminal windows open at the same time.

### Terminal 1: Mock Printer

This terminal runs the pretend 3D printer firmware:
```
python -m mock_printer.firmware
```

You will see output like:
```
[MOCK PRINTER] Connected on CNCB0
[MOCK PRINTER] Ready to receive G-code commands
[MOCK PRINTER] Received: M104 S215
[MOCK PRINTER] Set extruder temp to 215
[MOCK PRINTER] Received: M220 S75
[MOCK PRINTER] Set speed factor to 75%
```

### Terminal 2: Controller

This terminal runs the main controller:
```
python -m controller.main
```

You will see output like:
```
[CONTROLLER] Reading image: spaghetti_01.jpg
[CONTROLLER] Encoding image to base64...
[CONTROLLER] Sending to Cerebras API...
[CONTROLLER] Diagnosis: spaghetti (emergency_stop)
[CONTROLLER] Translating to G-code...
[CONTROLLER] Sending: M104 S0
[CONTROLLER] Sending: M140 S0
[CONTROLLER] Sending: G91
[CONTROLLER] Sending: G1 Z10
[CONTROLLER] Sending: G28 X Y
[CONTROLLER] Sending: M84
[CONTROLLER] Mock printer acknowledged all commands
[CONTROLLER] Waiting 3 seconds before next check...
```

## Output Format

The controller uses the Rich library to show a clean terminal layout with:
- Current image being analyzed (as text description)
- Latest diagnosis from the AI
- Last G-code commands sent
- Printer telemetry (temperature, position, speed)
- Timing information

## Demo Mode

For recording a demo video:
1. Open two terminal windows side by side
2. Terminal 1 (left): shows mock printer reacting to commands
3. Terminal 2 (right): shows controller sending payloads and receiving fast AI responses
4. The fast inference speed from Cerebras will be visible in the response times

## Changing Images

To test different failure modes:
- Replace the images in sample_images/ folder
- The controller reads images in sequence (sorted by name)
- It loops back to the first image after the last one
