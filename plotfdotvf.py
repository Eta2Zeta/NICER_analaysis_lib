#Hongyu Zhang 04/13/2024
#Python script to run folding search over frequency and frequency dot
#for Her X-1 stray light data

#first import everything
######################################
import pickle
import matplotlib.pyplot as plt
import re

import numpy as np

from hendrics.io import load_events

from hendrics.efsearch import folding_search, z_n_search
from hendrics.efsearch import z_n_search
#########################################

# User input filename:
filename = input('Input the event_nicer_xti_ev_calib.nc file: ')

#Load in both NuSTAR event files
events = load_events(filename)

#do folding search. Scale the f and fdot range to focus in on your area of interest
results = folding_search(events, 0.805, 0.81, step=None, func=z_n_search, oversample=10, fdotmin=-5e-7, fdotmax=5e-7)

# Use a regular expression to find the observation ID
match = re.search(r"ni(\d{10})", filename)

# Check if a match was found and extract the observation ID
if match:
    observation_id = match.group(1)
    print("Observation ID:", observation_id)
else:
    print("No observation ID found in the filename.")

#assign results to variables
ff,fd,stats,step,fdotsteps,length = results
print("Done")

#print the maximum Z statistic for F and Fdot
indexfmax=np.where(stats == np.amax(stats))
print("Best f:", ff[indexfmax] )
print("Best fdot:", fd[indexfmax] )

#Save the output of the folding search to separate data files. This is useful if you plan to do the 2-D Gaussian
#fit for errors, but don't want to rerun the time consuming folding search over and over. Here I saved using the
#pickle file format 
with open('foldingsearch_ff.data', 'wb') as fp:
 	pickle.dump(ff,fp)
# 	
with open('foldingsearch_fd.data', 'wb') as fp1:
 	pickle.dump(fd,fp1)
# 	
with open('foldingsearch_stats.data', 'wb') as fp2:
 	pickle.dump(stats,fp2)

#plot fdot vs f
plt.figure()
plt.pcolormesh(ff,fd,stats)
plt.xlabel("Frequency (Hz)",fontsize=18)
plt.ylabel("Frequency dot",fontsize=18)
plt.title(f"{observation_id}, 0.3-12 keV")
plt.colorbar()
plt.tight_layout(pad=0.5)
plt.savefig("fdotvf.pdf")
plt.show()