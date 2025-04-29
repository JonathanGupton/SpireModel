# Main processing script (Modified)

from collections import Counter
from collections import defaultdict
import os
from pathlib import Path
import pickle
import time
import logging
from multiprocessing import Pool, cpu_count
import traceback  # For more detailed exception logging

import orjson

# Import the modified filter function
try:
    # Adjust the import path based on your project structure
    # If filter.py is in SpireModel directory relative to this script's parent:
    from SpireModel.filter import get_modded_reason

    # If filter.py is in the same directory:
    # from filter import get_modded_reason
except ImportError:
    logging.error(
        "Could not import get_modded_reason from SpireModel.filter. Ensure filter.py is accessible."
    )

    # Define a dummy function if import fails, to avoid crashing processing entirely
    def get_modded_reason(data):
        logging.warning("Using dummy get_modded_reason: ALL logs will be processed.")
        return None  # Assume not modded if checker is unavailable


from dotenv import load_dotenv

# --- .env loading and Configuration (Keep as before) ---
dotenv_path_local = Path(".") / ".env"
dotenv_path_parent = Path("..") / ".env"

if dotenv_path_local.exists():
    load_dotenv(dotenv_path=dotenv_path_local)
    print(f"Loaded .env from {dotenv_path_local}")
elif dotenv_path_parent.exists():
    load_dotenv(dotenv_path=dotenv_path_parent)
    print(f"Loaded .env from {dotenv_path_parent}")
else:
    print("Warning: .env file not found in current or parent directory.")

log_path_str = os.getenv("LOGPATH")
if log_path_str is None:
    logging.error("LOGPATH environment variable not set.")
    exit(1)
log_path = Path(log_path_str)
output_dir = Path(".")  # Save in current dir, adjust as needed
output_dir.mkdir(parents=True, exist_ok=True)
OUTPUT_PICKLE_FILE = (
    output_dir / "metadata_dump_multiprocessing_extended.pkl"
)  # New filename
MAX_WORKERS = cpu_count()

# --- Logging Setup (Keep as before) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(processName)s - %(message)s",
)


