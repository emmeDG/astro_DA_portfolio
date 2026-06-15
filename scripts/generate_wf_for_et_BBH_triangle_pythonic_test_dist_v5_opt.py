# Main code to generate signals, noise and calculating the SNR over the signals injected in noise
# generate_wf_for_et_BBH_triangle_pythonic_test_dist.py
# Version 4.0
# Main code to generate signals, noise and calculating the SNR over the signals injected in noise

##### © MATTEO DI GIOVANNI 2024
##### MATTEO.DIGIOVANNI@UNIROMA1.IT
##### LA SAPIENZA UNIVERSITA' DI ROMA

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


# HERE WE DEFINE THE FUNCTIONS THAT WILL BE USED LATER IN THE SCRIPT

def print_program_info():
    
    # Display program banner and metadata.

    # Prints an ASCII-art header together with program information such as
    # author, version, release date, license and copyright notice.

    # This function is intended for command-line execution and provides
    # a visual summary of the software before the analysis starts.

    # Returns
    # -------
    # None
    
    print('\n\n')
    BLUE = "\033[34m"
    RESET = "\033[0m"  
    
    ascii_et = [
        "            ███████╗████████╗",
        "            ██╔════╝╚══██╔══╝",
        "            █████╗     ██║   ",
        "            ██╔══╝     ██║   ",
        "            ███████╗   ██║   ",
        "            ╚══════╝   ╚═╝   "
    ]
    
    ascii_spb = [
        
        "███████╗███████╗ ██████╗ ",
        "██╔════╝██╔═══██╗██╔══██╗",
        "███████╗███████╔╝██████╔╝",
        "╚════██║██╔═══╝  ██╔══██╗",
        "███████║██║      ██████╔╝",
        "╚══════╝╚═╝      ╚═════╝ "
    ]
    
    L_1 = [
        
         "#       ###########", 
         "#                 #", 
         "#                 #", 
         "#                 #", 
         "#                 #", 
         "#                 #", 
         "##########        #" 
    ]
    
    art = r"""
     _   _       _           _____           _ _               
    | \ | |     (_)         |_   _|         | | |              
    |  \| | ___  _ ___  ___   | | ___   ___ | | |__   _____  __
    | . ` |/ _ \| / __|/ _ \  | |/ _ \ / _ \| | '_ \ / _ \ \/ /
    | |\  | (_) | \__ \  __/  | | (_) | (_) | | |_) | (_) >  < 
    |_| \_|\___/|_|___/\___|  |_|\___/ \___/|_|_.__/ \___/_/\_\
    """
    
    
    spacing = "   "

    for left, right in zip(ascii_et, ascii_spb):
        print(BLUE + left + spacing + right + RESET)

    print()
    print(art)
    
    title = "\n           generate_wf_for_et_BBH_triangle_pythonic_test_dist_v5_opt.py\n"
    
    info = {
        "Author": "Matteo Di Giovanni",
        "Version": "1.5.0",
        "Date": "2026-03-11",
        "License": "GNU General Public License",
        "Copyright": "© 2025,2026 Matteo Di Giovanni"
    }

    # Costruisci le righe "chiave: valore"
    lines = [f"{k}: {v}" for k, v in info.items()]

    # Calcolo larghezza massima per riquadro
    max_len = max(len(line) for line in lines)
    inner_width = max_len + 4  # padding laterale
    box_width = inner_width + 2  # include i due bordi '#'

    # Stampa titolo centrato
    print(title.center(box_width))
    
    # Bordo superiore
    print("            "+"#" * box_width)

    # Righe centrate
    for line in lines:
        padding_total = max_len - len(line)
        left_pad = padding_total // 2
        right_pad = padding_total - left_pad
        print(f"            #{' ' * (left_pad + 2)}{line}{' ' * (right_pad + 2)}#")

    # Bordo inferiore
    print("            "+"#" * box_width)
    print()

def progress_bar(iteration: int, total: int, prefix: str = '', ETA: float = 0, decimals: int = 1, length: int = 100, fill: str = '█') -> None:
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ('{0:.' + str(decimals) + 'f}').format(100 * (iteration / float(total)))
    suffix  = ('ETA {0:.' + str(decimals) + 'f} hours').format(ETA)
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    line = f"{prefix} |{bar}| {percent}% {suffix}"
    sys.stdout.write('\r\033[K')
    sys.stdout.write(line)
    sys.stdout.flush()

def azimuth(lat1,lon1,lat2,lon2):

    # Compute the azimuth between two geographical coordinates.

    #The azimuth is measured clockwise from geographic North and is
    #used to determine interferometer arm orientations from detector
    #vertex coordinates.

    #Parameters
    #----------
    #lat1 : float
    #    Latitude of the starting point in degrees.
    #lon1 : float
    #    Longitude of the starting point in degrees.
    #lat2 : float
    #    Latitude of the destination point in degrees.
    #lon2 : float
    #    Longitude of the destination point in degrees.

    #Returns
    #-------
    #float
    #    Azimuth angle in degrees in the range [0, 360).

    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)

    dlon = lon2 - lon1

    x = np.sin(dlon) * np.cos(lat2)
    y = (np.cos(lat1) * np.sin(lat2) -
    np.sin(lat1) * np.cos(lat2) * np.cos(dlon))

    az = np.degrees(np.arctan2(x, y))
    az = (az + 360)

    return az

