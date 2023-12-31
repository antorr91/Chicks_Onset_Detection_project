#Library used for our study
import numpy as np
import IPython
import pandas as pd
from scipy.io import wavfile
import soundfile as sf
import scipy, matplotlib.pyplot as plt, IPython.display as ipd
import librosa, librosa.display
#import maad
import madmom
import os
import glob
#from madmom.audio.signal import HOP_SIZE
#from madmom.features import onsets

import matplotlib.pyplot as plt
import urllib.request

from itertools import product
import io
import requests
from utils import visualize_onsets




#######################** ALGORITHMS**#############################################
###################################################################################
#
# #  Compute filtering of onset detection function
def double_onsets_correction(onsets_predicted, gt_onsets, correction= 0.020):    
    # Calculate interonsets difference
    gt_onsets = np.array(gt_onsets, dtype=float)

    # Calculate the difference between consecutive onsets
    differences = np.diff(onsets_predicted)

    # Create a list to add the filtered onset and add a first value

    filtered_onsets = [onsets_predicted[0]]  #Add the first onset

    # Subtract all the onsets which are less than fixed threshold in time
    for i, diff in enumerate(differences):
      if diff >= correction:
      # keep the onset if the difference is more than the given selected time
        filtered_onsets.append(onsets_predicted[i + 1])
        #print the number of onsets predicted after correction
    return filtered_onsets
      
############################################################################################
############################################################################################



############################################################################################
#######################°°°HIGH FREQUENCY CONTENT°°°##########################################
############################################################################################
# Define a function to run High Frequency Content algorithm for ODT
def hfc_ons_detect(gt_onsets, file_name, out_dir):
    print(f"Processing {file_name}...")
    # create variable to save onsets
    Hfc_onsets = None
    # hop length  for this madmom spectrogram representation is
    hop_length = 441
    # the sample rate for the madmom spectrigram representation is
    sr= 44100
    # Create the filtered spectrogram
    spec_mdm = madmom.audio.spectrogram.FilteredSpectrogram(file_name,num_bands=12, fmin=1800, fmax=6500, fref=2500, norm_filters=True, unique_filters=True)

    # Compute onset based on High frequency content with madmom
    hfc_ons = madmom.features.onsets.high_frequency_content(spec_mdm)
    # Applying the peak picking function to count number of onsets
    peaks = madmom.features.onsets.peak_picking(hfc_ons,threshold= 2.5, smooth=None, pre_avg=25, post_avg=25, pre_max=1, post_max=1)
    # print the number of onsets detected
    print("Number of onsets detected with HFC algorithm:", len(peaks))
    
    #adjust frames according to the High frequency content function to represent accordingly the plot
    frames = np.arange(0, len(hfc_ons))  

    # Convert in seconds my onsets
    Hfc_onsets =[(peak * hop_length / sr ) for peak in peaks ]    
    
    # Convert in float the ground truth onsets
    gt_onsets = [float(onsets) for onsets in gt_onsets]

    # Extract the time values for each frame
    seconds = frames * hop_length / sr
    #correction of the interonsets interval 
    #Hfc_onsets = double_onsets_correction(Hfc_onsets, gt_onsets, correction= 0.020)
    print("Number of onsets detected with HFC algorithm after correction:", len(Hfc_onsets))

    # Save onsets to a text file
    fname_sans_path = os.path.basename(file_name)
    output_file = os.path.join(out_dir, f"HFC_onsets_{fname_sans_path.split('.wav')[0]}.txt")
    with open(output_file, "w") as file:
        file.write("\n".join(map(lambda x: str(float(x)), Hfc_onsets))) 
    return Hfc_onsets, output_file ,hfc_ons, seconds  

############################################################################################
############################################################################################ 




