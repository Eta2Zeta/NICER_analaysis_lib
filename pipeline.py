# Hongyu Zhang 04/20/2024
# Python code to standardize the nicerl2 pipeline of the 2022 Her X-1 data
# Currently under construction to streamline the process and naming conventions
# specifically for the 2022 data. 


import subprocess
import os
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
from astropy.io import fits

DATAPATH = '/Users/hongyuzhang/Documents/data/her_x-1/nicerl3_attempt'

def observationalID():
    while True:  # Keep looping until we get a valid input
        user_input = input("What is the observation ID? (01 to 15): ")
        if user_input.isdigit() and 1 <= int(user_input) <= 15:
            obsID = '360202' + user_input.zfill(2) + '01'
            return obsID
        else:
            print("Invalid input. Please enter a number between 01 and 15.")
            break  # Break the loop and exit the function if the input is invalid


def get_range(prompt, default):
    """
    Asks the user to input a range or use the default.
    Args:
    - prompt (str): The prompt message to show to the user.
    - default (str): The default range value if the user enters nothing.

    Returns:
    - str: The validated range entered by the user or the default value.
    """
    user_input = input(f"{prompt} [{default}]: ")
    if user_input.strip() == "":
        return default
    else:
        # Simple validation to check the format
        try:
            parts = user_input.split('-')
            assert len(parts) == 2, "Range must include two numbers separated by a dash."
            low, high = map(float, parts)  # This will raise ValueError if not float-able
            assert low < high, "The first number must be less than the second number."
            return user_input
        except (AssertionError, ValueError) as e:
            print(f"Invalid range. Error: {e}")
            return get_range(prompt, default)

def run_nicerl2_with_screen(obsID, nicerdir, underonly_range, overonly_range):
    """Run nicerl2 with SCREEN task using specified ranges."""
    os.chdir(nicerdir)
    nicerl2_command = f"nicerl2 {obsID} clobber=YES tasks=SCREEN overonly_range={overonly_range} underonly_range={underonly_range}"
    print(f"Running nicerl2 with command: {nicerl2_command}")
    subprocess.run(nicerl2_command, shell=True)


    
### Read GTI fork and plot it out visually
def plot_GTI(eventcldir, obsID):
    os.chdir(eventcldir)
    with fits.open(f'ni{obsID}_0mpu7_cl.evt') as evt:
        GTI = evt[3].data
        print(GTI)
        height = 10  # A constant to maintain line height in the plot

        # Extract start and end times from GTI data
        starts = GTI['START']
        stops = GTI['STOP']

        # Find the total observation period
        min_time = np.min(starts)
        max_time = np.max(stops)

        # Create line segments for GTI periods
        lines = [[(start - min_time, height), (stop - min_time, height)] for start, stop in zip(starts, stops)]
        lc = LineCollection(lines, colors='blue', linewidths=2)

        # Initialize plot
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.add_collection(lc)

        # Plot non-GTI regions
        # Start with the first non-GTI region before the first GTI
        if min_time < starts[0]:
            ax.axvspan(min_time - min_time, starts[0] - min_time, facecolor='red', alpha=0.5)
        
        # Plot intermediate non-GTI regions
        for i in range(len(stops) - 1):
            if starts[i+1] > stops[i]:
                ax.axvspan(stops[i] - min_time, starts[i+1] - min_time, facecolor='red', alpha=0.5)
        
        # Plot the last non-GTI region after the last GTI
        if max_time > stops[-1]:
            ax.axvspan(stops[-1] - min_time, max_time - min_time, facecolor='red', alpha=0.5)

        # Set plot limits and labels
        ax.set_xlim(min_time - min_time, max_time - min_time)
        ax.set_ylim(0, height * 1.2)
        ax.set_xlabel("Time since start (s)")
        ax.set_ylabel("GTI Status")
        ax.set_title(f"GTI Visualization for OBSID {obsID}")

        plt.show()



def plot_over_underonly(obsID):
    path = os.getcwd()
    os.chdir(path + '/auxil/')
    mkf_name = 'ni' + obsID + '.mkf'
    with fits.open(mkf_name) as mkf:
        # mkf.info()
        prefilter = mkf[1].data
        time = prefilter.field('TIME')
        sunshine = prefilter.field('SUNSHINE')
        num_fpm_on = prefilter.field('NUM_FPM_ON')
        overonly = prefilter.field("FPM_OVERONLY_COUNT")
        underonly = prefilter.field('FPM_UNDERONLY_COUNT')
        kp = prefilter.field('KP')
    fig, axs = plt.subplots(2, figsize=(12, 8))  # Adjust the figsize as needed
    # fig.suptitle('Overonly and Underonly')
    axs[0].plot(time,overonly,'ro',markersize = 1)
    axs[0].set_title('Overonly')
    axs[1].plot(time,underonly,'bo',markersize = 1)
    axs[1].set_title('Underonly')
    # plt.plot(time,overonly,'ro',time,underonly,'bo',markersize = 1)
    plt.show()