def noise_from_sqrt_psd(old_freq, sqrt_psd, fs, dur, seed):    #dur=sample   sample=fs*dur
    

    #Generate stationary Gaussian colored noise from a target ASD.

    #White Gaussian noise is generated in the frequency domain and
    #subsequently shaped using the provided amplitude spectral density
    #(ASD). The resulting noise is transformed back into the time domain.

    #Parameters
    #----------
    #old_freq : ndarray
    #    Frequency array associated with the input ASD.
    #sqrt_psd : ndarray
    #    Amplitude spectral density values.
    #fs : int
    #    Sampling frequency in Hz.
    #dur : int
    #    Duration of the generated noise in seconds.
    #seed : int
    #    Seed used to initialize the random number generator.

    #Returns
    #-------
    #ndarray
    #    Time-domain colored noise realization.


    frequencies = np.linspace(0, fs // 2, dur * fs // 2 + 1)

    norm = 0.5 * dur ** 0.5

    # Fourier-amplitudes of white noise
    _rng_state = np.random.RandomState(seed=seed)
    re = _rng_state.normal(0, norm, len(frequencies))
    im = _rng_state.normal(0, norm, len(frequencies))
    wtilde = re + 1j * im

    rpsd = np.interp(frequencies, old_freq, sqrt_psd, left=0, right=0)

    ctilde = wtilde * rpsd

    # set DC = 0
    ctilde[0] = 0
    # print(frequencies)
    time_series = np.fft.irfft(ctilde) * fs

    return time_series
    
def read_txt(filename):
    

    #Read a two-column text file.

    #The function is primarily used to load detector sensitivity curves,
    #where the first column contains frequency values and the second
    #column contains ASD values.

    #Parameters
    #----------
    #filename : str
    #    Path to the text file.

    #Returns
    #-------
    #tuple of ndarray
    #    Tuple containing:

    #    - frequency array
    #    - data array

    
    with open(filename) as inf:
        reader = csv.reader(inf, delimiter=" ")
        col_1 = list(zip(*reader))[0]
    col_1 = np.asarray(col_1, dtype=np.float32)
    
    with open(filename) as inf:
        reader = csv.reader(inf, delimiter=" ")
        col_2 = list(zip(*reader))[1]
    col_2 = np.asarray(col_2, dtype=np.float32)

    return col_1, col_2

def wf_timeseries(gps_start, quad, time, fs):
        

    #Convert waveform data into a GWPy TimeSeries object.

    #The waveform is tapered to reduce edge effects and assigned
    #the requested GPS start time.

    #Parameters
    #----------
    #gps_start : float
    #    GPS start time of the waveform.
    #quad : array_like
    #    Waveform strain samples.
    #time : array_like
    #    Time vector associated with the waveform.
    #fs : int
    #    Sampling frequency in Hz.

    #Returns
    #-------
    #gwpy.timeseries.TimeSeries
    #    Tapered waveform time series.


    signal_ts    = TimeSeries(quad, sample_rate = fs, t0 = gps_start, times = time)
    #signal_ts    = signal_ts.resample(rate = 4096) # Sampling rate of waveform and noise must be the same
    signal_ts    = signal_ts.taper()
    signal_ts.t0 = gps_start

    return signal_ts

def welch_method(time_strain, fs, seg_len_secs):
    
    #Estimate the power spectral density using Welch's method.

    #Computes one-sided and two-sided PSD estimates together with the
    #corresponding amplitude spectral densities (ASDs).

    #Parameters
    #----------
    #time_strain : array_like
    #    Input strain time series.
    #fs : int
    #    Sampling frequency in Hz.
    #seg_len_secs : float
    #    Segment length used for Welch averaging, expressed in seconds.

    #Returns
    #-------
    #tuple
    #    Contains:

    #    - one-sided frequency array
    #    - one-sided ASD
    #    - two-sided frequency array
    #    - two-sided ASD

    
    dt              = 1/fs                   # dt time interval
    N               = len(time_strain)       # dur*fs
    #seg_len_secs    = 600                    # [s] divido in slot di 128s
    seg_len_samps   = int(seg_len_secs//dt)  # [sample] dei segmenti da 128s
    taperWindow     = np.hanning(seg_len_samps)

    fq1, Pxx_spec1 = scipy.signal.welch(time_strain, fs=fs, window=taperWindow, nperseg= seg_len_samps, scaling = 'density', return_onesided = True)
    fq2, Pxx_spec2 = scipy.signal.welch(time_strain, fs=fs, window=taperWindow, nperseg= seg_len_samps, scaling = 'density', return_onesided = False)
    
    #print(Pxx_spec1)
    
    asd1           = np.sqrt(Pxx_spec1)
    asd2           = np.sqrt(Pxx_spec2)
    
    
    return fq1, asd1, fq2, asd2

def inject(ts, gps_start, filename, time, fs):
    

    #Inject a gravitational-wave signal into a noise realization.

    #Parameters
    #----------
    #ts : array_like
    #    Noise time series.
    #gps_start : float
    #    GPS start time of the noise segment.
    #filename : pycbc.types.TimeSeries
    #    Signal waveform to be injected.
    #time : array_like
    #    Time samples associated with the waveform.
    #fs : int
    #    Sampling frequency in Hz.

    #Returns
    #-------
    #gwpy.timeseries.TimeSeries
    #    Noise plus injected signal.

    
    signal_ts = wf_timeseries(filename.start_time, filename, time, fs)
    ts        = TimeSeries(ts, t0 = gps_start, sample_rate = fs)
    data      = ts.inject(signal_ts)  ## <------------- INJECT SIGNAL IN SIMULATED NOISE
    
    return data
    
def unifom_dist(N, xmin, xmax):  # generate uniform distribution

    #Generate samples from a uniform distribution.

    #Parameters
    #----------
    #N : int
    #    Number of samples to generate.
    #xmin : float
    #    Lower bound of the distribution.
    #xmax : float
    #    Upper bound of the distribution.

    #Returns
    #-------
    #list of float
    #    Uniformly distributed random values.

    
    distr_gps_times = []
    for _ in range(N):
        x = random.uniform(xmin, xmax)
        distr_gps_times.append(x)
    return distr_gps_times

def normalize_to_01(vector):   

    #Normalize an array to the interval [0, 1].

    #Parameters
    #----------
    #vector : ndarray
    #    Input array.

    #Returns
    #-------
    #ndarray
    #    Normalized array with minimum value 0 and maximum value 1.

    min_val = np.min(vector)
    max_val = np.max(vector)
    normalized_vector = (vector - min_val) / (max_val - min_val)
    return normalized_vector

class BBH:

        #Configuration container for Binary Black Hole analyses.

        #Attributes
        #----------
        #catalogName : str
        #    Path to the BBH population catalog.
        #apx : str
        #    Waveform approximant used for signal generation.
        #fs : int
        #    Sampling frequency in Hz.
        #f_lower : float
        #    Lower frequency cutoff for waveform generation.

        def __init__(self):
            self.catalogName = '../catalogs/18321_1yrCatalogBBH.h5'   #BBH
            self.apx         = 'IMRPhenomD' #'IMRPhenomD' 'IMRPhenomPv2_NRTidalv2'
            self.fs          = 4096
            self.f_lower     = 1
            
class BNS:
    
        #Configuration container for Binary Neutron Star analyses.

        #Attributes
        #----------
        #catalogName : str
        #    Path to the BNS population catalog.
        #apx : str
        #    Waveform approximant used for signal generation.
        #fs : int
        #    Sampling frequency in Hz.
        #f_lower : float
        #   Lower frequency cutoff for waveform generation.

        def __init__(self):
            self.catalogName = '../catalogs/18321_1yrCatalogBNS.h5'   #BBH
            self.apx         = 'IMRPhenomPv2_NRTidalv2' #'IMRPhenomD' 'IMRPhenomPv2_NRTidalv2'
            self.fs          = 64
            self.f_lower     = 2
    
registry = {
        "BBH": (BBH()),
        "BNS": (BNS())
    }


import time
import sys
import warnings
import numpy as np
import csv
import scipy
import h5py
import random
import matplotlib.pyplot as plt
import pickle
import argparse
from pycbc.detector import add_detector_on_earth
from pycbc.waveform import get_td_waveform, get_fd_waveform
from pycbc.detector import Detector
from lal import LIGOTimeGPS
from gwpy.timeseries import TimeSeries
from gwpy.frequencyseries import FrequencySeries
from pycbc.pnutils import get_inspiral_tf
from pycbc.filter import matched_filter
from pycbc.psd import interpolate, inverse_spectrum_truncation
from astropy.units import Quantity
from datetime import datetime
from gwpy.time import from_gps
from pycbc import waveform
from pycbc.conversions import tau3_from_mass1_mass2, tau0_from_mchirp, mass1_from_mchirp_q, mchirp_from_mass1_mass2
from scipy.signal import savgol_filter
from pycbc.filter import sigma
from gwpy.time import tconvert, to_gps
warnings.filterwarnings("ignore")

if __name__=="__main__":

    print_program_info()
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-case',help='candidate sites: SOS or TERZ (type str)',action='store',type=str)
    parser.add_argument('-config',help='detector configuration: TRIANGLE or 2L (type str)',action='store',type=str)
    parser.add_argument('-source_type',help='source type of the analysis: BBH or BNS (type str)',action='store',type=str)
    parser.add_argument('-plots',help='True or False - default = False (type bool)',action='store',type=bool)
    args = parser.parse_args()
    
    if args.plots == None:
        
            args.plots = False
            
    case           = args.case                    # SOS, TERZ
    config         = args.config                  # TRIANGLE, 2L
    source_type    = args.source_type
    plots          = args.plots
    cumulative     = False
    f_cut          = 10
    f_start        = 2
    net            = 0
    index          = 0
    
    del args
    
    if case == 'TERZ' and config == 'TRIANGLE': 
        file_list       = ['../sens_curves/ET_ALL_NB.txt', '../sens_curves/ET_TERZ_10th_perc_1year.txt', '../sens_curves/ET_TERZ_50th_perc_1year.txt', '../sens_curves/ET_TERZ_90th_perc_1year.txt']
        coords   = [[5.9342,50.6575], [5.9055,50.7533], [5.78714,50.69021]] #LON,LAT in degrees V1,V2,V3 #DELTA
        orient   = [[azimuth(coords[0][1],coords[0][0],coords[2][1],coords[2][0]),azimuth(coords[0][1],coords[0][0],coords[1][1],coords[1][0])],
                                [azimuth(coords[0][1],coords[0][0],coords[1][1],coords[1][0]),azimuth(coords[2][1],coords[2][0],coords[1][1],coords[1][0])],
                                [azimuth(coords[0][1],coords[0][0],coords[2][1],coords[2][0]),azimuth(coords[1][1],coords[1][0],coords[2][1],coords[2][0])]]
        alt      = 0
        armlegth = 10000 
        IFOs     = ['ET1', 'ET2', 'ET3']
        nIFOs    = 3
        
        print(' * Analyzing the triangle configuration for the EMR site.')
        
    elif case == 'SOS' and config == 'TRIANGLE': 
        file_list      = ['../sens_curves/ET_ALL_NB.txt', '../sens_curves/ET_P2_10th_perc_1year.txt', '../sens_curves/ET_P2_50th_perc_1year.txt', '../sens_curves/ET_P2_90th_perc_1year.txt']

        #file_list      = ['../sens_curves/ET_ALL_NB.txt', '../sens_curves/ET_P2_95th_perc_dec.txt', '../sens_curves/ET_P2_5th_perc_jul.txt']
        
        coords   = [[9.44896,40.472806], [9.329494,40.441343], [9.353505,40.53611]] #LON,LAT in degrees V1,V2,V3 #DELTA
        orient   = [[azimuth(coords[0][1],coords[0][0],coords[2][1],coords[2][0]),azimuth(coords[0][1],coords[0][0],coords[1][1],coords[1][0])],
                                [azimuth(coords[0][1],coords[0][0],coords[1][1],coords[1][0]),azimuth(coords[2][1],coords[2][0],coords[1][1],coords[1][0])],
                                [azimuth(coords[0][1],coords[0][0],coords[2][1],coords[2][0]),azimuth(coords[1][1],coords[1][0],coords[2][1],coords[2][0])]]
        alt = 250
        armlegth = 10000 
        IFOs     = ['ET1', 'ET2', 'ET3']
        nIFOs    = 3
        
        print(' * Analyzing the triangle configuration for the Sardinia site.')

    if config == '2L': 
        file_list      = ['../sens_curves/2L_sample_sensitivity.txt', '../sens_curves/ET_SAR_10th_perc_2022-2025_2L.txt', '../sens_curves/ET_SAR_50th_perc_2022-2025_2L.txt', '../sens_curves/ET_SAR_90th_perc_2022-2025_2L.txt','../sens_curves/2L_sample_sensitivity.txt', '../sens_curves/ET_DZA_10th_perc_2022-2025_2L.txt', '../sens_curves/ET_DZA_50th_perc_2022-2025_2L.txt', '../sens_curves/ET_DZA_90th_perc_2022-2025_2L.txt']
        case = '2LNET'
        IFOs     = ['ET1', 'ET2']
        armlegth = 15000
        nIFOs    = 2
        old = file_list
        file_list = file_list[0:4]
        print(' * Analyzing the 2L configuration.')
    
    # BNS SIGNALS ARE LONG SIGNALS.
    # TO ACHIEVE THE GENERATION OF A WAVEFORM, WE GENERATE IT SAMPLED AT 256 HZ
    # THIS MEANS THE F_MAX OF THE SIGNAL IS 128 HZ AND DOES NOT INCLUDE MERGER
    # WE ARE NOT INTERESTED IN THAT PART OF THE SIGNAL ANYWAY.

    source = registry[source_type]        
    events_tmp={}
    events = {}
    
    with h5py.File(source.catalogName, 'r') as f:
        for key in f.keys():
            events_tmp[key] = np.array(f[key])
    
    # THE EVENTS' TIMES IN THE CATALOGS ARE BUGGED
    # HERE WE CORRECTLY SAMPLE THEM RANDOMLY BETWEEN 01-01-2030 AND 01-01-2031
            
    N = len(events_tmp['tGPS'])  # Numerber of values to generate
    gps_min = int(to_gps('Jan 01 2030 00:00:00.000'))
    gps_max = int(to_gps('Jan 01 2031 00:00:00.000'))
    
    distr_gps_times = unifom_dist(N, gps_min, gps_max)
    events_tmp['tGPS']  = np.array(distr_gps_times)        # new GPS times in 1yr
    events_tmp['tcoal'] = normalize_to_01(events_tmp['tGPS'])
    
    # SINCE WE CANNOT PROCESS ALL THE BNS EVENTS
    # WE RANDOMLY SELECT SOME OF THEM
    # PRIVILEGING LOW Z EVENTS
    # BBH ARE SAMPLED BY JUST IMPOSING CUTS ON THE MASS RANGE OF INTEREST
    
    if source_type == 'BNS':
    
        idx_z_incl = np.where((events_tmp['z'] <= 1.5) & (events_tmp['z'] > 0.25))[0]
        idxs_rdn   = random.sample(list(enumerate(events_tmp['z'][idx_z_incl])), 1500)
        idx_tot    = np.append(np.where(events_tmp['z'] <= 0.25)[0],np.array(idxs_rdn, dtype = 'int')[:,0])
        
    elif source_type == 'BBH':
        
        idx_tot = np.append(np.where((events_tmp['m1_source'] >= 100) & (events_tmp['m2_source'] < 100))[0],np.where((events_tmp['m2_source'] >= 100) & (events_tmp['m1_source'] < 100))[0])
        idx_tot = np.append(idx_tot,np.where((events_tmp['m1_source'] + events_tmp['m2_source'] >= 100))[0])
        idx_tot = np.append(idx_tot,np.where((events_tmp['m1_source'] >= 100) & (events_tmp['m2_source'] >= 100))[0])
        
    fields_to_load = [
            'tGPS', 'tcoal', 'dec', 'ra', 'psi',
            'm1_source', 'm2_source', 'z',
            'chi1z', 'chi2z', 'iota', 'dL'
        ]
    
    for key in fields_to_load:
            events[key] = np.array(events_tmp[key][idx_tot])
        
    del events_tmp 

    results = {}
    for key in file_list:
        results[key] = np.zeros(len(idx_tot))
    
    tic = time.time()

    time_to_merge  = np.zeros(len(idx_tot))
    time_to_m_SNR  = np.zeros(len(idx_tot))
    time_tot       = np.zeros(len(idx_tot))

    print(' * Analyzing '+str(len(idx_tot))+' events.')

    ra, dec = np.meshgrid(np.arange(0, np.pi*2.0, .1),
                                  np.arange(-np.pi / 2.0, np.pi / 2.0, .1))
    ra = ra.flatten()
    dec = dec.flatten()
    
    det_ET1        = [None] * nIFOs #np.zeros(nIFOs)
    
    if config == 'TRIANGLE':

            # DEFINE FICTIOUS ET DETECTOR. I.E. THREE CO-LOCATED DETECTORS WITH DIFFERENT ORIENTATIONS (YANGLE AND XANGLE)
        for i, det in enumerate(IFOs):
                        #print(orient[i][1])

            add_detector_on_earth(name = det, longitude = np.pi/180*coords[i][0], latitude = np.pi/180*coords[i][1], height = alt, xlength=armlegth, ylength = armlegth, yangle = orient[i][0], xangle = orient[i][1])
            det_ET1[i] = Detector(det)
                    
    elif config == '2L':
        
        #SARDINIA
        
        add_detector_on_earth(name = IFOs[0], longitude = np.pi/180*9.448983, latitude = np.pi/180*40.472788, height = 250, xlength=armlegth, ylength = armlegth, yangle = azimuth(40.472788,9.448983,40.44821,9.273396), xangle = azimuth(40.472788,9.448983,40.607196,9.416704))
        det_ET1[0] = Detector('ET1')

        # EMR
        
        # add_detector_on_earth(name = IFOs[1], longitude = np.pi/180*5.917774, latitude = np.pi/180*50.759853, height = 0, xlength=armlegth, ylength = armlegth, yangle = azimuth(50.759853,5.917774,50.67793333,6.00407222), xangle = azimuth(50.759853,5.917774,50.69021,5.78714))
        #det_ET1[1] = Detector('ET2') 

        # LAUSITZ
        
        add_detector_on_earth(name = IFOs[1], longitude = np.pi/180*14.297119, latitude = np.pi/180*51.346692, height = 0, xlength=armlegth, ylength = armlegth, yangle = 125 , xangle = 125 + 90)
        
        det_ET1[1] = Detector('ET2')

    for sel,_ in enumerate(idx_tot):
        
            m=sel    
            if m == 0: 
                avgT = 0
            else: avgT = elapsed/m
        
            progress_bar(m, len(idx_tot), 'Events evaluated '+str(m)+'/'+str(len(idx_tot)), avgT*(len(idx_tot)-m)/3600, 1, 70, '█')
            
            #print(m, events['tGPS'][sel], events['z'][sel])
    
            end_time       = events['tGPS'][sel]                                  #1395411177 #1192529720
            declination    = events['dec'][sel]                                   #-20*np.pi/180#-70*np.pi/180 #0.65
            right_ascension= events['ra'][sel]                                    #15*np.pi/180#79*np.pi/180 #4.67
            polarization   = events['psi'][sel]                                   # POLARIZATION OF THE SOURCE

            if source_type == 'BNS':
            
                lambda1        = events['Lambda1'][sel]
                lambda2        = events['Lambda2'][sel]
                
            else:
                
                lambda1        = 0
                lambda2        = 0            
                
            #det_ET1        = [None] * nIFOs #np.zeros(nIFOs)
            signal_ET1     = [None] * nIFOs
            i_plot = 1
                
    
            if plots:
    
                fig, axs = plt.subplots(4, sharex=True, figsize=(20, 8))
                
    
                for i,d in enumerate(det_ET1):
                    fp, fc = d.antenna_pattern(ra, dec, polarization, end_time)
                    axs[i].remove()
                    axs[i] = fig.add_subplot(1,4,i+1, projection="mollweide")
                    ra[ra>np.pi] -= np.pi * 2.0
                    axs[i].scatter(ra, dec, c=fp**2.0 + fc**2.0)
                    axs[i].plot(right_ascension, declination, marker = '*', color = 'red')
                    axs[i].set_title(d.name)
                    axs[i].grid(True)
                    net+=fp**2.0 + fc**2.0
                
                ra[ra>np.pi] -= np.pi * 2.0
                axs[3].remove()
                axs[3] = plt.subplot(1,4,4, projection="mollweide")
                axs[3].scatter(ra, dec, c=net)
                axs[3].plot(right_ascension, declination, marker = '*', color = 'red')
                axs[3].set_title('Network antenna pattern')
                axs[3].grid(True)
                plt.tight_layout()
                plt.show()
    
            # GENERATE WAVEFORM WITH GIVEN APPROXIMANT
    
            # NOTE: Inclination runs from 0 to pi, with poles at 0 and pi
            #       coa_phase runs from 0 to 2 pi.
            
            hp, hc = get_td_waveform(approximant=source.apx,
                                     mass1      = events['m1_source'][sel]*(1 + events['z'][sel]),
                                     mass2      = events['m2_source'][sel]*(1 + events['z'][sel]),
                                     spin1z     = events['chi1z'][sel],
                                     spin2z     = events['chi2z'][sel],
                                     inclination= events['iota'][sel],
                                     lambda1    = lambda1,
                                     lambda2    = lambda2,
                                     delta_t    = 1.0/(source.fs),
                                     f_lower    = source.f_lower,
                                     distance   = events['dL'][sel]*1e3)
    
            # COMPUTE TF EVOLUTION OF SIGNAL TO GET TIME SPENT IN FREQUENCY BAND OF INTEREST
    
            hp, hc = hp.trim_zeros(), hc.trim_zeros()
            f = waveform.utils.frequency_from_polarizations(hp, hc)
            i_merger        = len(f)-1
            idx_f_cut       = np.argmin(np.abs(f[len(f)//2:i_merger] - f_cut))
            idx_f_start     = np.argmin(np.abs(f[len(f)//2:i_merger] - f_start))
            time_spent      = abs(f.sample_times[len(f)//2+idx_f_cut] - f.sample_times[len(f)//2+idx_f_start])
            time_to         = abs(f.sample_times[len(f)//2+idx_f_cut])
            time_tot[m]     = time_spent
            time_to_merge[m]= time_to
            
            
            if plots:
                plt.figure(num=i_plot)
                plt.plot(f.sample_times[len(f)//2:], f[len(f)//2:], label='TF Evolution', color = 'k')
                plt.axhspan(f_start, f_cut, alpha=0.5, color='red', label = 'Frequency region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
                plt.axvspan(float(f.sample_times[len(f)//2+idx_f_start]), float(f.sample_times[len(f)//2+idx_f_start]), alpha=0.5, color='blue', label = 'Time spent in region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
                plt.xlabel('Time [s]')
                plt.ylabel('Frequency [Hz]')
                plt.yscale('log')
                plt.legend()
                #plt.xscale('log')
                plt.show()
                i_plot+=1
                plt.show()
    
    
            hp.start_time  += end_time
            hc.start_time  += end_time
            wf_duration     = end_time - float(hp.start_time)
            time_spent      = end_time - hp.start_time
            iidx            = np.where(np.array(hp.sample_times) == end_time)
            iidx_cut        = iidx[0] - int((f.sample_times[-1] - f.sample_times[idx_f_cut])*source.fs)
            iidx_st         = iidx[0] - int((f.sample_times[-1] - f.sample_times[idx_f_start])*source.fs)
    
    
            if plots:
    
                fig, axs = plt.subplots(2, sharex=True, figsize=(8, 8))
                    
                axs[0].plot(hp.sample_times - float(hp.start_time),hp,label = 'hp polarization ' + source.apx, color = 'k')
                axs[0].axvspan(float(hp.sample_times[iidx_st]) - float(hp.start_time), float(hp.sample_times[iidx_cut]) - float(hp.start_time), alpha=0.5, color='red', label = 'Frequency region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
                axs[0].legend()
                axs[1].plot(hc.sample_times - float(hc.start_time),hc,label = 'hc polarization ' + source.apx, color = 'k')
                axs[1].axvspan(float(hp.sample_times[iidx_st]) - float(hp.start_time), float(hp.sample_times[iidx_cut]) - float(hp.start_time), alpha=0.5, color='red', label = 'Frequency region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
                axs[1].set_xlabel('Time [s]')
                axs[0].set_ylabel('Strain Amplitude')
                axs[1].set_ylabel('Strain Amplitude')
                axs[1].legend()
                plt.tight_layout()
                plt.suptitle('Time domain approximants')
                plt.show()
    

    
    
                
                # PROJECT WAVEFORM ON DETECTORS TAKING INTO ACCOUNT THE ANTENNA PATTERNS
                
    
            if plots:
    
                fig, axs = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))
    
            for i in range(len(IFOs)):
    
                signal_ET1[i] = det_ET1[i].project_wave(hp, hc,  right_ascension, declination, polarization)
    
                if i == 0:
                    idx_T_cut  = len(signal_ET1[0].sample_times)-1
                    time_spent = np.abs(signal_ET1[0].sample_times[-1] - signal_ET1[0].sample_times[0])
                if plots:
                    axs[i].plot(signal_ET1[i].sample_times - float(signal_ET1[i].start_time),signal_ET1[i],label = IFOs[i], color = 'k')
                    
                    axs[i].axvspan(float(signal_ET1[i].sample_times[iidx_st]) - float(signal_ET1[i].start_time),   float(signal_ET1[i].sample_times[iidx_cut]) -float(signal_ET1[i].start_time),     alpha=0.5, color='red', label =   'Frequencyregion of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
                    axs[i].legend()
                    axs[i].set_ylabel('Strain Amplitude')
    
                    if i == 2:
    
                        axs[i].set_xlabel('Time from ' +str(from_gps(float(signal_ET1[0].start_time))) + ' [s]')
    
                    plt.tight_layout()
                    plt.suptitle('Waveforms projected con ET detectors')
    
            if plots:
                plt.show()
    
            # GENERA RUMORE PER ET

            for fi, fl in enumerate(file_list):
    
                #print('* READING NOISE FROM: '+fl)
    
                ts_noise_ET1   = [None]*(nIFOs)
                data_ET1       = [None]*(nIFOs)
                noise_psd_ET1  = [None]*(nIFOs)
                data_to_fs_ET1 = [None]*(nIFOs)
                snrET1         = [None]*(nIFOs)
                snrtsET1       = [None]*(nIFOs)
                snrs           = []
                
    
                if config == 'TRIANGLE': freq, ETD = read_txt(fl)
                elif config == '2L':
                    ETD  = []
                    freq = []
                    freqtmp, tmp = read_txt(fl)
                    ETD.append(tmp)
                    freq.append(freqtmp)
                    freqtmp, tmp = read_txt(old[fi+4])
                    ETD.append(tmp)
                    freq.append(freqtmp)
                    
                #print('* GENERATING ET COLORED NOISE.')
                
                if events['m1_source'][sel] + events['m2_source'][sel] > 3 and time_spent > 128:
                
                    dur = int(time_spent*2)  # [s]

                elif events['m1_source'][sel] + events['m2_source'][sel] > 3 and time_spent < 128:

                    dur = 128
                    
                else:
                
                    dur = int(time_spent + 3600)
                
                for i in range(len(IFOs)):

                    if config == 'TRIANGLE': ts_noise_ET1[i] = noise_from_sqrt_psd(freq, ETD, fs=source.fs, dur=dur, seed=i + m)
                    elif config == '2L':     ts_noise_ET1[i] = noise_from_sqrt_psd(freq[i], ETD[i], fs=source.fs, dur=dur, seed=i + m)

                    #print('    '+IFOs[i]+' DONE.')
                
                if events['m1_source'][sel] + events['m2_source'][sel] > 3:
                    noise_starttime = float(signal_ET1[0].start_time) - int(time_spent/2)
                else:
                    noise_starttime = float(signal_ET1[0].start_time) - int(3600/2)
                
                noise_endtime   = noise_starttime + dur
                ts_noise_t      = np.linspace(noise_starttime,  noise_endtime, (dur*source.fs))                 # time vector
                
                #print('    Duration of noise is ' + str(dur) + ' seconds or ' + str(dur/3600) + ' hours')
                
                if plots:
                    plt.figure(num=i_plot)
                    plt.plot(ts_noise_t - noise_starttime, ts_noise_ET1[0], color = 'black')
                    plt.grid(True)
                    plt.xlabel('Time from '+str(from_gps(noise_starttime)) + ' [s]')
                    plt.ylabel('Strain Amplitude')
                    plt.title('Simulated noise')
                    plt.xlim(noise_starttime- noise_starttime,noise_endtime- noise_starttime)
                    plt.show()
                    i_plot += 1
                
                #print('* INJECTING SIGNAL INTO NOISE.')
            
                
                if plots:
                
                    fig, axs = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))
                
                for i in range(len(IFOs)):
                
                    data_ET1[i] = inject(ts_noise_ET1[i], noise_starttime, signal_ET1[i], signal_ET1[i].sample_times, source.fs)
                    #print('    '+IFOs[i]+' DONE.')
                    flago = False
                    if flago:
                        fq, asd_noise, fq2, asd_noise2  = welch_method(ts_noise_ET1[i], fs=source.fs, seg_len_secs= 64)  # seg=600
                        fqs, asd_s, fqs2, asd_2  = welch_method(signal_ET1[i], fs=source.fs, seg_len_secs= 64)
                        fqsn, asd_sn, fqsn2, asd_2n  = welch_method(data_ET1[i], fs=source.fs, seg_len_secs= 64)
                        
                        #plt.loglog(freq, ETD, color='darkorange', label='ETD')
                        plt.loglog(fq, asd_noise, color='darkgreen', alpha=0.4, label= 'ASD of simulated noise')
                        plt.loglog(np.sqrt(TimeSeries.from_pycbc(signal_ET1[i]).psd()*TimeSeries.from_pycbc(signal_ET1   [i]).psd().frequencies*(float(signal_ET1[i].end_time) - float(signal_ET1[i].start_time))),     label= 'ASD of   '+IFOs[i]+' injected signal', color = 'blue')
                        plt.loglog(np.sqrt(data_ET1[i].psd(64, overlap = 64/2, window = 'hann', method = 'welch')), label= 'ASD of noise     plus injected signal', alpha = 0.4, color = 'purple')
                        plt.legend()
                        plt.show()
                        #plt.set_xlim(1,1e3)
                        #plt.set_ylabel(r'$\frac{1}{\sqrt{Hz}}$')
                        #plt.set_ylim(1e-26,1e-16)
                        #if i == 2:
                        #    axs[2].set_xlabel('Frequency [Hz]')
                
                    data_ET1[i].highpass(1)
                    data_ET1[i].crop(5,5)
                
                if plots:
                    plt.tight_layout()
                    plt.show()
                    i_plot+=1
                
                
                if plots:
                    plt.figure(num=i_plot)
                    plt.plot((data_ET1[0].times - Quantity(noise_starttime, unit = 'second'))/60, data_ET1[0], color='gray', label='Noise +     Signal')
                    plt.plot((signal_ET1[0].sample_times - noise_starttime)/60, signal_ET1[0], color='red',  label='Injected signal')
                    plt.xlabel('Minutes from ' + str(from_gps(float(noise_starttime))))
                    plt.ylabel('Strain amplitude')
                    plt.legend()
                    plt.show()
                    i_plot +=1

                
                if plots:
                    fig, axs = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))
                    fig, axs2 = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))
                
                for i in range(len(IFOs)):

                    noise_psd_ET1[i] = TimeSeries(data_ET1[i], t0 = noise_starttime, sample_rate = source.fs, times =    ts_noise_t).psd(64,32).to_pycbc()
                    
                    data_to_fs_ET1[i] = data_ET1[i].to_pycbc().to_frequencyseries()
                    noise_psd_ET1[i] = interpolate(noise_psd_ET1[i] , data_to_fs_ET1[i].delta_f)
                    hp.resize(len(data_ET1[i]))
                
                    snrET1[i] = matched_filter(hp, data_ET1[i].to_pycbc(), psd = noise_psd_ET1[i],
                                     low_frequency_cutoff=2, high_frequency_cutoff=10)
                
                    snrtsET1[i] = TimeSeries.from_pycbc(snrET1[i]).abs()
                
                    if plots:
                
                        axs[i].plot((snrtsET1[i].times - snrtsET1[i].times[0])/60,snrtsET1[i], label = 'SNR '+IFOs[i], color = 'k')
                        axs[i].set_ylabel('SNR')
                        axs[i].legend()
                
                        white_data = (data_to_fs_ET1[i]/noise_psd_ET1[i]**0.5).to_timeseries()
                        white_data = white_data.highpass_fir(2, 512).lowpass_fir(200, 512)
                        to_plot = data_ET1[i] / sigma(data_ET1[i].to_pycbc(), psd=noise_psd_ET1[i], low_frequency_cutoff=2)
                        to_plot = (to_plot.to_pycbc().to_frequencyseries() * np.max(snrtsET1[i])).to_timeseries()
                        white_template = (to_plot.to_frequencyseries() / noise_psd_ET1[i]**0.5).to_timeseries()
                
                        axs2[i].plot(np.array(white_data.sample_times)- noise_starttime, white_data, label="Whitened data", color = 'k')
                        #axs2[i].plot(np.array(white_template.sample_times)- noise_starttime, white_template, label="Template")
                        axs2[i].set_xlim(end_time-7- noise_starttime, end_time+2- noise_starttime)
                        axs2[i].legend()
                
                        if i == 2:
                            axs[i].set_xlabel('Minutes from ' + str(from_gps(float(noise_starttime))))
                            axs2[i].set_xlabel('Seconds from ' + str(from_gps(float(noise_starttime))))
                
                if plots:
                    plt.show()
                
                if nIFOs == 3:
                    netSNR = np.sqrt(np.max(snrtsET1[0])**2+np.max(snrtsET1[1])**2+np.max(snrtsET1[2])**2)
                
                elif nIFOs == 2:
                    netSNR = np.sqrt(np.max(snrtsET1[0])**2+np.max(snrtsET1[1])**2)
                
                
                #print('    NETWORK SNR FOR SELECTED FREQUENCY BAND IS ' + str(netSNR))

                results[fl][sel] = netSNR
                    
                if cumulative:
                    #print('    CALCULATING CUMULATIVE SNR.')
                    snrs     = []
                    
                    ff   = 3
                    snrs = 0
                    
                    while ff <=10 and snrs <=12:
    
                        snrET1   = []
                        snrtsET1 = []
                    
                        for i in range(len(IFOs)):
                    
                            snrET1.append(matched_filter(hp, data_ET1[i].to_pycbc(), psd = noise_psd_ET1[i],
                                        low_frequency_cutoff=3, high_frequency_cutoff=ff))
                    
                            snrtsET1.append(TimeSeries.from_pycbc(snrET1[i]).abs())
                    
                        if nIFOs == 3:
                            snrs = (np.sqrt(np.max(snrtsET1[0])**2+np.max(snrtsET1[1])**2+np.max(snrtsET1[2])**2))
                        elif nIFOs == 2:
                            snrs = (np.sqrt(np.max(snrtsET1[0])**2+np.max(snrtsET1[1])**2))
                            
                        ff += 1
                    
                    idx_f_cum_SNR       = np.argmin(np.abs(f[len(f)//2:i_merger] - ff - 1))
                    time_to_SNR         = abs(f.sample_times[len(f)//2+idx_f_cum_SNR])
    
                    
                    if netSNR >= 12:
                    
                        time_to_m_SNR[m]= time_to_SNR
                        
                    else:
                    
                        time_to_m_SNR[m]= time_to_SNR*-1
    
            elapsed = time.time()-tic

            del netSNR, ts_noise_ET1, data_ET1, noise_psd_ET1, data_to_fs_ET1, snrET1, snrtsET1, snrs
            
            with open('../pkl/'+source_type+'_losses_'+case+'_'+source_type+'_sum_high_z_worstbest.pkl', 'wb') as file:
                pickle.dump(results, file)
        
            with open('../pkl/'+source_type+'_times_to_merge_'+case+'_'+source_type+'_sum_high_z_worstbest.pkl', 'wb') as file:
                pickle.dump(results, file)
