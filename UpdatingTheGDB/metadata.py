import arcpy
import csv
import sys
import os

# Defining required CSV column names and a flag for case-insensitive matching
REQUIRED_HEADERS = ["object", "summary", "description"]
ALLOW_CASE_INSENSITIVE_HEADERS = True  # set to False if case matching is needed

# Printing usage text and an example call.
def print_usage():
    print(
        "Usage:\n"
        "  python script.py <path_to_gdb_or_sde> <path_to_csv>\n\n"
        "Example:\n"
        r"  python script.py C:\path\to\cscl.gdb C:\path\to\metadatest.csv\n"
    )

# Trimming and lowercasing headers to compare reliably.
def normalize_headers(headers):
    return [h.strip().lower() for h in headers] if headers else []

# Checking that the CSV has all required headers and logging messages.
# Allowing case-insensitive matching when ALLOW_CASE_INSENSITIVE_HEADERS is True
def validate_headers(fieldnames, log_file):
    # if header row is missing/empty
    if fieldnames is None:
        msg = "The CSV appears to be empty/has no headers."
        log_file.write(msg + "\n")
        print(msg)
        return False

    # if using case-insensitive header matching
    if ALLOW_CASE_INSENSITIVE_HEADERS:
        fields = normalize_headers(fieldnames)
        required = set(REQUIRED_HEADERS)
        ok = required.issubset(set(fields))
    # else using strict case-sensitive matching
    else:
        fields = [h.strip() for h in fieldnames]
        ok = all(h in fields for h in REQUIRED_HEADERS)

    # if required headers are missing
    if not ok:
        msg = ("The header is not as written. Please fix the header or modify the script. "
               f"Required headers: {REQUIRED_HEADERS}. Found headers: {fieldnames}")
        log_file.write(msg + "\n")
        print(msg)
        return False
    return True

def main():
    # Checking if the code has necessary lines
    if len(sys.argv) < 3:
        print('Please input the csv/sde/path')
        print_usage()
        sys.exit(1)

    gdb_out = sys.argv[1]
    csv_in  = sys.argv[2]

    # Warning about missing/unknown gdb/sde path while still allowing arcpy.Exists to decide per-object
    if not os.path.exists(gdb_out):
        print(f"Warning: '{gdb_out}' does not exist on disk. Ensure this is a valid .gdb folder or .sde connection file.")

    # Exiting early when the CSV path is invalid to avoid file-open errors
    if not os.path.isfile(csv_in):
        print(f"Please input the csv. File not found: {csv_in}")
        sys.exit(1)

    # Resolving script directory and building a stable path to the log file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'log.txt')

    # Creating/overwriting the log to provide a fresh audit trail for each run
    with open(log_path, 'w') as log_file:
        log_file.write("Metadata Update Log\n")
        log_file.write("===================\n\n")
        log_file.flush()

        # Opening the CSV and constructing a DictReader for header-keyed access
        with open(csv_in, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)

            # Validating the header row before processing to avoid runtime key errors
            if not validate_headers(reader.fieldnames, log_file):
                log_file.write("Could not find proper header.\n")
                sys.exit(1)

            # Allowing case insensitive headers if ALLOW_CASE_INSENSITIVE_HEADERS = True
            if ALLOW_CASE_INSENSITIVE_HEADERS:
                header_map = {h.lower(): h for h in reader.fieldnames}
                def get_cell(row, key):
                    """Fetching a cell by logical key using the original header name when case-insensitive mode is enabled."""
                    return row.get(header_map[key], None)
            else:
                def get_cell(row, key):
                    """Fetching a cell directly by exact header name when case-sensitive mode is enforced."""
                    return row.get(key, None)

            # Initializing counters for a concise end-of-run summary
            updated_count = 0
            errors = 0

            # Iterating CSV data rows, starting at 2 so the counter matches line numbers (header is line 1)
            for csv_line, row in enumerate(reader, start=2):
                # Normalizing the object name and fetching metadata fields from the row
                obj_name    = (get_cell(row, "object") or "").strip()
                summary     = get_cell(row, "summary")
                description = get_cell(row, "description")

                # Skipping rows with missing object names to avoid invalid paths
                if not obj_name:
                    msg = f"Row {csv_line}: 'object' is empty. Skipping."
                    with open(log_path, 'a') as _append:
                        _append.write(msg + "\n")
                    print(msg)
                    errors += 1
                    continue

                # Logging a concise per-row summary for traceability
                log_message = f"Row {csv_line} | Object: {obj_name}, Summary: {summary}, Description length: {len(description or '')}"
                with open(log_path, 'a') as _append:
                    _append.write(log_message + "\n")

                # Building the full path to the target dataset inside the geodatabase/SDE
                object_path = os.path.join(gdb_out, obj_name)

                try:
                    if arcpy.Exists(object_path):
                        # Getting the live metadata handle for the target dataset
                        object_metadata = arcpy.metadata.Metadata(object_path)

                        # Writing only non-empty values to avoid unintentionally clearing existing metadata
                        if summary is not None and str(summary).strip() != "":
                            object_metadata.summary = summary

                        if description is not None and str(description).strip() != "":
                            object_metadata.description = description

                        # Saving changes so edits persist to the dataset
                        object_metadata.save()
                        updated_count += 1
                    else:
                        # Recording and reporting a missing dataset while continuing to the next row
                        error_message = f"Row {csv_line}: {object_path} doesn't exist."
                        with open(log_path, 'a') as _append:
                            _append.write(error_message + "\n")
                        print(error_message)
                        errors += 1

                except Exception as e:
                    # Catching and logging unexpected ArcPy or I/O errors per row to keep the batch running
                    error_message = f"Row {csv_line}: Error updating metadata for '{object_path}': {e}"
                    with open(log_path, 'a') as _append:
                        _append.write(error_message + "\n")
                    print(error_message)
                    errors += 1

            # Emitting a final summary to the log and stdout to aid quick verification
            summary_line = f"\nMetadata update completed. Updated: {updated_count}, Errors/Skipped: {errors}."
            with open(log_path, 'a') as _append:
                _append.write(summary_line + "\n")
            print(summary_line)

if __name__ == '__main__':
    main()
