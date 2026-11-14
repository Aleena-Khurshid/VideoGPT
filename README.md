# VideoGPT: Intelligent Video Surveillance Analysis

VideoGPT turns CCTV footage into searchable records. It detects vehicles, reads license plates, identifies vehicle colors, and lets you ask questions in plain English such as *"show red cars in gate1"*. It can also follow a vehicle across several cameras and send Gmail alerts for flagged events.

Built as a Final Year Project in BS Computer Systems Engineering at MUST, Mirpur, by Aleena Khurshid and Huma Nazr.

## Features

- **Vehicle detection** with YOLOv8 (`core/detector.py`)
- **License plate recognition** with EasyOCR (`core/alpr.py`)
- **Vehicle color detection** using k-means clustering in HSV color space (`core/color_extractor.py`)
- **Natural language search** that uses a Groq LLM to turn a question into a database query (`nlp/query_parser.py`)
- **Multi-camera investigation**: track a plate across gates, with a timeline, relation graph, and plate comparison (`investigation/`)
- **Email alerts** for flagged events through Gmail SMTP (`alerts/notifier.py`)
- **Streamlit dashboard** for camera setup, processing, search, investigation, analytics, and event logs (`ui/app.py`)

## How it works

```
CCTV video ─► frame sampling ─► YOLOv8 vehicle detection ─► EasyOCR plate reading
                                                    │
                                   color detection ─┘
                                                    ▼
                                     SQLAlchemy database (cameras, detections)
                                                    ▲
 "show red cars in gate1" ─► Groq LLM ─► structured query ─┘
                                                    │
                                     Streamlit UI, timelines, alerts
```

## Tech stack

| Tool | Purpose |
|---|---|
| YOLOv8 (Ultralytics) | Detects vehicles in each sampled frame |
| OpenCV | Reads video and crops frames |
| EasyOCR | Reads license plate text |
| Groq API (Llama 3) | Converts natural language questions into filters |
| SQLAlchemy + SQLite | Stores cameras and detection records |
| Streamlit | Web interface |
| NetworkX, Plotly | Relation graphs and charts |
| Gmail SMTP | Sends alert emails |

## Requirements

- Windows 10 or 11 (64-bit). The setup steps below use PowerShell.
- Python 3.10
- At least 16 GB RAM recommended
- About 10 GB of free disk space for models and data
- A free Groq API key from https://console.groq.com
- A Gmail account with an App Password (only needed for alerts)

## Setup

1. **Create and activate a virtual environment**

   ```powershell
   python -m venv vgpt_env
   vgpt_env\Scripts\activate
   ```

2. **Install PyTorch (CPU build) first**

   ```powershell
   pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu
   ```

3. **Install the other requirements**

   ```powershell
   pip install -r requirements.txt --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Configure secrets.** Copy the template and fill in your own values. Never commit `.env`.

   ```powershell
   copy .env.example .env
   ```

   | Variable | What to put |
   |---|---|
   | `GROQ_API_KEY` | Your Groq API key |
   | `GMAIL_SENDER` | The Gmail address that sends alerts |
   | `GMAIL_APP_PASSWORD` | A 16-character Gmail App Password (not your normal password) |
   | `GMAIL_RECIPIENT` | Where alerts are sent |

5. **Create the database.** This also registers the sample cameras `gate1`, `gate2`, and `gate3`.

   ```powershell
   python setup_db.py
   ```

6. **Add footage.** Place MP4 or AVI files at `data\videos\gate1\footage.mp4` (and the same for `gate2` and `gate3`). The `data/` folder is git-ignored.

## Running the app

```powershell
streamlit run ui/app.py
```

Open http://localhost:8501. If the port is busy, use `streamlit run ui/app.py --server.port 8502`.

On the first detection run, YOLOv8 downloads `yolov8n.pt` (about 6 MB). EasyOCR also downloads its models (about 200 MB) on first use, so the first run is slow.

## Usage

1. **Camera Manager:** register each gate camera and its video file path.
2. **Process Videos:** select cameras and start processing. This runs vehicle detection and plate reading.
3. **Natural Language Search:** ask questions such as *"show red cars in gate1"*.
4. **Multi-Camera Investigation:** enter a plate, for example *"investigate ABC-1234 in gate1 gate2 gate3"*, to see its timeline, relation graph, and plate comparison, and to send a Gmail alert.

## Project structure

```
VideoGPT/
├── core/           Vision pipeline: detector, plate reader, color, frame processor
├── database/       SQLAlchemy models and database operations
├── nlp/            Groq-based query parser
├── investigation/  Multi-camera timeline and plate tracking
├── alerts/         Gmail alert sender
├── ui/             Streamlit app
├── setup_db.py     Creates the database and sample cameras
├── requirements.txt
└── .env.example    Template for environment variables
```

## Limitations

- **No quantitative evaluation yet.** I have not measured detection, OCR, or search accuracy. The results depend on footage quality, lighting, and camera angle.
- **Tests are not written yet.** Adding tests for the query parser, plate normalization, and database operations is the next step.
- **Windows-focused setup.** The commands are written for PowerShell. The code itself is not tied to Windows.
- **Depends on a hosted LLM.** Natural language search needs a Groq API key and internet access. The model name is set in `nlp/query_parser.py` and may need updating when Groq changes its models.
- **Heavy first run.** YOLO and EasyOCR model downloads make the first start slow.

## Planned improvements

- Measure detection and plate-reading accuracy on labeled clips, and report the results here.
- Add unit tests and a CI workflow.
- Add screenshots or a short demo video of the dashboard.

## Author

**Aleena Khurshid**: BS Computer Systems Engineering, MUST Mirpur. [GitHub](https://github.com/Aleena-Khurshid) · [LinkedIn](https://linkedin.com/in/aleena-khurshid-ai)

Co-developer: **Huma Nazr**.
