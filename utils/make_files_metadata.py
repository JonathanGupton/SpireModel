# import os
# from pathlib import Path
# import time
#
# from dotenv import load_dotenv
# import orjson
# import pandas as pd
#
#
# load_dotenv(dotenv_path=r'..\.env')
#
# log_path = Path(os.getenv('LOGPATH'))
#
# COLUMNS = ("filename", "character_chosen", "victory")
#
# i = 0
# log_metadata = []
# for filepath in log_path.iterdir():
#     if i % 10_000 == 0:
#         print(i, time.ctime(), sep="\t")
#     with open(filepath, "rb") as f:
#         logs = orjson.loads(f.read())
#         for log in logs:
#             log = log['event']
#             filename = str(filepath.name)
#             play_id = log['play_id']
#             character_chosen = log['character_chosen']
#             victory = log['victory']
#             log_metadata.append((filename, play_id, character_chosen, victory))
#     i += 1
# df = pd.DataFrame(log_metadata, columns=COLUMNS)
# df.to_csv("log_metadata.csv")

import os
import time
from pathlib import Path
from dotenv import load_dotenv
import orjson
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables from .env file
load_dotenv(dotenv_path=r'..\.env')
log_path = Path(os.getenv('LOGPATH'))

COLUMNS = ("filename", "play_id", "character_chosen", "victory")

def process_file(filepath):
    """Process a file and return a list of metadata tuples."""
    metadata = []
    with open(filepath, "rb") as f:
        logs = orjson.loads(f.read())
        for log in logs:
            event = log['event']
            filename = str(filepath.name)
            play_id = event['play_id']
            character_chosen = event['character_chosen']
            victory = event['victory']
            metadata.append((filename, play_id, character_chosen, victory))
    return metadata

def main():
    all_metadata = []
    files = list(log_path.iterdir())
    processed = 0

    # Adjust MAX_WORKERS as needed
    MAX_WORKERS = 64
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_file, filepath): filepath for filepath in files}
        for future in as_completed(futures):
            processed += 1
            if processed % 10000 == 0:
                print(processed, time.ctime(), sep="\t")
            all_metadata.extend(future.result())

    df = pd.DataFrame(all_metadata, columns=COLUMNS)
    df.to_csv("log_metadata.csv", index=False)

if __name__ == "__main__":
    main()