# Setup Guide

## Prerequisites

- Windows 10 or 11
- Python 3.11 or higher
- Internet connection (for Cerebras API)

## Step 1: Set Up Python Environment

Open a terminal in the project folder:
```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Add Sample Images

Place the sample images in the `sample_images/` folder. See `IMAGE_REQUIREMENTS.md` for what images are needed.

## Step 3: Set Your API Key

Create a file called `.env` in the project root with:
```
CEREBRAS_API_KEY=your_api_key_here
```

## Step 4: Run the System

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

- "Module not found": Run `pip install -r requirements.txt`
- "Connection refused": Make sure mock printer is running first
- "API error": Check your API key in .env file
