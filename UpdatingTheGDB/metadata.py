import arcpy
import csv
import sys
import os

if __name__ == '__main__':
    
    # Basic input error handling, if less than 4 lines, python, script, gdb, 
    if len(sys.argv) < 3:
        print('Please make sure you have the python environment setup, and have input the correct the csv/gdb/sde')
        sys.exit(1)

    gdb_out = sys.argv[1]  # E.G: C:\Users\USERNAME\metadata\cscl.gdb
    csv_in  = sys.argv[2]  # E.G: C:\Users\USERNAME\metadata\MetadataUpdated.csv

    # Getting the path of the folder where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(script_dir, 'log.txt') # Creating log.txt on the same folder as the script

    # Opening log file for writing
    with open(log_path, 'w') as log_file:
        log_file.write("Metadata Update Log\n")
        log_file.write("===================\n\n")

        # Opening CSV and validate header before processing rows
        with open(csv_in, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)  # Read the file as a dictionary

            required_headers = ['object', 'summary', 'description']
            fieldnames = reader.fieldnames if reader.fieldnames else []
            
            #Validating the headers
            if not fieldnames or any(h not in fieldnames for h in required_headers):
                warn_msg = "the header in not as written. Please fix the header or modify the script"
                log_file.write(warn_msg + "\n")
                print(warn_msg)
                sys.exit(1)

            for row in reader:
                # Write to log.txt
                log_message = f"Object: {row['object']}, Summary: {row['summary']}, Description: {row['description']}\n"
                log_file.write(log_message)
                log_file.flush()
                
                
                # Combining the geodatabase and the csv
                object_path = os.path.join(gdb_out, row['object'])

                new_metadata = arcpy.metadata.Metadata()
                
                # Checking & loading the metadata
                if arcpy.Exists(object_path):
                    object_metadata = arcpy.metadata.Metadata(object_path)
                    new_metadata    = object_metadata
                    
                    # Updating the summary and descriptions of the Metadata
                    if row['summary'] is not None:
                        object_metadata.summary = row['summary']

                    if row['description'] is not None:
                        object_metadata.description = row['description']
                    
                # Error message if the database doesn't exist    
                else:
                    error_message = f'{object_path} doesnt exist\n'
                    log_file.write(error_message)
                    raise ValueError(error_message)

                object_metadata.copy(new_metadata)
                object_metadata.save()

        log_file.write("\nMetadata update completed successfully.\n")
