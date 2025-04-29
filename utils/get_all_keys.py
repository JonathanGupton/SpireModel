from collections import Counter

# defaultdict is no longer strictly needed for the core counting,
# but kept in case is_modded_log or other parts might use it implicitly,
# or for potential future re-integration. Can be removed if certain it's unused.
from collections import defaultdict
import os
from pathlib import Path
import pickle
import time
import logging
from multiprocessing import Pool, cpu_count

import orjson

# Assuming SpireModel.filter.is_modded_log exists and works as before
try:
    from SpireModel.filter import is_modded_log
except ImportError:
    logging.warning("Could not import is_modded_log. Assuming no logs are modded.")

    # Define a dummy function if the import fails
    def is_modded_log(data):
        return False  # Default to false if the function can't be imported


from dotenv import load_dotenv

# Ensure .env is in the script's directory or specify the correct relative path
# If the script is in 'scripts/' and .env is in the parent, '..' is correct.
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

# --- Configuration ---
log_path_str = os.getenv("LOGPATH")
if log_path_str is None:
    logging.error("LOGPATH environment variable not set.")
    exit(1)
log_path = Path(log_path_str)
# Changed filename to reflect the new purpose
OUTPUT_PICKLE_FILE = (
    Path(__file__).resolve().parent.parent / "all_keys_dump_multiprocessing.pkl"
)
MAX_WORKERS = cpu_count()

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(processName)s - %(message)s",
)


# --- Worker Function (Processes a single file - MODIFIED FOR KEY COUNTING) ---
def process_log_file(filepath: Path):
    """
    Reads, parses, and counts all keys within the 'event' dictionary
    of each valid, non-modded log entry in a single JSON file.

    Returns a dictionary containing the key counts for this file and metadata,
    or None if processing fails.
    """
    # Data structures local to this process/file
    key_counts = Counter()  # Counts all keys found in 'event' dicts
    processed_logs = 0  # Non-modded logs processed in this file
    modded_logs = 0  # Modded logs skipped in this file
    file_errors = 0  # Errors encountered within log entries in this file

    try:
        with open(filepath, "rb") as f:
            content = f.read()
            # Handle empty files
            if not content:
                # Return empty data, file was 'processed' but contained nothing
                return {
                    "keys": key_counts,
                    "processed_logs_count": processed_logs,
                    "modded_logs_skipped": modded_logs,
                    "errors": file_errors,
                }
            logs = orjson.loads(content)

        if not isinstance(logs, list):
            logging.warning(f"Expected a list of logs, got {type(logs)} in {filepath}")
            # Indicate an error at the file level, but don't return None yet
            # We might count this as a 'failed file' later if needed,
            # but returning the current (empty) state is also valid.
            file_errors += 1  # Increment error count for this file
            return {
                "keys": key_counts,
                "processed_logs_count": processed_logs,
                "modded_logs_skipped": modded_logs,
                "errors": file_errors,  # Return the error count
            }

        for log in logs:
            # Basic check for expected structure
            if not isinstance(log, dict) or "event" not in log:
                file_errors += 1
                continue

            data = log["event"]
            if not isinstance(data, dict):
                file_errors += 1
                continue

            # Validate mod status (optional, keep if you want to exclude modded keys)
            if is_modded_log(data):
                modded_logs += 1
                continue

            processed_logs += 1  # Count non-modded logs processed from this file

            # --- Key Counting ---
            # Iterate through all keys in the 'event' dictionary
            for key in data.keys():
                # Ensure key is a string (keys in JSON are usually strings)
                # Counter handles hashable types automatically
                if isinstance(key, str):
                    key_counts[key] += 1
                else:
                    # Handle non-string keys if necessary, e.g., convert to string
                    # or skip them, depending on requirements.
                    # For simplicity, we'll count their string representation here.
                    try:
                        key_counts[str(key)] += 1
                    except Exception:
                        # If even converting to string fails, count it as an error maybe?
                        # logging.warning(f"Could not process non-string key {key} in {filepath}")
                        file_errors += 1

        # --- End Key Counting ---

        # Return the collected counts and metadata for this file
        return {
            "keys": key_counts,
            "processed_logs_count": processed_logs,
            "modded_logs_skipped": modded_logs,
            "errors": file_errors,
        }

    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None  # Signal failure for this file
    except orjson.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON in file: {filepath} - {e}")
        # Treat JSON errors as file failures
        # Return None, or return a dict indicating the error type if preferred
        return None  # Signal failure for this file
    except Exception as e:
        logging.exception(f"Unexpected error processing file {filepath}: {e}")
        return None  # Signal failure for this file


