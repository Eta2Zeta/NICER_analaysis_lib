# Hongyu Zhang 04/13/2024
# Python code to use stingray to plot joint pulse profiles - Her X-1
# Modified to standardize as the plotting of pulse profile
# This file is used by placing it at the "analysis" directory where the nicer_xti_ev_calib.nc file is 
# already created and ready to be copied
# TODO: I guess I can auto detect all the nicer_xti_ev_calib.nc files in the directory 

import matplotlib.pyplot as plt
import numpy as np
from hendrics.io import load_events
from stingray.pulse.pulsar import fold_events
import re

#Set parameters
#spin frequency from the plotfdotvf.py script
fr = #TODO
#spin frequency dot from the plotfdotvf.py script
frdot =	#TODO
#desired number of bins
pbin = 128							        
tstart = #TODO

# Input the file name
filename = input('Input of the nicer_xti_ev_calib.nc file: ')

# Load NICER events
nicer_events_1 = load_events(filename)

# Extract observation ID and GTI label from filename
obs_id_match = re.search(r"ni(\d{10})", filename)
observation_id = obs_id_match.group(1) if obs_id_match else "unknown"

gti_match = re.search(r"(GTI\d?)", filename)
gti_label = gti_match.group(1) if gti_match else ""

# Fold the data
ni_ph_1, ni_profile_1, ni_profile_err_1 = fold_events(nicer_events_1.time, fr, frdot, ref_time=tstart, nbin=pbin)

# Normalize the pulse profile
mean_rate = np.mean(ni_profile_1)
ni_profile_1 /= mean_rate
ni_profile_err_1 /= mean_rate

# Find the index of the phase with the lowest count
min_index = np.argmin(ni_profile_1)
# Calculate shift to align this min phase to 0.1
shift = (pbin // 10) - min_index

# Shift the profile and error cyclically
ni_profile_shifted = np.roll(ni_profile_1, shift)
ni_profile_err_shifted = np.roll(ni_profile_err_1, shift)

# Duplicate the shifted data to maintain continuity over two periods
ni_profile_extended = np.tile(ni_profile_shifted, 3)  # Extending to three to handle wrap-around in plotting
ni_profile_err_extended = np.tile(ni_profile_err_shifted, 3)

# Plotting
plt.figure(figsize=(10, 5))  # Increased DPI here for higher resolution
plt.errorbar(np.arange(len(ni_profile_extended)) / pbin, ni_profile_extended, ni_profile_err_extended, color='blue', drawstyle='steps-mid', label="1.4-10keV")
plt.xlabel("Phase", fontsize=16)
plt.ylabel("Normalized Count Rate (cts/s)", fontsize=16)
title_text = f"Her X-1, {observation_id} {gti_label}, Aligned to Min Phase" if gti_label else f"Her X-1, {observation_id}, Aligned to Min Phase"
plt.title(title_text, fontsize=16)
plt.legend(loc="upper right")
plt.tick_params(labelsize=16)
plt.xlim([0, 2])  # Only show two periods
plt.tight_layout(pad=0.5)
plt.show()