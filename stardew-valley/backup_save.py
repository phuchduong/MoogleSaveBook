"""
Author: phuchduong
Last Updated: 2026-04-19
Version: 1.0

This script copies the contents of the CeladonCreek save folder to a local
repository folder. It creates a dated backup folder to ensure history is 
preserved and provides verbose console logging for each file moved.
"""

import os
import shutil
from datetime import datetime

# The specific farm save folder location on your Windows 11 machine
SOURCE_PATH = r'C:\Users\Phuc\AppData\Roaming\StardewValley\Saves\CeladonCreek_436060727'

# The repository directory where backups will be stored.
# The script is intended to be run from inside this directory.
DEST_PARENT = r'C:\repos\MoogleSaveBook\stardew-valley'

def run_backup():
    # Capture the current date to suffix the folder name.
    # This creates a folder like save_2026_04_19.
    current_date = datetime.now().strftime('%Y_%m_%d')
    folder_name = f'save_{current_date}'
    
    # Construct the full path for the new folder within the repository.
    full_dest_path = os.path.join(DEST_PARENT, folder_name)

    print('Initializing Stardew Valley backup...')
    print(f'Checking source path: {SOURCE_PATH}')

    # Validate that the source files actually exist before attempting copy.
    if not os.path.exists(SOURCE_PATH):
        print('Abort: The source folder was not found. Please check the path.')
        return

    # Create the destination directory if it does not already exist.
    try:
        if not os.path.exists(full_dest_path):
            os.makedirs(full_dest_path)
            print(f'Directory created: {folder_name}')
        else:
            print(f'Directory already exists: {folder_name}. Files may be updated.')
    except Exception as error:
        print(f'Critical Error: Could not create folder. {error}')
        return

    # Loop through all files in the save folder to perform the backup.
    print('Starting file transfer...')
    try:
        files_to_copy = os.listdir(SOURCE_PATH)
        
        for file in files_to_copy:
            source_file = os.path.join(SOURCE_PATH, file)
            dest_file = os.path.join(full_dest_path, file)

            # Check if the item is a file to avoid errors with subfolders.
            if os.path.isfile(source_file):
                print(f'Processing: {file}')
                print(f'  Source Location: {source_file}')
                print(f'  Target Location: {dest_file}')
                
                # Copying the file while preserving metadata like timestamps.
                shutil.copy2(source_file, dest_file)
                print('  Status: OK')
            else:
                # If there are subdirectories, they are logged as skipped.
                print(f'Skipping item: {file} (Not a file)')
                
    except Exception as error:
        print(f'Error during copy: {error}')

    print('Backup process finished successfully.')

if __name__ == '__main__':
    # Execute the backup function.
    run_backup()