# --- Aggregation Function (MODIFIED for key counting) ---
def aggregate_results(all_results):
    """Combines key counts and metadata from all worker processes."""
    logging.info("Starting aggregation of results...")
    # Initialize final aggregated data structures
    final_key_counts = Counter()
    total_processed_logs = 0
    total_modded_logs_skipped = 0
    total_errors_in_files = 0
    files_processed_successfully = 0

    for file_result in all_results:
        if file_result is None:  # Skip results from failed files
            continue

        files_processed_successfully += 1

        # Aggregate metadata
        total_processed_logs += file_result.get("processed_logs_count", 0)
        total_modded_logs_skipped += file_result.get("modded_logs_skipped", 0)
        total_errors_in_files += file_result.get("errors", 0)

        # Aggregate key counts
        # Use .get with a default empty Counter for safety
        worker_key_counts = file_result.get("keys", Counter())
        final_key_counts.update(worker_key_counts)  # Efficiently adds counts

    logging.info(f"Aggregation complete.")
    logging.info(
        f"Total non-modded logs processed across all files: {total_processed_logs}"
    )
    logging.info(
        f"Total modded logs skipped across all files: {total_modded_logs_skipped}"
    )
    if total_errors_in_files > 0:
        logging.warning(
            f"Total errors encountered within log entries: {total_errors_in_files}"
        )

    # Return aggregated counts and metadata in a dictionary
    return {
        "all_key_counts": final_key_counts,
        "_total_processed_logs": total_processed_logs,
        "_total_modded_logs_skipped": total_modded_logs_skipped,
        "_total_errors_in_files": total_errors_in_files,
        "_files_processed_successfully": files_processed_successfully,
    }


# --- Main Execution ---
if __name__ == "__main__":
    start_time = time.time()
    logging.info(f"Starting key counting using up to {MAX_WORKERS} processes.")

    if not log_path or not log_path.is_dir():
        logging.error(f"Log path not found or not a directory: {log_path}")
        exit(1)

    # Get list of files to process
    # Using iterdir and filtering is generally fine and often faster for huge directories
    # than glob initially loading everything.
    logging.info(f"Scanning directory: {log_path}")
    try:
        all_entries = list(log_path.iterdir())
    except OSError as e:
        logging.error(f"Error accessing log directory {log_path}: {e}")
        exit(1)

    logging.info(f"Found {len(all_entries)} entries. Filtering for files...")

    # Filter out directories and ensure they are files
    # Optional: Add filtering for specific extensions like '.json' if needed
    # files_to_process = [f for f in all_entries if f.is_file() and f.suffix.lower() == '.json']
    files_to_process = [f for f in all_entries if f.is_file()]
    num_files = len(files_to_process)
    logging.info(f"Found {num_files} actual files to process.")

    if num_files == 0:
        logging.warning("No files found to process.")
        exit(0)

    results_from_workers = []
    files_processed_count = 0  # Files successfully processed by worker (returned data)
    files_failed_count = 0  # Files failed in worker (returned None or raised exception)
    total_files_handled = 0  # Counter for progress reporting

    # Use multiprocessing Pool
    logging.info(f"Submitting {num_files} file processing tasks to Pool...")
    try:
        with Pool(processes=MAX_WORKERS) as pool:
            # Use imap_unordered for efficiency - processes results as they complete
            results_iterator = pool.imap_unordered(process_log_file, files_to_process)

            # Process results as they arrive
            for result in results_iterator:
                total_files_handled += 1
                if result is not None:
                    results_from_workers.append(result)
                    # We track success based on non-None return now
                    # files_processed_count is calculated during aggregation
                else:
                    # Error should have been logged within the worker process or during file access
                    files_failed_count += 1

                # Log progress periodically
                if total_files_handled % 500 == 0 or total_files_handled == num_files:
                    # Success count here reflects non-None returns
                    current_success_count = len(results_from_workers)
                    logging.info(
                        f"Progress: {total_files_handled}/{num_files} files handled ({current_success_count} succeeded, {files_failed_count} failed)."
                    )

    except Exception as e:
        logging.exception(
            f"An error occurred during multiprocessing pool execution: {e}"
        )
        # Decide if you want to proceed with partial results or exit

    final_success_count = len(results_from_workers)
    logging.info(
        f"Finished processing files. Success: {final_success_count}, Failed: {files_failed_count}"
    )

    # Aggregate results from all successful workers
    if results_from_workers:
        final_aggregated_data = aggregate_results(results_from_workers)

        # Retrieve the actual key counts for display/saving
        final_key_counts = final_aggregated_data.get("all_key_counts", Counter())
        logging.info(f"Found {len(final_key_counts)} unique keys across all logs.")
        # Optionally print the most common keys:
        # top_n = 10
        # logging.info(f"Top {top_n} most common keys: {final_key_counts.most_common(top_n)}")

        # Save the final aggregated dictionary (including counts and metadata)
        logging.info(f"Saving aggregated data to {OUTPUT_PICKLE_FILE}...")
        try:
            with open(OUTPUT_PICKLE_FILE, "wb") as f:
                # Dump the entire dictionary returned by aggregate_results
                pickle.dump(final_aggregated_data, f)
            logging.info(f"Data saved successfully to {OUTPUT_PICKLE_FILE}.")
        except Exception as e:
            logging.exception(f"Failed to save pickle file: {e}")
    else:
        logging.warning(
            "No results were successfully processed. Skipping aggregation and saving."
        )

    end_time = time.time()
    logging.info(f"Total processing time: {end_time - start_time:.2f} seconds")
