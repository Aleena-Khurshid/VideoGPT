# VideoGPT - Intelligent Video Surveillance Analysis

BSc Computer Systems Engineering Final Year Project
MUST Mirpur | Aleena Khurshid (FA22-CSE-008) | Huma Nazr (FA22-CSE-067)

## System Requirements
- Windows 10/11 (64-bit)
- Python 3.10.x (Download: https://www.python.org/downloads/release/python-31011/)
- VS Code (Download: https://code.visualstudio.com/)
- 16GB RAM recommended
- 10GB free disk space (for models + data)

## Quick Start

### Step 1 - Clone / Extract Project
Extract the project folder. Open VS Code. Open the VideoGPT folder.

### Step 2 - Open VS Code Terminal
Press Ctrl+backtick to open terminal. Make sure it shows PowerShell.

### Step 3 - Create Virtual Environment
```powershell
python -m venv vgpt_env
```

### Step 4 - Activate Virtual Environment
```powershell
vgpt_env\Scripts\activate
```
You should see (vgpt_env) in your prompt.

### Step 5 - Install PyTorch (CPU version first)
```powershell
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu
```

### Step 6 - Install All Other Requirements
```powershell
pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu
```

If any package fails install individually:
```powershell
pip install streamlit ultralytics opencv-python easyocr Pillow numpy pandas scikit-learn SQLAlchemy groq plotly networkx python-dotenv loguru Shapely
```

### Step 7 - Configure Environment Variables
Copy .env.example to .env:
```powershell
copy .env.example .env
```
Open .env in VS Code and fill in:
- GROQ_API_KEY: Get free at https://console.groq.com (sign up, create API key)
- GMAIL_SENDER: Your Gmail address
- GMAIL_APP_PASSWORD: Gmail > Settings > Security > App Passwords > Generate
- GMAIL_RECIPIENT: Where to send alerts

### Step 8 - Initialise Database
```powershell
python setup_db.py
```
Expected output: Database initialised. Cameras gate1/gate2/gate3 registered.

### Step 9 - Add Your Videos
Place CCTV video files (MP4/AVI) in:
- data\videos\gate1\footage.mp4
- data\videos\gate2\footage.mp4
- data\videos\gate3\footage.mp4

### Step 10 - Run VideoGPT
```powershell
streamlit run ui/app.py
```
Browser opens at http://localhost:8501

## How to Use

1. Camera Manager -> Register your gate cameras with video file paths
2. Process Videos -> Select cameras -> Click Start Processing (runs YOLO + ALPR)
3. Search -> Type natural language query: "show red cars in gate1"
4. Investigation -> Type "investigate ABC-1234 in gate1 gate2 gate3"
   - See timeline chart
   - See relation graph
   - See plate comparison
   - Send Gmail alert

## Troubleshooting

Port already in use:
```powershell
streamlit run ui/app.py --server.port 8502
```

EasyOCR slow first run (downloading models ~200MB) - just wait.

YOLO auto-downloads yolov8n.pt (~6MB) on first detection run.

If torch not found:
```powershell
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Project Structure
```
VideoGPT/
├── core/           Vision pipeline (YOLO, ALPR, color)
├── database/       SQLAlchemy models and CRUD
├── nlp/            Groq LLM query parser
├── investigation/  Multi-camera investigation engine
├── alerts/         Gmail notification system
├── ui/             Streamlit web interface
├── data/           Videos, frames, clips (git-ignored)
├── setup_db.py     Database initialiser
├── requirements.txt
├── .env.example
└── README.md
```