# --- Worker Function (Processes a single file) ---
def process_log_file(filepath: Path):
    """
    Reads, parses, and extracts summary data from a single log file.
    Counts reasons for skipping modded logs.
    Returns a dictionary containing the summarized data for this file,
    or None if processing fails.
    """
    # Initialize data structures local to this process/file
    file_data = {
        # --- Data Fields (keep all existing and new ones) ---
        "floor_reached": Counter(),
        "master_deck": Counter(),
        "relics": Counter(),
        "damage_taken_by_enemy": defaultdict(Counter),
        "potions_obtained": defaultdict(Counter),
        "floors_visited": set(),
        "path_per_floor_counts": Counter(),  # <-- ADDED: Initialize new counter
        "items_purchased": set(),
        "neow_bonus": Counter(),
        "build_version": set(),
        "purchased_purges": Counter(),
        "events": Counter(),
        "neow_cost": Counter(),
        "is_trial": Counter(),
        "character_chosen": Counter(),
        "is_prod": Counter(),
        "is_daily": Counter(),
        "chose_seed": Counter(),
        "circlet_count": Counter(),
        "win_rate": Counter(),
        "is_beta": Counter(),
        "is_endless": Counter(),
        "special_seed": Counter(),
        # --- Metadata ---
        "processed_logs_count": 0,
        "modded_logs_skipped": 0,
        "modded_reasons": Counter(),
        "errors": 0,
        "filter_errors": 0,
    }
    processed_logs = 0
    modded_logs = 0
    filter_errors = 0

    try:
        with open(filepath, "rb") as f:
            content = f.read()
            if not content:
                return file_data

            logs = orjson.loads(content)

        if not isinstance(logs, list):
            if isinstance(logs, dict) and "event" in logs:
                logs = [logs]
            else:
                logging.warning(
                    f"Expected list/dict of logs, got {type(logs)} in {filepath}"
                )
                file_data["errors"] += 1
                return file_data

        for log in logs:
            if not isinstance(log, dict) or "event" not in log:
                file_data["errors"] += 1
                continue

            data = log["event"]
            if not isinstance(data, dict):
                file_data["errors"] += 1
                continue

            # === MODIFIED MOD CHECK ===
            mod_reason = None
            try:
                mod_reason = get_modded_reason(data)
            except Exception as e:
                logging.warning(
                    f"Error during mod check in {filepath}: {e}", exc_info=False
                )
                filter_errors += 1
                mod_reason = "filter_check_error"

            if mod_reason is not None:
                modded_logs += 1
                file_data["modded_reasons"][mod_reason] += 1
                continue
            # === END MODIFIED MOD CHECK ===

            processed_logs += 1

            # --- Data Extraction (Keep all the try/except blocks as before) ---
            # (Existing extraction logic for floor_reached, master_deck, etc.)
            # ... (all previous try/except blocks for other fields remain unchanged) ...
            try:
                floor = data.get("floor_reached")
                file_data["floor_reached"][floor] += 1 if floor is not None else 0
            except Exception:
                pass
            try:
                master_deck = data.get("master_deck")
                if isinstance(master_deck, list):
                    for card in master_deck:
                        if isinstance(card, str):
                            file_data["master_deck"][card] += 1
            except Exception:
                pass
            try:
                relics = data.get("relics")
                if isinstance(relics, list):
                    for relic in relics:
                        if isinstance(relic, str):
                            file_data["relics"][relic] += 1
            except Exception:
                pass
            try:
                damage_taken = data.get("damage_taken")
                if isinstance(damage_taken, list):
                    for battle in damage_taken:
                        if isinstance(battle, dict):
                            enemy, damage = battle.get("enemies"), battle.get("damage")
                            if isinstance(enemy, str) and damage is not None:
                                try:
                                    file_data["damage_taken_by_enemy"][enemy][
                                        damage
                                    ] += 1
                                except TypeError:
                                    pass
            except Exception:
                pass
            try:
                potions_obtained = data.get("potions_obtained")
                if isinstance(potions_obtained, list):
                    for potion in potions_obtained:
                        if isinstance(potion, dict):
                            key, floor = potion.get("key"), potion.get("floor")
                            if isinstance(key, str) and floor is not None:
                                try:
                                    file_data["potions_obtained"][key][floor] += 1
                                except TypeError:
                                    pass
            except Exception:
                pass

            # --- MODIFIED: Process path_per_floor ---
            try:
                path = data.get("path_per_floor")
                if isinstance(path, list):
                    # Keep original logic for floors_visited set
                    file_data["floors_visited"].update(
                        {
                            f
                            for f in path
                            if isinstance(f, (str, int, float, tuple, type(None)))
                        }
                    )
                    # --- ADDED: Count string occurrences in path_per_floor ---
                    for item in path:
                        if isinstance(item, str):
                            file_data["path_per_floor_counts"][item] += 1
                    # --- END ADDED ---
            except Exception as e:
                # Optional: Log if needed, but pass to avoid crashing on one field
                # logging.warning(f"Error processing path_per_floor in {filepath} for a log: {e}")
                pass
            # --- END MODIFIED ---

            try:
                items = data.get("items_purchased")
                if isinstance(items, list):
                    file_data["items_purchased"].update(
                        {i for i in items if isinstance(i, (str, int, float, tuple))}
                    )
            except Exception:
                pass
            try:
                neow = data.get("neow_bonus")
                if neow is not None and isinstance(neow, (str, int, float, tuple)):
                    file_data["neow_bonus"][neow] += 1
            except Exception:
                pass
            try:
                build = data.get("build_version")
                if build is not None and isinstance(build, (str, int, float, tuple)):
                    file_data["build_version"].add(build)
            except Exception:
                pass
            try:
                purges = data.get("purchased_purges")
                file_data["purchased_purges"][purges] += 1 if purges is not None else 0
            except Exception:
                pass
            try:
                events = data.get("event_choices")
                if isinstance(events, list):
                    for event in events:
                        if isinstance(event, dict):
                            name = event.get("event_name")
                            if isinstance(name, str):
                                file_data["events"][name] += 1
            except Exception:
                pass
            try:
                val = data.get("neow_cost")
                file_data["neow_cost"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("is_trial")
                file_data["is_trial"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("character_chosen")
                if val is not None and isinstance(val, str):
                    file_data["character_chosen"][val] += 1
            except Exception:
                pass
            try:
                val = data.get("is_prod")
                file_data["is_prod"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("is_daily")
                file_data["is_daily"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("chose_seed")
                file_data["chose_seed"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("circlet_count")
                file_data["circlet_count"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("victory")
                file_data["win_rate"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("is_beta")
                file_data["is_beta"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("is_endless")
                file_data["is_endless"][val] += 1 if val is not None else 0
            except Exception:
                pass
            try:
                val = data.get("special_seed")
                file_data["special_seed"][val] += 1 if val is not None else 0
            except Exception:
                pass
            # --- End Data Extraction ---

        # Update final counts for the file
        file_data["processed_logs_count"] = processed_logs
        file_data["modded_logs_skipped"] = modded_logs
        file_data["filter_errors"] = filter_errors
        return file_data

    except FileNotFoundError:
        logging.error(f"File not found: {filepath}")
        return None
    except orjson.JSONDecodeError as e:
        logging.error(f"Failed JSON parse: {filepath} - {e}")
        return None
    except Exception as e:
        logging.exception(f"Unexpected error processing file {filepath}: {e}")
        return None


# --- Aggregation Function ---
def aggregate_results(all_results):
    """Combines results from all worker processes."""
    logging.info("Starting aggregation of results...")
    # Initialize final aggregated data structures
    final_data = {
        # --- Data Fields (keep all existing and new ones) ---
        "floor_reached": Counter(),
        "master_deck": Counter(),
        "relics": Counter(),
        "damage_taken_by_enemy": defaultdict(Counter),
        "potions_obtained": defaultdict(Counter),
        "floors_visited": set(),
        "path_per_floor_counts": Counter(),  # <-- ADDED: Initialize aggregated counter
        "items_purchased": set(),
        "neow_bonus": Counter(),
        "build_version": set(),
        "purchased_purges": Counter(),
        "events": Counter(),
        "neow_cost": Counter(),
        "is_trial": Counter(),
        "character_chosen": Counter(),
        "is_prod": Counter(),
        "is_daily": Counter(),
        "chose_seed": Counter(),
        "circlet_count": Counter(),
        "win_rate": Counter(),
        "is_beta": Counter(),
        "is_endless": Counter(),
        "special_seed": Counter(),
        # --- Metadata ---
        "_total_processed_logs": 0,
        "_total_modded_logs_skipped": 0,
        "_total_modded_reasons": Counter(),
        "_total_data_errors_in_logs": 0,
        "_total_filter_errors": 0,
        "_files_processed_successfully": 0,
        "_files_failed_processing": 0,
    }

    for file_result in all_results:
        if file_result is None:
            final_data["_files_failed_processing"] += 1
            continue

        final_data["_files_processed_successfully"] += 1

        # Aggregate metadata counters
        final_data["_total_processed_logs"] += file_result.get(
            "processed_logs_count", 0
        )
        final_data["_total_modded_logs_skipped"] += file_result.get(
            "modded_logs_skipped", 0
        )
        final_data["_total_data_errors_in_logs"] += file_result.get("errors", 0)
        final_data["_total_filter_errors"] += file_result.get("filter_errors", 0)
        final_data["_total_modded_reasons"].update(
            file_result.get("modded_reasons", Counter())
        )

        # --- Aggregate all data fields (Counters, Sets, defaultdicts) ---
        final_data["floor_reached"].update(file_result.get("floor_reached", Counter()))
        final_data["master_deck"].update(file_result.get("master_deck", Counter()))
        final_data["relics"].update(file_result.get("relics", Counter()))
        final_data["purchased_purges"].update(
            file_result.get("purchased_purges", Counter())
        )
        final_data["events"].update(file_result.get("events", Counter()))
        final_data["neow_bonus"].update(file_result.get("neow_bonus", Counter()))
        final_data["neow_cost"].update(file_result.get("neow_cost", Counter()))
        final_data["is_trial"].update(file_result.get("is_trial", Counter()))
        final_data["character_chosen"].update(
            file_result.get("character_chosen", Counter())
        )
        final_data["is_prod"].update(file_result.get("is_prod", Counter()))
        final_data["is_daily"].update(file_result.get("is_daily", Counter()))
        final_data["chose_seed"].update(file_result.get("chose_seed", Counter()))
        final_data["circlet_count"].update(file_result.get("circlet_count", Counter()))
        final_data["win_rate"].update(file_result.get("win_rate", Counter()))
        final_data["is_beta"].update(file_result.get("is_beta", Counter()))
        final_data["is_endless"].update(file_result.get("is_endless", Counter()))
        final_data["special_seed"].update(file_result.get("special_seed", Counter()))

        # --- ADDED: Aggregate the new counter ---
        final_data["path_per_floor_counts"].update(
            file_result.get("path_per_floor_counts", Counter())
        )
        # --- END ADDED ---

        final_data["floors_visited"].update(file_result.get("floors_visited", set()))
        final_data["items_purchased"].update(file_result.get("items_purchased", set()))
        final_data["build_version"].update(file_result.get("build_version", set()))

        damage_taken = file_result.get("damage_taken_by_enemy")
        if damage_taken:
            for enemy, counts in damage_taken.items():
                if isinstance(counts, Counter):
                    final_data["damage_taken_by_enemy"][enemy].update(counts)
        potions_obtained = file_result.get("potions_obtained")
        if potions_obtained:
            for potion, counts in potions_obtained.items():
                if isinstance(counts, Counter):
                    final_data["potions_obtained"][potion].update(counts)
        # --- End Aggregation of data fields ---

    logging.info("Aggregation complete.")
    # (Keep existing logging for metadata totals)
    logging.info(
        f"Total non-modded logs processed: {final_data['_total_processed_logs']:_}"
    )
    logging.info(
        f"Total modded logs skipped: {final_data['_total_modded_logs_skipped']:_}"
    )
    if final_data["_total_data_errors_in_logs"] > 0:
        logging.warning(
            f"Total data errors within log entries: {final_data['_total_data_errors_in_logs']}"
        )
    if final_data["_total_filter_errors"] > 0:
        logging.warning(
            f"Total errors during filter check execution: {final_data['_total_filter_errors']}"
        )
    if final_data["_files_failed_processing"] > 0:
        logging.warning(
            f"Total files failed processing (read/JSON errors): {final_data['_files_failed_processing']}"
        )

    if final_data["_total_modded_reasons"]:
        logging.info("Breakdown of reasons for skipping modded logs:")
        sorted_reasons = sorted(
            final_data["_total_modded_reasons"].items(),
            key=lambda item: item[1],
            reverse=True,
        )
        for reason, count in sorted_reasons:
            logging.info(f"  - {reason}: {count:_}")
    else:
        logging.info("No logs were skipped due to modding flags.")

    return final_data


# --- Main Execution (Unchanged) ---
if __name__ == "__main__":
    start_time = time.time()
    logging.info(f"Starting log processing using up to {MAX_WORKERS} processes.")

    if not log_path or not log_path.is_dir():
        logging.error(f"Log path not found or not a directory: {log_path}")
        exit(1)

    all_entries = list(log_path.iterdir())
    files_to_process = [f for f in all_entries if f.is_file()]
    num_files = len(files_to_process)
    logging.info(
        f"Found {len(all_entries)} entries in {log_path}, processing {num_files} files."
    )

    if num_files == 0:
        logging.warning("No files found to process.")
        exit(0)

    results_from_workers = []
    files_returned_data_count = 0
    files_returned_none_count = 0
    total_files_iterator_handled = 0

    logging.info(f"Submitting {num_files} file processing tasks to Pool...")
    try:
        with Pool(processes=MAX_WORKERS) as pool:
            results_iterator = pool.imap_unordered(process_log_file, files_to_process)

            for result in results_iterator:
                total_files_iterator_handled += 1
                if result is not None:
                    results_from_workers.append(result)
                    files_returned_data_count += 1
                else:
                    files_returned_none_count += 1

                if (
                    total_files_iterator_handled % 500 == 0
                    or total_files_iterator_handled == num_files
                ):
                    logging.info(
                        f"Progress: {total_files_iterator_handled}/{num_files} tasks completed "
                        f"({files_returned_data_count} succeeded, {files_returned_none_count} failed)."
                    )

    except Exception as e:
        logging.exception(f"Error during multiprocessing pool execution: {e}")

    logging.info(
        f"Pool processing finished. Files returned data: {files_returned_data_count}, "
        f"Files returned None (failed): {files_returned_none_count}"
    )

    if results_from_workers:
        final_aggregated_data = aggregate_results(results_from_workers)

        logging.info(f"Saving aggregated data to {OUTPUT_PICKLE_FILE}...")
        try:
            with open(OUTPUT_PICKLE_FILE, "wb") as f:
                pickle.dump(final_aggregated_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            logging.info("Data saved successfully.")
        except Exception as e:
            logging.exception(f"Failed to save pickle file: {e}")
    else:
        logging.warning(
            "No results successfully processed. Skipping aggregation/saving."
        )

    end_time = time.time()
    logging.info(f"Total processing time: {end_time - start_time:.2f} seconds")
