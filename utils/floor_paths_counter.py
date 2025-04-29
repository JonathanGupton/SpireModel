from collections import Counter
import os
from pathlib import Path
import pickle
import time
import logging
from multiprocessing import Pool, cpu_count

import orjson

from SpireModel.filter import is_modded_log

# --- Configuration ---
# Assuming your .env file is in the parent directory relative to the script
# If the script is in 'scripts/' and .env is in '.', use '../.env'
# If the script and .env are in the same directory, use '.env'
# dotenv_path = Path(__file__).resolve().parent.parent / '.env' # More robust way to find parent dir
dotenv_path = r'..\.env' # Keep original path if it works for your setup

# --- Load Environment Variables (Optional but good practice) ---
# You might not strictly need dotenv if LOGPATH is set system-wide,
# but it's good for project-specific settings.
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=dotenv_path)
    log_path_str = os.getenv('LOGPATH')
except ImportError:
    print("dotenv library not found. Trying to get LOGPATH directly from environment.")
    log_path_str = os.getenv('LOGPATH')

if log_path_str is None:
    logging.error("LOGPATH environment variable not set or .env file not found/loaded correctly.")
    exit(1)

log_path = Path(log_path_str)
OUTPUT_PICKLE_FILE = Path('../floor_paths.pkl') # Use Path object, place in parent dir
MAX_WORKERS = cpu_count()

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(processName)s - %(message)s')

# --- Worker Function (Simplified for path counting) ---
def process_log_file_for_paths(filepath: Path):
    """
    Reads a log file, extracts 'path_per_floor', converts to tuple, and counts occurrences.
    Returns a Counter object for paths found in this file, or None on error.
    """
    path_counter = Counter()
    processed_logs_in_file = 0
    errors_in_file = 0

    try:
        with open(filepath, "rb") as f:
            content = f.read()
            if not content:
                # logging.warning(f"File is empty: {filepath}") # Optional: can be noisy
                return path_counter # Return empty counter for empty file

            logs = orjson.loads(content)

        if not isinstance(logs, list):
            logging.warning(f"Expected a list of logs, got {type(logs)} in {filepath}")
            return None # Indicate error

        for log in logs:
            if not isinstance(log, dict) or 'event' not in log:
                # logging.warning(f"Skipping malformed log entry in {filepath}") # Optional: noisy
                errors_in_file += 1
                continue

            data = log['event']
            if not isinstance(data, dict):
                # logging.warning(f"Skipping malformed 'event' data in {filepath}") # Optional: noisy
                errors_in_file += 1
                continue

            # Skip modded logs if desired (using a simplified check or reusing is_modded_log)
            # For this specific task, you might decide *not* to filter modded logs
            # if you want path counts from *all* logs.
            if is_modded_log(data): # Uncomment if you need filtering
                continue           # Uncomment if you need filtering

            processed_logs_in_file += 1

            # --- Path Extraction ---
            try:
                path_per_floor = data.get('path_per_floor')
                if isinstance(path_per_floor, list):
                    # Convert list to tuple to make it hashable (usable as Counter key)
                    path_tuple = tuple(path_per_floor)
                    path_counter[path_tuple] += 1
                # else: # Optional: Log if path_per_floor is missing or not a list
                    # if path_per_floor is not None:
                    #     logging.debug(f"path_per_floor is not a list in {filepath}: {type(path_per_floor)}")
            except Exception as e:
                logging.warning(f"Error processing path_per_floor in {filepath} for log: {e}")
                errors_in_file += 1
        # --- End Path Extraction ---

        # Optional: Log file-level stats if needed
        # logging.debug(f"File {filepath}: Processed {processed_logs_in_file} logs, found {len(path_counter)} unique paths, {errors_in_file} errors.")

        return path_counter

    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None # Signal failure
    except orjson.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON in file: {filepath} - {e}")
        return None # Signal failure
    except Exception as e:
        logging.exception(f"Unexpected error processing file {filepath}: {e}")
        return None # Signal failure


# --- Aggregation Function (Simplified) ---
def aggregate_path_counters(list_of_counters):
    """Combines multiple Counter objects into one."""
    logging.info("Starting aggregation of path counters...")
    final_path_counter = Counter()
    for counter in list_of_counters:
        if counter is not None: # Ensure we only process valid counters from workers
            final_path_counter.update(counter)
    logging.info(f"Aggregation complete. Found {len(final_path_counter)} unique paths in total.")
    return final_path_counter


# --- Main Execution ---
if __name__ == '__main__':
    start_time = time.time()
    logging.info(f"Starting path_per_floor counting using up to {MAX_WORKERS} processes.")

    # Ensure output directory exists (parent directory of the pickle file)
    output_dir = OUTPUT_PICKLE_FILE.parent
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Ensured output directory exists: {output_dir}")
    except Exception as e:
        logging.error(f"Could not create output directory {output_dir}: {e}")
        exit(1)


    if not log_path or not log_path.is_dir():
        logging.error(f"Log path not found or not a directory: {log_path}")
        exit(1)

    files_to_process = [f for f in log_path.iterdir() if f.is_file()]
    num_files = len(files_to_process)
    logging.info(f"Found {num_files} files to process in {log_path}.")

    if num_files == 0:
        logging.warning("No files found to process.")
        exit(0)

    results_from_workers = []
    files_processed_count = 0
    files_failed_count = 0
    total_files_handled = 0

    logging.info(f"Submitting {num_files} file processing tasks to Pool...")
    try:
        with Pool(processes=MAX_WORKERS) as pool:
            # Use the simplified worker function
            results_iterator = pool.imap_unordered(process_log_file_for_paths, files_to_process)

            for result_counter in results_iterator:
                total_files_handled += 1
                if result_counter is not None:
                    results_from_workers.append(result_counter)
                    files_processed_count += 1
                else:
                    files_failed_count += 1

                if total_files_handled % 500 == 0 or total_files_handled == num_files:
                    logging.info(
                        f"Progress: {total_files_handled}/{num_files} files handled "
                        f"({files_processed_count} succeeded, {files_failed_count} failed).")

    except Exception as e:
        logging.exception(f"An error occurred during multiprocessing pool execution: {e}")

    logging.info(f"Finished processing files. Success: {files_processed_count}, Failed: {files_failed_count}")

    if results_from_workers:
        # Aggregate the counters
        final_paths = aggregate_path_counters(results_from_workers)

        # Save the final path counter to a pickle file
        logging.info(f"Saving final path counts to {OUTPUT_PICKLE_FILE}...")
        try:
            with open(OUTPUT_PICKLE_FILE, 'wb') as f:
                pickle.dump(final_paths, f)
            logging.info("Path counts saved successfully.")
            # Optional: Print some results
            logging.info(f"Top 5 most common paths:")
            for path, count in final_paths.most_common(5):
                 logging.info(f"  Path: {path}, Count: {count}")

        except Exception as e:
            logging.exception(f"Failed to save pickle file: {e}")
    else:
        logging.warning("No results were successfully processed. Skipping aggregation and saving.")

    end_time = time.time()
    logging.info(f"Total processing time: {end_time - start_time:.2f} seconds")