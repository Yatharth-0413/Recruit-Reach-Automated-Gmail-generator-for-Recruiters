
import os
import subprocess
import sys

os.makedirs("data", exist_ok=True)
os.makedirs("attachments", exist_ok=True)

subprocess.run([
    sys.executable,
    "-m",
    "streamlit",
    "run",
    "app.py"
])
