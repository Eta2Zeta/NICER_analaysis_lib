import os

def rename_files(directory):
    # Change to the specified directory
    os.chdir(directory)
    
    # List all files in the directory
    files = os.listdir('.')
    
    # Loop through the files
    for filename in files:
        # Replace 'underonly' with 'uo' and 'overonly' with 'oo'
        new_filename = filename.replace('underonly', 'uo').replace('overonly', 'oo')
        
        # Rename the file if there is a change
        if new_filename != filename:
            os.rename(filename, new_filename)
            print(f"Renamed '{filename}' to '{new_filename}'")

# Usage example
directory = '/Users/hongyuzhang/Documents/data/her_x-1/2022_data/3602020601/xti/analysis/GTI1'
rename_files(directory)
