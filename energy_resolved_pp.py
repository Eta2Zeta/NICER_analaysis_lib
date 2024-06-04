import os
import subprocess
import shutil
import re
import numpy as np
from ni_utilities import observationalID, load_timing_parameters
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from hendrics.io import load_events
from stingray.pulse.pulsar import fold_events

DATAPATH = '/Users/hongyuzhang/Documents/data/her_x-1/2022_data'
#Used for equal energy intervals, if set to 0, custum intervals will be used
INTERVAL = 0 
CUSTOM_INTERVALS = [5,8,14,100]
RMF_FILE = "nixtiref20170601v003.rmf"
RMF_DIR = '/Users/hongyuzhang/Documents/soft/caldb/data/nicer/xti/cpf/rmf'
PULSE_PROFILE_DIR = "pulse_profiles"
PBIN = 128



def create_xspec_script(analysis_dir, base_filename, start, end, interval):
    script_path = os.path.join(analysis_dir, "process_all.xcm")
    
    with open(script_path, "w") as f:        
        # Write the initial commands to load the data
        f.write("xsel1\n")
        f.write(f"read events {base_filename}.evt\n")
        f.write(".\n")
        f.write("yes\n")
        
        if INTERVAL == 0:  # Use custom intervals
            for i in range(len(CUSTOM_INTERVALS) - 1):
                pi_start = CUSTOM_INTERVALS[i] * 10
                pi_end = CUSTOM_INTERVALS[i + 1] * 10
                new_file = f"{base_filename}_E{CUSTOM_INTERVALS[i]}_{CUSTOM_INTERVALS[i + 1]}.evt"
                f.write(f'filter column "PI={pi_start}:{pi_end}"\n')
                f.write("extract events\n")
                f.write(f"save events {new_file}\n")
                f.write("no\n")
                f.write("clear all\n")
                f.write("yes\n")
                f.write(f"read events {base_filename}.evt\n")
                f.write(".\n")
        else:  # Use equal intervals
            # Loop over the PI range to filter and save new event files
            for i in range(start, end + 1, interval):
                pi_start = i * 10
                pi_end = (i + interval) * 10
                new_file = f"{base_filename}_E{i}_{i+interval}.evt"
                
                # Filter by the PI range, extract, and save the events
                f.write(f'filter column "PI={pi_start}:{pi_end}"\n')
                f.write("extract events\n")
                f.write(f"save events {new_file}\n")
                f.write("no\n")  # Respond 'no' to the prompt asking to use filtered events as input
                
                # Clear all selections and reload the original events file to start fresh
                f.write("clear all\n")
                f.write("yes\n")  # Confirm to clear all data
                f.write(f"read events {base_filename}.evt\n")
                f.write(".\n")  # No need for 'yes' after the first time

        # Write the commands to exit xselect
        f.write("quit\n")
        f.write("no\n")
    
    print(f"Created XSPEC script at: {script_path}")

def process_energy_resolved_files(base_filename, analysis_dir, rmf_file):
    # Regular expression to match files and extract energy intervals
    pattern = re.compile(rf'{re.escape(base_filename)}_E(\d+)_(\d+)\.evt$')

    # Search for matching .evt files in the directory
    evt_files = [f for f in os.listdir(analysis_dir) if pattern.match(f)]

    print(evt_files)
    
    for evt_file in evt_files:
        # Extract the energy intervals from the filename
        match = pattern.search(evt_file)
        if match:
            start_energy, end_energy = match.groups()

            nicer_xti_file = f'{base_filename}_E{start_energy}_{end_energy}_nicer_xti_ev.nc'
            calib_file = f'{base_filename}_E{start_energy}_{end_energy}_nicer_xti_ev_calib.nc'
            full_evt_file_path = os.path.join(analysis_dir, evt_file)
            full_nicer_xti_file_path = os.path.join(analysis_dir, nicer_xti_file)
            full_calib_file_path = os.path.join(analysis_dir, calib_file)

            # Check if the NICER XTI file is already there
            if not os.path.exists(full_nicer_xti_file_path):
                command1 = f'HENreadevents {full_evt_file_path}'
                subprocess.run(command1, shell=True)
                print(f"Processed {evt_file} to {nicer_xti_file}")
            else:
                print(f"{nicer_xti_file} already exists, skipping HENreadevents.")

            # Check if the calibrated file is already there
            if not os.path.exists(full_calib_file_path):
                command2 = f'HENcalibrate {full_nicer_xti_file_path} -r {rmf_file}'
                subprocess.run(command2, shell=True)
                print(f"Calibrated {nicer_xti_file} to {calib_file}")
            else:
                print(f"{calib_file} already exists, skipping HENcalibrate.")

