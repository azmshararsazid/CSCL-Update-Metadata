import arcpy
import csv
import sys
import os

if __name__ == '__main__':

    gdb_out = sys.argv[1]  # Geodatabase/SDE path
    csv_in  = sys.argv[2]  # Input CSV path

    # Resolve script directory and build log path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'log.txt')

    # Create/overwrite the log file
    with open(log_path, 'w') as log_file:
        log_file.write("Metadata Update Log\n")
        log_file.write("===================\n\n")
        
        # Open CSV and create a DictReader (rows as dicts keyed by headers)
        with open(csv_in, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row in reader:  # Iterate each CSV row
                # Log the intended update for this row
                log_message = f"Object: {row['object']}, Summary: {row['summary']}, Description: {row['description']}\n"
                log_file.write(log_message)
                log_file.flush()
 
                # Build full dataset path inside the geodatabase/SDE
                object_path = os.path.join(gdb_out, row['object'])
                
                # Prepare a new Metadata object
                new_metadata = arcpy.metadata.Metadata()
 
                if arcpy.Exists(object_path):  # Proceed only if the dataset exists
                    # Get the target dataset's metadata handle
                    object_metadata = arcpy.metadata.Metadata(object_path)
                    new_metadata    = object_metadata
 
                    # Assign summary/description from CSV (if provided)
                    if row['summary'] is not None:
                        object_metadata.summary = row['summary']
                    if row['description'] is not None:
                        object_metadata.description = row['description']
                else:
                    # Log and raise if the dataset path is missing
                    error_message = f'{object_path} doesnt exist\n'
                    log_file.write(error_message)
                    raise ValueError(error_message)
                
                # Copy metadata fields and save changes
                object_metadata.copy(new_metadata)
                object_metadata.save()
        
        # Mark successful completion in the log
        log_file.write("\nMetadata update completed successfully.\n")
