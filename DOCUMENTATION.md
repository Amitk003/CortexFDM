# CortexFDM Documentation

## What is CortexFDM?

CortexFDM is a system that watches a 3D printer while it prints, spots problems in real time, and fixes them automatically. Imagine a smart assistant that looks at your print, sees when something goes wrong, and adjusts the printer settings to save the print.

## How It Works

The system has 4 main parts:

### 1. Mock Printer
This is a pretend 3D printer that runs as a Python script. It listens for G-code commands over a TCP connection on your local machine. G-code is the language used to control 3D printers (like "set temperature to 200" or "move to position X10 Y20"). The mock printer keeps track of its temperature, position, and speed, and replies to every command just like a real printer would.

### 2. Mock Camera
Instead of a real camera, the system reads sample images from a folder. These images show different 3D printing states: a perfect print, under-extrusion (gaps in the layers), or spaghetti (total failure where the print has detached from the bed). The images are resized and compressed to be sent to the AI efficiently.

### 3. AI Engine
The images are sent to the Gemma 4 31B model running on Cerebras fast inference. The model looks at the image and decides what is happening:
- Nominal (everything is fine)
- Under-extrusion (not enough plastic coming out)
- Layer shift (layers are misaligned)
- Spaghetti (total failure)

It then calls a tool that returns structured instructions in JSON format.

### 4. Controller
The controller is the brain. It:
1. Reads an image from the folder
2. Converts it to base64 format
3. Sends it to the AI along with current printer telemetry
4. Gets back the diagnosis in JSON
5. Translates the JSON into G-code commands
6. Sends the G-code to the mock printer over the TCP connection

This loop runs every 3 seconds.

## Supported Failure Modes

| Failure Mode | What It Looks Like | What The System Does |
|---|---|---|
| Spaghetti | Tangled plastic loops printing in the air | Emergency stop - turn off heaters, lift head, disable motors |
| Layer Shift | Layers suddenly shifted sideways | Reduce print speed to 70% to prevent more skipped steps |
| Under-extrusion | Gaps in walls, weak layers | Increase nozzle temperature by 5-10 degrees |

## Safety

The controller has safety limits built in:
- Maximum allowed temperature: 250 degrees Celsius
- Minimum allowed speed: 10%
- All commands are validated before sending
