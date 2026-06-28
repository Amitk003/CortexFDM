# Setup Guide

## Prerequisites

- Windows 10 or 11
- Python 3.11 or higher
- Internet connection (for Cerebras API)

## Step 1: Install com0com

com0com creates virtual serial port pairs on Windows. One half of the pair will be used by the mock printer, the other by the controller.

1. Go to https://com0com.sourceforge.net/
2. Download the latest signed setup executable
3. Run the installer
4. After installation, open Device Manager and expand "Ports (COM & LPT)"
5. You should see CNCA0 and CNCB0 ports listed

If you do not see the ports, open Command Prompt as Administrator and run:
```
"C:\Program Files (x86)\com0com\setupc.exe" install
"C:\Program Files (x86)\com0com\setupc.exe" create 0 PortName=CNCA0 PortName=CNCB0
```

## Step 2: Set Up Python Environment

Open a terminal in the project folder:
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3: Add Sample Images

Place the sample images in the `sample_images/` folder. See `IMAGE_REQUIREMENTS.md` for what images are needed.

## Step 4: Set Your API Key

Create a file called `.env` in the project root with:
```
CEREBRAS_API_KEY=your_api_key_here
```

## Step 5: Run the System

Open two terminals.

Terminal 1 - Start the mock printer:
```
.\venv\Scripts\activate
python -m mock_printer.firmware
```

Terminal 2 - Start the controller:
```
.\venv\Scripts\activate
python -m controller.main
```

## Troubleshooting

- "Port not found": Make sure com0com is installed and ports are visible in Device Manager
- "Module not found": Run `pip install -r requirements.txt`
- "API error": Check your API key in .env file
