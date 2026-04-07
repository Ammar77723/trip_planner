"""Start the Streamlit frontend"""
import subprocess
import sys
import os

if __name__ == "__main__":
    print("=" * 50)
    print("Starting Airspace Copilot Frontend")
    print("=" * 50)
    print("Frontend will open in your browser")
    print("=" * 50)
    
    # Get the path to streamlit
    streamlit_path = os.path.join(os.path.dirname(sys.executable), "Scripts", "streamlit.exe")
    if not os.path.exists(streamlit_path):
        streamlit_path = "streamlit"
    
    # Run streamlit
    subprocess.run([streamlit_path, "run", "frontend/app.py"])

