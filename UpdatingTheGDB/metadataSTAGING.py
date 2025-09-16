import arcpy
import csv
import sys
import os

REQUIRED_HEADERS = ["object", "summary", "description"]
ALLOW_CASE_INSENSITIVE_HEADERS = True  # set to False if case matching is needed

def print_usage():
    print(
        "Usage:\n"
        "  python script.py <path_to_gdb_or_sde> <path_to_csv>\n\n"
        "Example:\n"
        r"  python script.py C:\path\to\cscl.gdb C:\path\to\metadatest.csv\n"
    )

def normalize_headers(headers):
    return [h.strip().lower() for h in headers] if headers else []

def validate_headers(fieldnames, log_file):
    if fieldnames is None:
        msg = "The CSV appears to be empty/has no headers."
        log_file.write(msg + "\n")
        print(msg)
        return False

    if ALLOW_CASE_INSENSITIVE_HEADERS:
        fields = normalize_headers(fieldnames)
        required = set(REQUIRED_HEADERS)
        ok = required.issubset(set(fields))
    else:
        fields = [h.strip() for h in fieldnames]
        ok = all(h in fields for h in REQUIRED_HEADERS)

    if not ok:
        msg = ("The header is not as written. Please fix the header or modify the script. "
               f"Required headers: {REQUIRED_HEADERS}. Found headers: {fieldnames}")
        log_file.write(msg + "\n")
        print(msg)
        return False
    return True

def main():
    if len(sys.argv) < 3:
        print('Please input the csv/sde/path')
        print_usage()
        sys.exit(1)

    gdb_out = sys.argv[1]
    csv_in  = sys.argv[2]

  
    if not os.path.exists(gdb_out):
        print(f"Warning: '{gdb_out}' does not exist on disk. Ensure this is a valid .gdb folder or .sde connection file.")
       

    if not os.path.isfile(csv_in):
        print(f"Please input the csv. File not found: {csv_in}")
        sys.exit(1)

--
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'log.txt')

    with open(log_path, 'w') as log_file:
        log_file.write("Metadata Update Log\n")
        log_file.write("===================\n\n")
        log_file.flush()

        with open(csv_in, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            if not validate_headers(reader.fieldnames, log_file):
                log_file.write("Could not find proper header.\n")
                sys.exit(1)

            if ALLOW_CASE_INSENSITIVE_HEADERS:
                header_map = {h.lower(): h for h in reader.fieldnames}
                def get_cell(row, key):
                    return row.get(header_map[key], None)
            else:
                def get_cell(row, key):
                    return row.get(key, None)

            updated_count = 0
            errors = 0

            for csv_line, row in enumerate(reader, start=2):
                obj_name    = (get_cell(row, "object") or "").strip()
                summary     = get_cell(row, "summary")
                description = get_cell(row, "description")

                if not obj_name:
                    msg = f"Row {csv_line}: 'object' is empty. Skipping."
                    log_file.write(msg + "\n")
                    print(msg)
                    errors += 1
                    continue

                log_message = f"Row {csv_line} | Object: {obj_name}, Summary: {summary}, Description length: {len(description or '')}"
                log_file.write(log_message + "\n")
                log_file.flush()

                object_path = os.path.join(gdb_out, obj_name)

                try:
                    if arcpy.Exists(object_path):
                        object_metadata = arcpy.metadata.Metadata(object_path)

                        if summary is not None and str(summary).strip() != "":
                            object_metadata.summary = summary

                        if description is not None and str(description).strip() != "":
                            object_metadata.description = description

                        object_metadata.save()
                        updated_count += 1
                    else:
                        error_message = f"Row {csv_line}: {object_path} doesn't exist."
                        log_file.write(error_message + "\n")
                        print(error_message)
                        errors += 1

                except Exception as e:
                    error_message = f"Row {csv_line}: Error updating metadata for '{object_path}': {e}"
                    log_file.write(error_message + "\n")
                    print(error_message)
                    errors += 1

            summary_line = f"\nMetadata update completed. Updated: {updated_count}, Errors/Skipped: {errors}."
            log_file.write(summary_line + "\n")
            print(summary_line)

if __name__ == '__main__':
    main()