def plot_energy_resolved_pulse_profiles(analysis_dir, base_filename, pbin, fr, frdot, tstart):
    pulse_profile_path = os.path.join(analysis_dir, PULSE_PROFILE_DIR)
    if not os.path.exists(pulse_profile_path):
        os.makedirs(pulse_profile_path)

    full_energy_file = os.path.join(analysis_dir, f"{base_filename}_nicer_xti_ev_calib.nc")
    try:
        full_energy_events = load_events(full_energy_file)
        _, full_profile, _ = fold_events(full_energy_events.time, fr, frdot, ref_time=tstart, nbin=pbin)
        full_min_index = np.argmin(full_profile)
        full_shift = (pbin // 10) - full_min_index
    except FileNotFoundError:
        print(f"File not found: {full_energy_file}")
        return  # If the full energy file isn't found, exit the function

    energy_list = CUSTOM_INTERVALS if INTERVAL == 0 else range(5, 100, INTERVAL)

    for i in range(len(energy_list) - 1):
        e1 = energy_list[i]
        e2 = energy_list[i + 1]
        label_name = f"{e1}-{e2}keV"
        f_name = f"{base_filename}_E{e1}_{e2}_nicer_xti_ev_calib.nc"
        full_path = os.path.join(analysis_dir, f_name)

        try:
            nicer_events = load_events(full_path)
            ph, profile, profile_err = fold_events(nicer_events.time, fr, frdot, ref_time=tstart, nbin=pbin)
            mean_rate = np.mean(profile)
            profile /= mean_rate
            profile_err /= mean_rate
            profile_shifted = np.roll(profile, full_shift)
            profile_err_shifted = np.roll(profile_err, full_shift)
            profile_extended = np.tile(profile_shifted, 3)
            profile_err_extended = np.tile(profile_err_shifted, 3)

            plt.figure(figsize=(10, 5))
            plt.errorbar(np.arange(len(profile_extended)) / pbin, profile_extended, profile_err_extended, color='blue', drawstyle='steps-mid', label=label_name)
            plt.xlabel("Phase", fontsize=16)
            plt.ylabel("Normalized Count Rate (cts/s)", fontsize=16)
            plt.title(f"Her X-1, {base_filename}, Energy: {label_name}", fontsize=16)
            plt.legend(loc="upper right")
            plt.tick_params(labelsize=16)
            plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%.2f'))  # This line sets the y-axis labels to 2 decimal places
            plt.xlim([0, 2])
            plt.tight_layout(pad=0.5)
            plt.savefig(os.path.join(pulse_profile_path, f"herx1_nicer_pp_en_{label_name}.png"))
            plt.close()
        except FileNotFoundError:
            print(f"File not found: {full_path}")


def main():
    nicerdir = DATAPATH
    obsID = observationalID()
    datasetdir = os.path.join(nicerdir, obsID)
    xtidir = os.path.join(datasetdir, 'xti')
    analysis_dir = os.path.join(xtidir, 'analysis')
    

    # List all GTI folders and ask the user to select one
    gti_folders = [f for f in os.listdir(analysis_dir) if f.startswith("GTI")]

    # If GTI folders are found, let the user choose one
    if gti_folders:
        print("Available GTI folders:")
        for index, folder in enumerate(gti_folders, 1):
            print(f"{index}: {folder}")
        
        gti_choice = int(input("Select a GTI folder by entering its number: ")) - 1
        if gti_choice >= 0 and gti_choice < len(gti_folders):
            gti_folder = gti_folders[gti_choice]
            analysis_dir = os.path.join(analysis_dir, gti_folder)
            gti_number = re.search(r'GTI(\d+)', gti_folder).group(1)  # Extracting the number from the folder name
            gti_pattern = f"_GTI{gti_number}_"
            obs_id_gti = f"{obsID}_GTI{gti_number}"
        else:
            print("Invalid GTI folder selection. Proceeding with the default analysis directory.")
            gti_pattern = "_"
            obs_id_gti = obsID  # Use the obsID alone if GTI is not applicable
    else:
        print("No GTI folders found. Proceeding with the default analysis directory.")
        gti_pattern = "_"
        obs_id_gti = obsID


    # Load timing parameters
    timing_params = load_timing_parameters(DATAPATH, obs_id_gti)
    if timing_params:
        tstart = timing_params['tstart']
        fr = timing_params['fr']
        frdot = timing_params['frdot']
    else:
        print("Timing parameters not found for this observation and GTI.")
        return  # Exit if parameters are not found


    # Adjust the event file pattern based on whether a GTI folder is selected
    evt_pattern = rf'ni\d+_0mpu7_cl_uo\d+_oo\d+{gti_pattern}bary_scorr\.evt'

    # Find the actual event files matching the adjusted pattern
    evt_files = [f for f in os.listdir(analysis_dir) if re.search(evt_pattern, f)]
    if not evt_files:
        raise FileNotFoundError("No event file found matching the pattern.")
    
    # Assume the first matching file is the file to use
    actual_evt_file = evt_files[0]
    match = re.search(r"uo(\d+)_oo(\d+)", actual_evt_file)
    if match:
        underonly_num = match.group(1)
        overonly_num = match.group(2)
        if gti_folders: 
            base_filename = f"ni{obsID}_0mpu7_cl_uo{underonly_num}_oo{overonly_num}_{gti_folder}_bary_scorr"
        else: 
            base_filename = f"ni{obsID}_0mpu7_cl_uo{underonly_num}_oo{overonly_num}_bary_scorr"
    else:
        raise ValueError("Filename pattern does not match expected format.")
    
    # Decision point to call specific functions based on whether custom ranges are used
    if INTERVAL == 0:
        # Call functions to handle custom energy ranges
        custom_folder_name = f"energy_resolved_pp_E{'-'.join(map(str, CUSTOM_INTERVALS))}_bin{PBIN}"
        energy_resolved_analysis_dir = os.path.join(analysis_dir, custom_folder_name)

    else:
        # Call standard functions as before
        # Ensure the analysis directory exists
        energy_resolved_analysis_dir = os.path.join(analysis_dir, f"energy_resolved_pp_it{INTERVAL}_bin{PBIN}")


    if not os.path.exists(energy_resolved_analysis_dir):
        os.makedirs(energy_resolved_analysis_dir)

    # Copy the base event file and the RMF file to the analysis directory
    shutil.copy(os.path.join(analysis_dir, f"{base_filename}.evt"), energy_resolved_analysis_dir)
    shutil.copy(os.path.join(RMF_DIR, RMF_FILE), energy_resolved_analysis_dir)

    # Ask user if they want to generate the XSPEC script
    generate_script = input("Do you want to generate the XSPEC script now? [yes/no]: ").strip().lower()
    if generate_script == 'yes':
        create_xspec_script(energy_resolved_analysis_dir, base_filename, 5, 100, INTERVAL)
    else:
        print("XSPEC script generation skipped.")

    # Ask user if they want to execute the XSPEC script
    execute_script = input("Do you want to execute the XSPEC script now? [yes/no]: ").strip().lower()
    if execute_script == 'yes':
        os.chdir(energy_resolved_analysis_dir)  # Change to the correct directory
        command = f"xselect @process_all.xcm"
        subprocess.run(command, shell=True)
        print("XSPEC script executed successfully.")
    else:
        os.chdir(energy_resolved_analysis_dir)  # Change to the correct directory
        print(f"Now at: {energy_resolved_analysis_dir}")

    # Ask user if they want to calibrate using HENDRICS
    HENDRICS = input("Do you want to use HENDRICS to calibrate? [yes/no]: ").strip().lower()
    if HENDRICS == 'yes':
        # First calibrate the full energy event file
        full_energy_evt_file = f"{base_filename}.evt"
        full_energy_nicer_xti_file = f"{base_filename}_nicer_xti_ev.nc"
        full_energy_calib_file = f"{base_filename}_nicer_xti_ev_calib.nc"
        
        # Check if the NICER XTI file is already there
        if not os.path.exists(full_energy_nicer_xti_file):
            command1_full = f'HENreadevents {full_energy_evt_file}'
            subprocess.run(command1_full, shell=True)
            print(f"Processed {full_energy_evt_file} to {full_energy_nicer_xti_file}")
        else:
            print(f"{full_energy_nicer_xti_file} already exists, skipping HENreadevents.")

        # Check if the calibrated file is already there
        if not os.path.exists(full_energy_calib_file):
            command2_full = f'HENcalibrate {full_energy_nicer_xti_file} -r {RMF_FILE}'
            subprocess.run(command2_full, shell=True)
            print(f"Calibrated {full_energy_nicer_xti_file} to {full_energy_calib_file}")
        else:
            print(f"{full_energy_calib_file} already exists, skipping HENcalibrate.")

        # Then proceed with energy-resolved calibration
        process_energy_resolved_files(base_filename, energy_resolved_analysis_dir, RMF_FILE)
    else:
        print("HENDRICS not executed")



    # Ask user if they want to plot pulse profile
    plot_pp = input("Do you want to plot pulse profiles now? [yes/no]: ").strip().lower()
    if plot_pp == 'yes':
        plot_energy_resolved_pulse_profiles(energy_resolved_analysis_dir, base_filename, PBIN, fr, frdot, tstart)
    else:
        print("PP not plotted")

if __name__ == "__main__":
    main()
