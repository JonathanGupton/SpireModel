"""Script used to track down modded files by the presence of 'theJungle' in the file text"""
import os
from pathlib import Path
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv(dotenv_path=r'..\.env')
log_path = Path(os.getenv('LOGPATH'))


for fp in log_path.iterdir():
    with open(fp, "r") as f:
        data = f.read()
        if "theJungle" in data:
            print(fp)