############################################################################################
#######################°°°THRESHOLDED PHASE DEVIATION°°°####################################
############################################################################################
# Define a function to run Thresholded phase deviation for ODT
def tpd_ons_detect(gt_onsets,file_name, out_dir):
    #create variable to save onsets
    Tpd_onsets = None
    # hop length  for this madmom spectrogram representation is
    hop_length = 441
    # the sample rate for the madmom spectrigram representation is
    sr= 44100    

    # Create the filtered spectrogram
    spec_mdm = madmom.audio.spectrogram.FilteredSpectrogram(file_name, num_bands=64,fmin=1800, fmax=6000, fref=2500, norm_filters=True, unique_filters= True, circular_shift= True)

    # Compute phase deviation using madmom
    phase_ons_fn = madmom.features.onsets.phase_deviation(spectrogram=spec_mdm)

    # Assign the alpha value for thresholding
    alpha = 0.95
    # Apply thresholding on the phase deviation function
    phase_ons_fn[phase_ons_fn < alpha] = 0
    # Apply thresholding and peak picking  # threshold= 0.95, smooth=None, pre_avg= 0, post_avg= 0 , pre_max= 10, post_max = 10
    peaks = madmom.features.onsets.peak_picking(phase_ons_fn, threshold= 0.95, smooth=None, pre_avg= 0, post_avg= 0 , pre_max= 10, post_max = 10)

    print("Number of onsets detected with TPD algorithm:", len(peaks))
    # Compute the values for each frame
    frames= np.arange(0, len(phase_ons_fn))
    
    # Convert in float the ground truth onsets
    gt_onsets = [float(onsets) for onsets in gt_onsets]

    # Compute seconds from frames
    seconds = frames * hop_length / sr
    # Convert in seconds my onsets
    Tpd_onsets= np.array(peaks) * hop_length /sr

    # correction of the interonsets interval
    #Tpd_onsets= double_onsets_correction(Tpd_onsets, gt_onsets, correction= 0.020)
    #print("Number of onsets detected with TPD algorithm after correction:", len(Tpd_onsets))
    # Save onsets to a text file
    fname_sans_path = os.path.basename(file_name)
    output_file = os.path.join(out_dir, f"TPD_onsets_{fname_sans_path.split('.wav')[0]}.txt")
    with open(output_file, "w") as file:
        file.write("\n".join(map(str, Tpd_onsets))) 
    return Tpd_onsets, output_file, phase_ons_fn, seconds



############################################################################################
############################################################################################


############################################################################################
#######################°°°NORMALISED WEIGHTED PHASE DEVIATION°°°############################
############################################################################################
# Define a function to run Normalised weighted phase deviation (NWPD) for ODT
def nwpd_ons_detect(gt_onsets, file_name, out_dir):
    
    # Create variable to save onsets
    Nwpd_onsets = None
    # hop length  for this madmom spectrogram representation is
    hop_length = 441
    # the sample rate for the madmom spectrigram representation is
    sr= 44100    

    # Create the spectrogram using madmom
    madmom_spec = madmom.audio.spectrogram.Spectrogram(file_name, circular_shift= True)

    # Compute normalized weighted phase deviation using madmom
    nwpd_ons_fn = madmom.features.onsets.normalized_weighted_phase_deviation(madmom_spec, epsilon=2.220446049250313e-16)

    # Applying the peak picking function to count number of onsets # threshold= 0.92, smooth=None, pre_avg=0, post_avg=0, pre_max=30, post_max=30
    peaks = madmom.features.onsets.peak_picking(nwpd_ons_fn, threshold=0.92, smooth=None, pre_avg=0, post_avg=0, pre_max=30, post_max=30)
    

    # Compute the values for each frame
    frames = np.arange(0, len(nwpd_ons_fn))
    # import the ground truth onsets
    
    # Convert in float the ground truth onsets
    gt_onsets = [float(onsets) for onsets in gt_onsets]

    # Plot the high-frequency content
    seconds = frames * hop_length / sr
    

    # Convert in seconds my onsets
    Nwpd_onsets= peaks * hop_length /sr
    
    print("Number of onsets detected with NWPD algorithm:", len(Nwpd_onsets))
    # correction of the interonsets interval
    #Nwpd_onsets = double_onsets_correction(Nwpd_onsets, gt_onsets, correction= 0.020)
    #print("Number of onsets detected with NWPD algorithm after correction:", len(Nwpd_onsets))

    # Save onsets to a text file
    fname_sans_path = os.path.basename(file_name)
    output_file = os.path.join(out_dir, f"NWPD_onsets_{fname_sans_path.split('.wav')[0]}.txt")
    with open(output_file, "w") as file:
        file.write("\n".join(map(str, Nwpd_onsets)))
    print(f"The file has been saved in the output folder{out_dir} as {output_file}")     
    return Nwpd_onsets, output_file, nwpd_ons_fn, seconds
            
