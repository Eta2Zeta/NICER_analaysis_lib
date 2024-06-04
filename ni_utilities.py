import csv
import os

def observationalID():
    while True:  # Keep looping until we get a valid input
        user_input = input("What is the observation ID? (01 to 15): ")
        if user_input.isdigit() and 1 <= int(user_input) <= 15:
            obsID = '360202' + user_input.zfill(2) + '01'
            return obsID
        else:
            print("Invalid input. Please enter a number between 01 and 15.")
            break  # Break the loop and exit the function if the input is invalid

    
def load_timing_parameters(data_path, obs_id_gti):
    filename = os.path.join(data_path, "timing_parameters.txt")
    with open(filename, mode='r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header
        for row in reader:
            if row[0] == obs_id_gti:
                return {
                    'tstart': float(row[1]),
                    'fr': float(row[2]),
                    'frdot': float(row[3])
                }
    return None  # Return None if the specific ID is not found