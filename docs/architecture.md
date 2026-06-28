# Architecture Overview

## High-Level Design

The system has 3 main parts that talk to each other:

```
[Controller]  <--- Virtual Serial Port --->  [Mock Printer]
     |
     | (sends images to AI)
     v
[Cerebras API (Gemma 4 31B)]
```

## Components

### Controller
The controller is the main program. It does these things in a loop:
1. Reads an image from the sample_images folder
2. Resizes and compresses the image
3. Encodes it as base64 text
4. Sends the image to the Cerebras API
5. Gets back a diagnosis (what defect was found)
6. Translates the diagnosis into G-code commands
7. Sends the G-code to the mock printer over the virtual serial port
8. Waits 3 seconds, then repeats

### Mock Printer
A script that pretends to be a 3D printer. It:
- Listens on a virtual serial port
- Parses incoming G-code commands
- Keeps track of temperature, position, and speed
- Replies with "ok" after each command
- Prints state changes to the terminal

### Cerebras API
The AI service. It:
- Receives an image of the print
- Analyzes it using the Gemma 4 31B model
- Returns a structured JSON response with the defect type and action needed

## Communication Flow

1. Controller reads image -> encodes to base64
2. Controller sends image + telemetry to Cerebras API
3. Cerebras returns JSON tool call with diagnosis
4. Controller parses JSON -> generates G-code
5. Controller sends G-code over virtual serial port
6. Mock printer receives G-code -> updates internal state
7. Mock printer replies "ok"
8. Repeat from step 1

## Safety

The controller has safety checks that run before any G-code is sent:
- Temperature is clamped to max 250 degrees
- Speed is clamped to min 10%
- Only allowed G-code commands can be sent