############################################################################################
############################################################################################



############################################################################################
#######################°°°RECTIFIED COMPLEX DOMAIN°°°#######################################
############################################################################################
# Define a function to run Rectified complex domain (RCD) for ODT
def rcd_ons_detect(gt_onsets,file_name, out_dir):
    # Create variable to save onsets
    Rcd_onsets = None
    # hop length  for this madmom spectrogram representation is
    hop_length = 441
    # the sample rate for the madmom spectrigram representation is
    sr= 44100    

    # Create the spectrogram using madmom
    madmom_spec = madmom.audio.spectrogram.Spectrogram(file_name, circular_shift= True)

    # Compute rectified complex domain onsets using madmom
    rcd_ons_fn = madmom.features.onsets.rectified_complex_domain(madmom_spec, diff_frames=None)

    # Applying the peak picking function with the current parameter values  thr= 50, smooth= None, pre_avg=25, post_avg=25, pre_max=10, post_max=10
    peaks = madmom.features.onsets.peak_picking(rcd_ons_fn, threshold= 50, smooth= None, pre_avg=25, post_avg=25, pre_max=10, post_max=10)
    # Compute the values for each frame
    frames= np.arange(0, len(rcd_ons_fn))
    # Convert in float the ground truth onsets
    gt_onsets = [float(onsets) for onsets in gt_onsets]
    # Plot the high-frequency content
    seconds = frames * hop_length / sr
    # Convert in seconds my onsets
    Rcd_onsets= peaks * hop_length /sr

    print("Number of onsets detected with RCD algorithm:", len(Rcd_onsets))
    # correction of the interonsets interval
    #Rcd_onsets = double_onsets_correction(Rcd_onsets, gt_onsets, correction= 0.020)
    #print("Number of onsets detected with RCD algorithm after correction:", len(Rcd_onsets))

    # Save onsets to a text file
    fname_sans_path = os.path.basename(file_name)
    output_file = os.path.join(out_dir, f"RCD_onsets_{fname_sans_path.split('.wav')[0]}.txt")
    with open(output_file, "w") as file:
        file.write("\n".join(map(str, Rcd_onsets))) 
    print(f"The file has been saved in the output folder{out_dir} as {output_file}")    
    return Rcd_onsets, output_file, rcd_ons_fn, seconds

############################################################################################
############################################################################################