def main():
    nicerdir = DATAPATH
    obsID = observationalID()
    datasetdir = nicerdir + '/' + obsID
    eventcldir = datasetdir + '/xti/event_cl/'
    xtidir = datasetdir + '/xti/'


    ### running nicerl2
    nicerl2_one = input('Running nicerl2 for subprocesses CALMERGE and MKF? [yes] ')
    if nicerl2_one == '':
        nicerl2_one = 'yes'
    if nicerl2_one == 'yes':
        os.chdir(nicerdir)
        print("""We are running 
              CALMERGE: apply calibrations and merge the per-MPU event lists into a single merged 
              ufa file (nicercal and nimpumerge steps); and 
              MKF:  create updated filter file (niprefilter and niprefilter2 steps).""")
        # nicerl2 = "nicerl2 indir=" + obsID +  """ geomag_columns="kp_noaa.fits(KP)" clobber=yes > """ + obsID + "nicerl2.log"
        nicerl2 = "nicerl2 indir=" + obsID +  """ clobber=yes tasks=CALMERGE,MKF > """ + obsID + "nicerl2.log"
        print(nicerl2)
        subprocess.run(nicerl2, shell = True)

    ### ploting the overonly and underonly ranges
    view_mkf = input('Viewing overonly and underonly range? [yes]')
    if view_mkf == '':
        view_mkf = 'yes'
    if view_mkf == 'yes':
        os.chdir(datasetdir)
        plot_over_underonly(obsID)


    ### changing the OVER_ONLY and UNDER_ONLY range and run the nicerl2 again with new parameters
    # Set initial default values
    underonly_range = '0-500'
    overonly_range = '0-30'

    # Ask the user if they want to change the defaults
    change_ranges = input("Do you want to change the range for OVER_ONLY and UNDER_ONLY counts? [yes/no] (default: yes): ").strip().lower()
    if change_ranges == '' or change_ranges == 'yes':
        underonly_range = get_range("Enter new UNDER_ONLY range", underonly_range)
        overonly_range = get_range("Enter new OVER_ONLY range", overonly_range)
    
    print(f"Using UNDER_ONLY range: {underonly_range}")
    print(f"Using OVER_ONLY range: {overonly_range}")
    
    ### Run nicerl2 with the SCREEN task optionally
    run_screen = input("Run nicerl2 with SCREEN task? [yes/no] (default: no): ").strip().lower()
    if run_screen == 'yes':
        run_nicerl2_with_screen(obsID, nicerdir, underonly_range, overonly_range)


    view_gti = input('View Good Time Intervals (GTI)? [yes]: ')
    if view_gti == '':
        view_gti = 'yes'
    if view_gti.lower() == 'yes':
        plot_GTI(eventcldir, obsID)  # Assuming 'read_GTI' is predefined elsewhere in your script

    
    ### now filtering by kp index 
    kp_index_choice = input('Filter by kp index and SUN_ANGLE? [yes]')
    if kp_index_choice == '':
        kp_index_choice = 'yes'
    if kp_index_choice == 'yes':
        filter_kp = 'nimaketime infile=' + datasetdir + '/auxil/ni' + obsID + '.mkf outfile=' + datasetdir + '/auxil/ni' + obsID + '.mkf_gti1 cleanup=YES underonly_range=' + underonly_range + ' overonly_range="' + overonly_range + ' expr="SUN_ANGLE>60 && KP<5" chatter=5 clobber=yes'
        print(filter_kp)
        subprocess.run(filter_kp, shell = True)

    ### creating an analysis folder in the /xti/ folder
    mkdir = input('make analysis file? [yes]')
    if mkdir == '':
        mkdir = 'yes'
    if mkdir == 'yes': 
        os.chdir(xtidir)
        subprocess.run('mkdir analysis', shell = True)

    ### copying event file over to analysis
    cpevt = input('Copy event file to analysis dir? [yes]')
    if cpevt == '':
        cpevt = 'yes'
    if cpevt == 'yes':
        os.chdir(eventcldir)
        copy_evt = 'cp ni' + obsID + '_0mpu7_cl.evt ' + xtidir + 'analysis/'
        subprocess.run(copy_evt,shell = True)

    #TODO
    ### niextract 
    niextract = "niextract-events filename='" + xtidir + "/analysis/ni" + obsID + "_0mpu7_cl.evt[PI=30:1200,EVENT_FLAGS=bxxx1x000]' eventsout=" + datasetdir + "/xti/analysis/ni" + obsID + "_0mpu7_cl_underonly" + underonly_num + "_overonly" + overonly_num+ ".evt timefile=" + datasetdir + "/auxil/ni" + obsID + ".mkf_gti1 gti=GTI chatter=5"
    niextract_choice = input('Run niextract? [yes]')
    print(niextract)
    if niextract_choice == '':
        niextract_choice = 'yes'
    if niextract_choice == 'yes': 
        subprocess.run(niextract, shell = True)


if __name__ == "__main__":
    main()      
    # test()


