"""Run this once to initialise the database and folder structure."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.models import init_db
from database.crud import register_camera

if __name__ == "__main__":
    init_db()
    register_camera(
        "gate1", "Main Entrance",
        "Gate 1 - Main Entrance Camera",
        "data/videos/gate1/"
    )
    register_camera(
        "gate2", "Side Entrance",
        "Gate 2 - Side Entrance Camera",
        "data/videos/gate2/"
    )
    register_camera(
        "gate3", "Exit Gate",
        "Gate 3 - Exit Camera",
        "data/videos/gate3/"
    )
    print("Database initialised successfully.")
    print("Cameras gate1, gate2, gate3 registered.")
    print("")
    print("Next steps:")
    print("  1. Place video files in data/videos/gate1/, gate2/, gate3/")
    print("  2. Configure .env file with your API keys")
    print("  3. Run: streamlit run ui/app.py")