############################################################################################
#######################°°°SUPERFLUX°°°######################################################
############################################################################################
# Define a function to run the Superflux algorithm for ODT
def superflux_ons_detect(gt_onsets,file_name, out_dir):
    # create variable to save onsets
    onset_sf = None
    #Load my file
    y, sr = librosa.load(file_name)
    # Create the spectrogram
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_fft=2048 * 2, hop_length=1024 // 2, window=0.12, fmin=2050, fmax=6000, n_mels=15)
    # detect onsets through spectral flux
    odf_sf = librosa.onset.onset_strength(S=librosa.power_to_db(S, ref=np.max), sr=sr, hop_length=1024 // 2, lag=5, max_size=50)
    # detect onsets through superflux
    onset_sf = librosa.onset.onset_detect(onset_envelope=odf_sf, sr=sr, hop_length=1024 // 2, units='time')
    #set hop length for conversion in seconds
    hop_length=1024 // 2
    # Compute the frames for the onset function
    frames = np.arange(0, len(odf_sf))
    # Calculate the time values for each frame
    seconds = frames * hop_length / sr

    # import the ground truth onsets
    # gt_onsets = [onset for onset in gt_onsets if onset.replace('.', '', 1).isdigit()]
    # Convert in float the ground truth onsets
    gt_onsets = [float(onsets) for onsets in gt_onsets]

    # Convert onset times from seconds to frame indices
    onset_frames = np.asarray(onset_sf * sr / hop_length) # Superflux in librosa gives onsets in seconds
    # print the number of onsets detected
    print("Number of onsets detected with Superflux algorithm:", len(onset_sf))
    # correction of the interonsets interval
    #onset_sf = double_onsets_correction(onset_sf, gt_onsets, correction= 0.020)
    print("Number of onsets detected with Superflux algorithm after correction:", len(onset_sf))

    # Save onsets to a text file
    fname_sans_path = os.path.basename(file_name)
    output_file = os.path.join(out_dir, f"Superflux_onsets_{fname_sans_path.split('.wav')[0]}.txt")
    with open(output_file, "w") as file:
        file.write("\n".join(map(str, onset_sf))) 
    print(f"The file has been saved in the output folder{out_dir} as {output_file}")    
    return onset_sf, output_file, odf_sf, seconds 
  
############################################################################################
############################################################################################



############################################################################################
#######################°°°DOUBLE THRESHOLD FUNCTION°°°######################################
############################################################################################
# double threshold approach to identify chicks' calls onsets
def double_thr_ons_detect(gt_onsets, file_name, out_dir):

  # hop length  for this madmom spectrogram representation is
  hop_length = 441
  # the sample rate for the madmom spectrigram representation is
  sr= 44100    
    # Create variable to save onsets 
  onset_times= None
  # Compute the STFT of the audio signal
  x, sr= librosa.load(file_name, sr=sr)
  #set the number of FFT bins
  n_fft = 2048
    #set the hop length
  hop_length = 440
  # Compute the spectrogram magnitude
  spectrogram = np.abs(librosa.stft(x, n_fft=n_fft, hop_length=hop_length))
  # Frequency range of interest (2 kHz to 5 kHz)
  freq_bins = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
  #set the low frequency bin
  low_freq_bin = np.argmax(freq_bins >= 2000)
  #set the high frequency bin
  high_freq_bin = np.argmax(freq_bins >= 5800)

  # set the low threshold
  low_threshold = 100
  #set the high threshold
  high_threshold = 200

  # Initialize arrays to store onset times
  onset_times = []
   # for each time frame
  for t in range(spectrogram.shape[1]-1):
      # for each frequency bin
      for f in range(low_freq_bin, high_freq_bin):
          # if the value is higher than the threshold frequency value
          if f < spectrogram.shape[0]:
              # if the value is higher than the threshold frequency value OR if the value is higher than the threshold frequency value & 
              # the value is higher than the previous and the next value
              if (spectrogram[f, t] > high_threshold) | (spectrogram[f, t] > low_threshold and
                                                          (spectrogram[f, t] > spectrogram[f , t -1]) and
                                                          (spectrogram[f, t] > spectrogram[f , t +1])):

                # Convert time frame index to seconds
                onset_time = librosa.frames_to_time(t, sr=sr, hop_length=hop_length)
                # Append the time to the array of onsets
                onset_times.append(onset_time)
    
  # Convert in float the ground truth onsets
  gt_onsets = [float(onsets) for onsets in gt_onsets]
  # Print the number of onsets detected      
  print("Number of onset detected with DTOs:", len(onset_times))
  # Calculate the time values for each frame
  frames = np.arange(0, len(onset_times))
  # Extract the time values for each frame
  seconds = frames * hop_length / sr
  assert len(onset_times) == len(seconds)
  # correction of the interonsets interval
  #onset_times = double_onsets_correction(onset_times, gt_onsets, correction= 0.020)
  #print("Number of onsets detected with Double threshold algorithm after correction:", len(onset_times))
    
  # Save onsets to a text file
  fname_sans_path = os.path.basename(file_name)
  output_file = os.path.join(out_dir, f"Double_thr_onsets_{fname_sans_path.split('.wav')[0]}.txt")
  with open(output_file, "w") as file:
      file.write("\n".join(map(str, onset_times))) 
  return onset_times, output_file, seconds, spectrogram

############################################################################################
############################################################################################