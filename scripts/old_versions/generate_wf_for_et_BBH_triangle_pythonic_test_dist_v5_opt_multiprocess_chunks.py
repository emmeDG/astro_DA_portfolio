# Main code to generate signals, noise and calculating the SNR over the signals injected in noise
# generate_wf_for_et_BBH_triangle_pythonic_test_dist.py
# Version 4.0

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import csv
from datetime import datetime
import multiprocessing as mp
import os
import pickle
import random
import sys
import time
import warnings

from astropy.units import Quantity
from gwpy.frequencyseries import FrequencySeries
from gwpy.time import from_gps, tconvert, to_gps
from gwpy.timeseries import TimeSeries
import h5py
from lal import LIGOTimeGPS
import matplotlib.pyplot as plt
import numpy as np
from pycbc import waveform
from pycbc.conversions import tau3_from_mass1_mass2, tau0_from_mchirp, mass1_from_mchirp_q, mchirp_from_mass1_mass2
from pycbc.detector import add_detector_on_earth, Detector
from pycbc.filter import matched_filter, sigma
from pycbc.pnutils import get_inspiral_tf
from pycbc.psd import interpolate, inverse_spectrum_truncation
from pycbc.waveform import get_td_waveform, get_fd_waveform
from scipy.signal import savgol_filter
import scipy

warnings.filterwarnings("ignore")


def print_program_info():
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

    title = "\n           generate_wf_for_et_BBH_triangle_pythonic_test_dist_v5_opt_multiprocess_chunks.py\n"

    info = {
        "Author": "Matteo Di Giovanni",
        "Version": "1.6.0",
        "Date": "2026-04-28",
        "License": "GNU General Public License",
        "Copyright": "© 2025,2026 Matteo Di Giovanni"
    }

    lines = [f"{k}: {v}" for k, v in info.items()]
    max_len = max(len(line) for line in lines)
    inner_width = max_len + 4
    box_width = inner_width + 2

    print(title.center(box_width))
    print("            " + "#" * box_width)

    for line in lines:
        padding_total = max_len - len(line)
        left_pad = padding_total // 2
        right_pad = padding_total - left_pad
        print(f"            #{' ' * (left_pad + 2)}{line}{' ' * (right_pad + 2)}#")

    print("            " + "#" * box_width)
    print()


def progress_bar(iteration: int, total: int, prefix: str = '', ETA: float = 0, decimals: int = 1, length: int = 100, fill: str = '█') -> None:
    percent = ('{0:.' + str(decimals) + 'f}').format(100 * (iteration / float(total)))
    suffix = ('ETA {0:.' + str(decimals) + 'f} hours').format(ETA)
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    line = f"{prefix} |{bar}| {percent}% {suffix}"
    sys.stdout.write('\r\033[K')
    sys.stdout.write(line)
    sys.stdout.flush()


def azimuth(lat1, lon1, lat2, lon2):
    lat1, lon1 = np.radians(lat1), np.radians(lon1)
    lat2, lon2 = np.radians(lat2), np.radians(lon2)

    dlon = lon2 - lon1
    x = np.sin(dlon) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(dlon)

    az = np.degrees(np.arctan2(x, y))
    az = az + 360

    return az


def noise_from_sqrt_psd(old_freq, sqrt_psd, fs, dur, seed):
    frequencies = np.linspace(0, fs // 2, dur * fs // 2 + 1)
    norm = 0.5 * dur ** 0.5

    _rng_state = np.random.RandomState(seed=seed)
    re = _rng_state.normal(0, norm, len(frequencies))
    im = _rng_state.normal(0, norm, len(frequencies))
    wtilde = re + 1j * im

    rpsd = np.interp(frequencies, old_freq, sqrt_psd, left=0, right=0)
    ctilde = wtilde * rpsd
    ctilde[0] = 0

    time_series = np.fft.irfft(ctilde) * fs
    return time_series


def read_txt(filename):
    with open(filename) as inf:
        reader = csv.reader(inf, delimiter=" ")
        col_1 = list(zip(*reader))[0]
    col_1 = np.asarray(col_1, dtype=np.float32)

    with open(filename) as inf:
        reader = csv.reader(inf, delimiter=" ")
        col_2 = list(zip(*reader))[1]
    col_2 = np.asarray(col_2, dtype=np.float32)

    return col_1, col_2


def wf_timeseries(gps_start, quad, time_axis, fs):
    signal_ts = TimeSeries(quad, sample_rate=fs, t0=gps_start, times=time_axis)
    signal_ts = signal_ts.taper()
    signal_ts.t0 = gps_start
    return signal_ts


def welch_method(time_strain, fs, seg_len_secs):
    dt = 1 / fs
    seg_len_samps = int(seg_len_secs // dt)
    taperWindow = np.hanning(seg_len_samps)

    fq1, Pxx_spec1 = scipy.signal.welch(time_strain, fs=fs, window=taperWindow, nperseg=seg_len_samps, scaling='density', return_onesided=True)
    fq2, Pxx_spec2 = scipy.signal.welch(time_strain, fs=fs, window=taperWindow, nperseg=seg_len_samps, scaling='density', return_onesided=False)

    asd1 = np.sqrt(Pxx_spec1)
    asd2 = np.sqrt(Pxx_spec2)

    return fq1, asd1, fq2, asd2


def inject(ts, gps_start, filename, time_axis, fs):
    signal_ts = wf_timeseries(filename.start_time, filename, time_axis, fs)
    ts = TimeSeries(ts, t0=gps_start, sample_rate=fs)
    data = ts.inject(signal_ts)
    return data


def unifom_dist(N, xmin, xmax):
    distr_gps_times = []
    for _ in range(N):
        x = random.uniform(xmin, xmax)
        distr_gps_times.append(x)
    return distr_gps_times


def normalize_to_01(vector):
    min_val = np.min(vector)
    max_val = np.max(vector)
    normalized_vector = (vector - min_val) / (max_val - min_val)
    return normalized_vector


class BBH:
    def __init__(self):
        self.catalogName = '../catalogs/18321_1yrCatalogBBH.h5'
        self.apx = 'IMRPhenomD'
        self.fs = 4096
        self.f_lower = 1


class BNS:
    def __init__(self):
        self.catalogName = '../catalogs/18321_1yrCatalogBNS.h5'
        self.apx = 'IMRPhenomPv2_NRTidalv2'
        self.fs = 64
        self.f_lower = 2


registry = {
    "BBH": BBH(),
    "BNS": BNS()
}

def take_h5_rows(dataset, idx):
    idx = np.asarray(idx, dtype=np.int64)
    unique_idx, inverse = np.unique(idx, return_inverse=True)
    ordered_values = np.asarray(dataset[unique_idx])
    return ordered_values[inverse]


def build_analysis_cases(file_list, config):
    cases = []

    if config == 'TRIANGLE':
        for fl in file_list:
            freq, etd = read_txt(fl)
            cases.append({'label': fl, 'freq': freq, 'curves': etd})
    elif config == '2L':
        half = len(file_list) // 2
        for fi in range(half):
            freq, etd_1 = read_txt(file_list[fi])
            _, etd_2 = read_txt(file_list[fi + half])
            cases.append({'label': file_list[fi], 'freq': freq, 'curves': [etd_1, etd_2]})
    else:
        raise ValueError('Unsupported config: ' + str(config))

    return cases


def create_detectors(config, IFOs, coords, orient, alt, armlegth):
    det_ET1 = [None] * len(IFOs)

    if config == 'TRIANGLE':
        for i, det in enumerate(IFOs):
            add_detector_on_earth(
                name=det,
                longitude=np.pi / 180 * coords[i][0],
                latitude=np.pi / 180 * coords[i][1],
                height=alt,
                xlength=armlegth,
                ylength=armlegth,
                yangle=orient[i][0],
                xangle=orient[i][1]
            )
            det_ET1[i] = Detector(det)
    elif config == '2L':
        add_detector_on_earth(
            name=IFOs[0],
            longitude=np.pi / 180 * 9.448983,
            latitude=np.pi / 180 * 40.472788,
            height=250,
            xlength=armlegth,
            ylength=armlegth,
            yangle=azimuth(40.472788, 9.448983, 40.44821, 9.273396),
            xangle=azimuth(40.472788, 9.448983, 40.607196, 9.416704)
        )
        det_ET1[0] = Detector('ET1')

        add_detector_on_earth(
            name=IFOs[1],
            longitude=np.pi / 180 * 5.917774,
            latitude=np.pi / 180 * 50.759853,
            height=0,
            xlength=armlegth,
            ylength=armlegth,
            yangle=azimuth(50.759853, 5.917774, 50.67793333, 6.00407222),
            xangle=azimuth(50.759853, 5.917774, 50.69021, 5.78714)
        )
        det_ET1[1] = Detector('ET2')

    return det_ET1


def process_event_chunk(payload):
    positions = np.asarray(payload['positions'], dtype=int)
    events = payload['events']
    config_data = payload['config']

    source_type = config_data['source_type']
    source_apx = config_data['source_apx']
    source_fs = config_data['source_fs']
    source_f_lower = config_data['source_f_lower']
    cumulative = config_data['cumulative']
    f_cut = config_data['f_cut']
    f_start = config_data['f_start']
    plots = config_data['plots']
    config = config_data['config']
    IFOs = config_data['IFOs']
    nIFOs = config_data['nIFOs']
    coords = config_data['coords']
    orient = config_data['orient']
    alt = config_data['alt']
    armlegth = config_data['armlegth']
    cases = config_data['cases']

    results_chunk = np.zeros((len(cases), len(positions)))
    time_to_merge_chunk = np.zeros(len(positions))
    time_to_m_SNR_chunk = np.zeros(len(positions))
    time_tot_chunk = np.zeros(len(positions))

    det_ET1 = create_detectors(config, IFOs, coords, orient, alt, armlegth)

    if plots:
        ra_grid, dec_grid = np.meshgrid(np.arange(0, np.pi * 2.0, .1), np.arange(-np.pi / 2.0, np.pi / 2.0, .1))
        ra_grid = ra_grid.flatten()
        dec_grid = dec_grid.flatten()
    else:
        ra_grid = None
        dec_grid = None

    for local_idx, global_idx in enumerate(positions):
        end_time = events['tGPS'][local_idx]
        declination = events['dec'][local_idx]
        right_ascension = events['ra'][local_idx]
        polarization = events['psi'][local_idx]
        mass1 = events['m1_source'][local_idx]
        mass2 = events['m2_source'][local_idx]
        z = events['z'][local_idx]

        if source_type == 'BNS':
            lambda1 = events['Lambda1'][local_idx]
            lambda2 = events['Lambda2'][local_idx]
        else:
            lambda1 = 0
            lambda2 = 0

        signal_ET1 = [None] * nIFOs
        i_plot = 1

        if plots:
            fig, axs = plt.subplots(4, sharex=True, figsize=(20, 8))
            ra_plot = np.array(ra_grid, copy=True)
            net = 0

            for i, d in enumerate(det_ET1):
                fp, fc = d.antenna_pattern(ra_plot, dec_grid, polarization, end_time)
                axs[i].remove()
                axs[i] = fig.add_subplot(1, 4, i + 1, projection="mollweide")
                ra_plot[ra_plot > np.pi] -= np.pi * 2.0
                axs[i].scatter(ra_plot, dec_grid, c=fp**2.0 + fc**2.0)
                axs[i].plot(right_ascension, declination, marker='*', color='red')
                axs[i].set_title(d.name)
                axs[i].grid(True)
                net += fp**2.0 + fc**2.0

            ra_plot[ra_plot > np.pi] -= np.pi * 2.0
            axs[3].remove()
            axs[3] = plt.subplot(1, 4, 4, projection="mollweide")
            axs[3].scatter(ra_plot, dec_grid, c=net)
            axs[3].plot(right_ascension, declination, marker='*', color='red')
            axs[3].set_title('Network antenna pattern')
            axs[3].grid(True)
            plt.tight_layout()
            plt.show()

        hp, hc = get_td_waveform(
            approximant=source_apx,
            mass1=mass1 * (1 + z),
            mass2=mass2 * (1 + z),
            spin1z=events['chi1z'][local_idx],
            spin2z=events['chi2z'][local_idx],
            inclination=events['iota'][local_idx],
            lambda1=lambda1,
            lambda2=lambda2,
            delta_t=1.0 / source_fs,
            f_lower=source_f_lower,
            distance=events['dL'][local_idx] * 1e3
        )

        hp, hc = hp.trim_zeros(), hc.trim_zeros()
        freq_evolution = waveform.utils.frequency_from_polarizations(hp, hc)
        i_merger = len(freq_evolution) - 1
        idx_f_cut = np.argmin(np.abs(freq_evolution[len(freq_evolution)//2:i_merger] - f_cut))
        idx_f_start = np.argmin(np.abs(freq_evolution[len(freq_evolution)//2:i_merger] - f_start))
        time_spent = abs(freq_evolution.sample_times[len(freq_evolution)//2 + idx_f_cut] - freq_evolution.sample_times[len(freq_evolution)//2 + idx_f_start])
        time_to = abs(freq_evolution.sample_times[len(freq_evolution)//2 + idx_f_cut])
        time_tot_chunk[local_idx] = time_spent
        time_to_merge_chunk[local_idx] = time_to

        if plots:
            plt.figure(num=i_plot)
            plt.plot(freq_evolution.sample_times[len(freq_evolution)//2:], freq_evolution[len(freq_evolution)//2:], label='TF Evolution', color='k')
            plt.axhspan(f_start, f_cut, alpha=0.5, color='red', label='Frequency region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
            plt.axvspan(float(freq_evolution.sample_times[len(freq_evolution)//2 + idx_f_start]), float(freq_evolution.sample_times[len(freq_evolution)//2 + idx_f_start]), alpha=0.5, color='blue', label='Time spent in region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
            plt.xlabel('Time [s]')
            plt.ylabel('Frequency [Hz]')
            plt.yscale('log')
            plt.legend()
            plt.show()
            i_plot += 1

        hp.start_time += end_time
        hc.start_time += end_time
        time_spent = end_time - hp.start_time
        iidx = np.where(np.array(hp.sample_times) == end_time)
        iidx_cut = iidx[0] - int((freq_evolution.sample_times[-1] - freq_evolution.sample_times[idx_f_cut]) * source_fs)
        iidx_st = iidx[0] - int((freq_evolution.sample_times[-1] - freq_evolution.sample_times[idx_f_start]) * source_fs)

        if plots:
            fig, axs = plt.subplots(2, sharex=True, figsize=(8, 8))
            axs[0].plot(hp.sample_times - float(hp.start_time), hp, label='hp polarization ' + source_apx, color='k')
            axs[0].axvspan(float(hp.sample_times[iidx_st]) - float(hp.start_time), float(hp.sample_times[iidx_cut]) - float(hp.start_time), alpha=0.5, color='red', label='Frequency region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
            axs[0].legend()
            axs[1].plot(hc.sample_times - float(hc.start_time), hc, label='hc polarization ' + source_apx, color='k')
            axs[1].axvspan(float(hp.sample_times[iidx_st]) - float(hp.start_time), float(hp.sample_times[iidx_cut]) - float(hp.start_time), alpha=0.5, color='red', label='Frequency region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
            axs[1].set_xlabel('Time [s]')
            axs[0].set_ylabel('Strain Amplitude')
            axs[1].set_ylabel('Strain Amplitude')
            axs[1].legend()
            plt.tight_layout()
            plt.suptitle('Time domain approximants')
            plt.show()

        if plots:
            fig, axs = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))

        for i in range(len(IFOs)):
            signal_ET1[i] = det_ET1[i].project_wave(hp, hc, right_ascension, declination, polarization)
            if i == 0:
                time_spent = np.abs(signal_ET1[0].sample_times[-1] - signal_ET1[0].sample_times[0])

            if plots:
                axs[i].plot(signal_ET1[i].sample_times - float(signal_ET1[i].start_time), signal_ET1[i], label=IFOs[i], color='k')
                axs[i].axvspan(float(signal_ET1[i].sample_times[iidx_st]) - float(signal_ET1[i].start_time), float(signal_ET1[i].sample_times[iidx_cut]) - float(signal_ET1[i].start_time), alpha=0.5, color='red', label='Frequencyregion of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
                axs[i].legend()
                axs[i].set_ylabel('Strain Amplitude')
                if i == 2:
                    axs[i].set_xlabel('Time from ' + str(from_gps(float(signal_ET1[0].start_time))) + ' [s]')
                plt.tight_layout()
                plt.suptitle('Waveforms projected con ET detectors')

        if plots:
            plt.show()

        for case_idx, case in enumerate(cases):
            ts_noise_ET1 = [None] * nIFOs
            data_ET1 = [None] * nIFOs
            noise_psd_ET1 = [None] * nIFOs
            data_to_fs_ET1 = [None] * nIFOs
            snrET1 = [None] * nIFOs
            snrtsET1 = [None] * nIFOs

            freq = case['freq']
            ETD = case['curves']

            if mass1 + mass2 > 3 and time_spent > 128:
                dur = int(time_spent * 2)
            elif mass1 + mass2 > 3 and time_spent < 128:
                dur = 128
            else:
                dur = int(time_spent + 3600)

            for i in range(len(IFOs)):
                if config == 'TRIANGLE':
                    ts_noise_ET1[i] = noise_from_sqrt_psd(freq, ETD, fs=source_fs, dur=dur, seed=i + global_idx)
                else:
                    ts_noise_ET1[i] = noise_from_sqrt_psd(freq, ETD[i], fs=source_fs, dur=dur, seed=i + global_idx)

            if mass1 + mass2 > 3:
                noise_starttime = float(signal_ET1[0].start_time) - int(time_spent / 2)
            else:
                noise_starttime = float(signal_ET1[0].start_time) - int(3600 / 2)

            noise_endtime = noise_starttime + dur
            ts_noise_t = np.linspace(noise_starttime, noise_endtime, dur * source_fs)

            if plots:
                plt.figure(num=i_plot)
                plt.plot(ts_noise_t - noise_starttime, ts_noise_ET1[0], color='black')
                plt.grid(True)
                plt.xlabel('Time from ' + str(from_gps(noise_starttime)) + ' [s]')
                plt.ylabel('Strain Amplitude')
                plt.title('Simulated noise')
                plt.xlim(0, noise_endtime - noise_starttime)
                plt.show()
                i_plot += 1

            if plots:
                fig, axs = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))

            for i in range(len(IFOs)):
                data_ET1[i] = inject(ts_noise_ET1[i], noise_starttime, signal_ET1[i], signal_ET1[i].sample_times, source_fs)

                if plots:
                    fq, asd_noise, fq2, asd_noise2 = welch_method(ts_noise_ET1[i], fs=source_fs, seg_len_secs=64)
                    fqs, asd_s, fqs2, asd_2 = welch_method(signal_ET1[i], fs=source_fs, seg_len_secs=64)
                    fqsn, asd_sn, fqsn2, asd_2n = welch_method(data_ET1[i], fs=source_fs, seg_len_secs=64)
                    curve_to_plot = ETD if config == 'TRIANGLE' else ETD[i]

                    axs[i].loglog(freq, curve_to_plot, color='darkorange', label='ETD')
                    axs[i].loglog(fq, asd_noise, color='darkgreen', alpha=0.4, label='ASD of simulated noise')
                    axs[i].loglog(np.sqrt(TimeSeries.from_pycbc(signal_ET1[i]).psd() * TimeSeries.from_pycbc(signal_ET1[i]).psd().frequencies * (float(signal_ET1[i].end_time) - float(signal_ET1[i].start_time))), label='ASD of ' + IFOs[i] + ' injected signal', color='blue')
                    axs[i].loglog(np.sqrt(data_ET1[i].psd(64, overlap=64/2, window='hann', method='welch')), label='ASD of noise plus injected signal', alpha=0.4, color='purple')
                    axs[i].legend()
                    axs[i].set_xlim(1, 1e3)
                    axs[i].set_ylim(1e-26, 1e-16)
                    axs[i].set_ylabel(r'$\frac{1}{\sqrt{Hz}}$')
                    if i == 2:
                        axs[2].set_xlabel('Frequency [Hz]')

                data_ET1[i].highpass(1)
                data_ET1[i].crop(5, 5)

            if plots:
                plt.tight_layout()
                plt.show()
                i_plot += 1

            if plots:
                plt.figure(num=i_plot)
                plt.plot((data_ET1[0].times - Quantity(noise_starttime, unit='second')) / 60, data_ET1[0], color='gray', label='Noise + Signal')
                plt.plot((signal_ET1[0].sample_times - noise_starttime) / 60, signal_ET1[0], color='red', label='Injected signal')
                plt.xlabel('Minutes from ' + str(from_gps(float(noise_starttime))))
                plt.ylabel('Strain amplitude')
                plt.legend()
                plt.show()
                i_plot += 1

            if plots:
                fig, axs = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))
                fig, axs2 = plt.subplots(nIFOs, sharex=True, figsize=(8, 8))

            for i in range(len(IFOs)):
                noise_psd_ET1[i] = TimeSeries(data_ET1[i], t0=noise_starttime, sample_rate=source_fs, times=ts_noise_t).psd(64, 32).to_pycbc()
                data_to_fs_ET1[i] = data_ET1[i].to_pycbc().to_frequencyseries()
                noise_psd_ET1[i] = interpolate(noise_psd_ET1[i], data_to_fs_ET1[i].delta_f)
                hp.resize(len(data_ET1[i]))
                snrET1[i] = matched_filter(hp, data_ET1[i].to_pycbc(), psd=noise_psd_ET1[i], low_frequency_cutoff=2, high_frequency_cutoff=10)
                snrtsET1[i] = TimeSeries.from_pycbc(snrET1[i]).abs()

                if plots:
                    axs[i].plot((snrtsET1[i].times - snrtsET1[i].times[0]) / 60, snrtsET1[i], label='SNR ' + IFOs[i], color='k')
                    axs[i].set_ylabel('SNR')
                    axs[i].legend()

                    white_data = (data_to_fs_ET1[i] / noise_psd_ET1[i]**0.5).to_timeseries()
                    white_data = white_data.highpass_fir(2, 512).lowpass_fir(200, 512)
                    to_plot = data_ET1[i] / sigma(data_ET1[i].to_pycbc(), psd=noise_psd_ET1[i], low_frequency_cutoff=2)
                    to_plot = (to_plot.to_pycbc().to_frequencyseries() * np.max(snrtsET1[i])).to_timeseries()
                    white_template = (to_plot.to_frequencyseries() / noise_psd_ET1[i]**0.5).to_timeseries()

                    axs2[i].plot(np.array(white_data.sample_times) - noise_starttime, white_data, label="Whitened data", color='k')
                    axs2[i].set_xlim(end_time - 7 - noise_starttime, end_time + 2 - noise_starttime)
                    axs2[i].legend()

                    if i == 2:
                        axs[i].set_xlabel('Minutes from ' + str(from_gps(float(noise_starttime))))
                        axs2[i].set_xlabel('Seconds from ' + str(from_gps(float(noise_starttime))))

            if plots:
                plt.show()

            if nIFOs == 3:
                netSNR = np.sqrt(np.max(snrtsET1[0])**2 + np.max(snrtsET1[1])**2 + np.max(snrtsET1[2])**2)
            else:
                netSNR = np.sqrt(np.max(snrtsET1[0])**2 + np.max(snrtsET1[1])**2)

            results_chunk[case_idx, local_idx] = netSNR

            if cumulative:
                ff = 3
                snrs = 0

                while ff <= 10 and snrs <= 12:
                    snrET1 = []
                    snrtsET1 = []

                    for i in range(len(IFOs)):
                        snrET1.append(matched_filter(hp, data_ET1[i].to_pycbc(), psd=noise_psd_ET1[i], low_frequency_cutoff=3, high_frequency_cutoff=ff))
                        snrtsET1.append(TimeSeries.from_pycbc(snrET1[i]).abs())

                    if nIFOs == 3:
                        snrs = np.sqrt(np.max(snrtsET1[0])**2 + np.max(snrtsET1[1])**2 + np.max(snrtsET1[2])**2)
                    else:
                        snrs = np.sqrt(np.max(snrtsET1[0])**2 + np.max(snrtsET1[1])**2)

                    ff += 1

                idx_f_cum_SNR = np.argmin(np.abs(freq_evolution[len(freq_evolution)//2:i_merger] - ff - 1))
                time_to_SNR = abs(freq_evolution.sample_times[len(freq_evolution)//2 + idx_f_cum_SNR])
                time_to_m_SNR_chunk[local_idx] = time_to_SNR if netSNR >= 12 else -time_to_SNR

    return {
        'positions': positions,
        'results': results_chunk,
        'time_to_merge': time_to_merge_chunk,
        'time_to_m_SNR': time_to_m_SNR_chunk,
        'time_tot': time_tot_chunk
    }


if __name__ == "__main__":
    print_program_info()

    parser = argparse.ArgumentParser()
    parser.add_argument('-case', help='candidate sites: SOS or TERZ (type str)', action='store', type=str)
    parser.add_argument('-config', help='detector configuration: TRIANGLE or 2L (type str)', action='store', type=str)
    parser.add_argument('-source_type', help='source type of the analysis: BBH or BNS (type str)', action='store', type=str)
    parser.add_argument('-plots', help='True or False - default = False (type bool)', action='store', type=bool)
    parser.add_argument('-nchunks', help='number of event chunks for multiprocessing (type int)', action='store', type=int, default=1)
    args = parser.parse_args()

    if args.plots is None:
        args.plots = False

    if args.nchunks is None or args.nchunks < 1:
        raise ValueError('-nchunks must be >= 1')

    case = args.case
    config = args.config
    source_type = args.source_type
    plots = args.plots
    nchunks = args.nchunks
    cumulative = False
    f_cut = 10
    f_start = 2

    del args

    if plots and nchunks > 1:
        raise ValueError('plots=True is supported only with -nchunks 1 in this multiprocessing version.')

    if case == 'TERZ' and config == 'TRIANGLE':
        file_list = ['../sens_curves/ET_ALL_NB.txt', '../sens_curves/ET_TERZ_10th_perc_1year.txt', '../sens_curves/ET_TERZ_50th_perc_1year.txt', '../sens_curves/ET_TERZ_90th_perc_1year.txt']
        coords = [[5.9342, 50.6575], [5.9055, 50.7533], [5.78714, 50.69021]]
        orient = [
            [azimuth(coords[0][1], coords[0][0], coords[2][1], coords[2][0]), azimuth(coords[0][1], coords[0][0], coords[1][1], coords[1][0])],
            [azimuth(coords[0][1], coords[0][0], coords[1][1], coords[1][0]), azimuth(coords[2][1], coords[2][0], coords[1][1], coords[1][0])],
            [azimuth(coords[0][1], coords[0][0], coords[2][1], coords[2][0]), azimuth(coords[1][1], coords[1][0], coords[2][1], coords[2][0])]
        ]
        alt = 0
        armlegth = 10000
        IFOs = ['ET1', 'ET2', 'ET3']
        nIFOs = 3
        print(' * Analyzing the triangle configuration for the EMR site.')

    elif case == 'SOS' and config == 'TRIANGLE':
        file_list = ['../sens_curves/ET_ALL_NB.txt', '../sens_curves/ET_P2_95th_perc_dec.txt', '../sens_curves/ET_P2_5th_perc_jul.txt']
        coords = [[9.44896, 40.472806], [9.329494, 40.441343], [9.353505, 40.53611]]
        orient = [
            [azimuth(coords[0][1], coords[0][0], coords[2][1], coords[2][0]), azimuth(coords[0][1], coords[0][0], coords[1][1], coords[1][0])],
            [azimuth(coords[0][1], coords[0][0], coords[1][1], coords[1][0]), azimuth(coords[2][1], coords[2][0], coords[1][1], coords[1][0])],
            [azimuth(coords[0][1], coords[0][0], coords[2][1], coords[2][0]), azimuth(coords[1][1], coords[1][0], coords[2][1], coords[2][0])]
        ]
        alt = 250
        armlegth = 10000
        IFOs = ['ET1', 'ET2', 'ET3']
        nIFOs = 3
        print(' * Analyzing the triangle configuration for the Sardinia site.')

    elif config == '2L':
        file_list = [
            '../sens_curves/ET_ALL_NB.txt',
            '../sens_curves/ET_P2_10th_perc_1year.txt',
            '../sens_curves/ET_P2_50th_perc_1year.txt',
            '../sens_curves/ET_P2_90th_perc_1year.txt',
            '../sens_curves/ET_ALL_NB.txt',
            '../sens_curves/ET_TERZ_10th_perc_1year.txt',
            '../sens_curves/ET_TERZ_50th_perc_1year.txt',
            '../sens_curves/ET_TERZ_90th_perc_1year.txt'
        ]
        case = '2LNET'
        IFOs = ['ET1', 'ET2']
        armlegth = 15000
        nIFOs = 2
        coords = None
        orient = None
        alt = None
        print(' * Analyzing the 2L configuration.')
    else:
        raise ValueError('Unsupported case/config combination.')

    source = registry[source_type]

    with h5py.File(source.catalogName, 'r') as f:
        N = len(f['tGPS'])
        gps_min = int(to_gps('Jan 01 2030 00:00:00.000'))
        gps_max = int(to_gps('Jan 01 2031 00:00:00.000'))
        generated_tgps = np.asarray(unifom_dist(N, gps_min, gps_max))

        if source_type == 'BNS':
            z_all = np.array(f['z'])
            idx_z_incl = np.where((z_all <= 1.5) & (z_all > 0.25))[0]
            idxs_rdn = random.sample(list(enumerate(z_all[idx_z_incl])), 1500)
            idx_tot = np.append(np.where(z_all <= 0.25)[0], np.array(idxs_rdn, dtype='int')[:, 0])
            fields_to_load = ['tGPS', 'dec', 'ra', 'psi', 'Lambda1', 'Lambda2', 'm1_source', 'm2_source', 'z', 'chi1z', 'chi2z', 'iota', 'dL']
        elif source_type == 'BBH':
            m1_all = np.array(f['m1_source'])
            m2_all = np.array(f['m2_source'])
            idx_tot = np.append(np.where((m1_all >= 100) & (m2_all < 100))[0], np.where((m2_all >= 100) & (m1_all < 100))[0])
            idx_tot = np.append(idx_tot, np.where((m1_all + m2_all >= 100))[0])
            idx_tot = np.append(idx_tot, np.where((m1_all >= 100) & (m2_all >= 100))[0])
            fields_to_load = ['tGPS', 'dec', 'ra', 'psi', 'm1_source', 'm2_source', 'z', 'chi1z', 'chi2z', 'iota', 'dL']
        else:
            raise ValueError('Unsupported source_type: ' + str(source_type))

        events = {}
        for key in fields_to_load:
            if key == 'tGPS':
                events[key] = generated_tgps[idx_tot]
            else:
                events[key] = take_h5_rows(f[key], idx_tot)

    analysis_cases = build_analysis_cases(file_list, config)
    results = {case_info['label']: np.zeros(len(idx_tot)) for case_info in analysis_cases}
    time_to_merge = np.zeros(len(idx_tot))
    time_to_m_SNR = np.zeros(len(idx_tot))
    time_tot = np.zeros(len(idx_tot))

    print(' * Analyzing ' + str(len(idx_tot)) + ' events.')
    tic = time.time()

    config_payload = {
        'source_type': source_type,
        'source_apx': source.apx,
        'source_fs': source.fs,
        'source_f_lower': source.f_lower,
        'cumulative': cumulative,
        'f_cut': f_cut,
        'f_start': f_start,
        'plots': plots,
        'config': config,
        'IFOs': IFOs,
        'nIFOs': nIFOs,
        'coords': coords,
        'orient': orient,
        'alt': alt,
        'armlegth': armlegth,
        'cases': analysis_cases
    }

    if len(idx_tot) == 0:
        chunk_payloads = []
    else:
        chunk_count = min(nchunks, len(idx_tot))
        chunk_positions = [np.asarray(chunk, dtype=int) for chunk in np.array_split(np.arange(len(idx_tot)), chunk_count) if len(chunk) > 0]
        chunk_payloads = []
        for positions in chunk_positions:
            chunk_events = {key: values[positions] for key, values in events.items()}
            chunk_payloads.append({'positions': positions, 'events': chunk_events, 'config': config_payload})

    completed = 0

    def merge_chunk_result(chunk_result):
        positions = chunk_result['positions']
        for case_idx, case_info in enumerate(analysis_cases):
            results[case_info['label']][positions] = chunk_result['results'][case_idx]
        time_to_merge[positions] = chunk_result['time_to_merge']
        time_to_m_SNR[positions] = chunk_result['time_to_m_SNR']
        time_tot[positions] = chunk_result['time_tot']

    if len(chunk_payloads) == 1:
        chunk_result = process_event_chunk(chunk_payloads[0])
        merge_chunk_result(chunk_result)
        completed = len(chunk_result['positions'])
        elapsed = time.time() - tic
        avgT = elapsed / completed if completed > 0 else 0
        eta = avgT * (len(idx_tot) - completed) / 3600 if completed > 0 else 0
        progress_bar(completed, len(idx_tot), 'Events evaluated ' + str(completed) + '/' + str(len(idx_tot)), eta, 1, 70, '█')
    elif len(chunk_payloads) > 1:
        max_workers = min(os.cpu_count() or 1, len(chunk_payloads))
        with ProcessPoolExecutor(max_workers=max_workers, mp_context=mp.get_context('spawn')) as executor:
            future_map = {executor.submit(process_event_chunk, payload): payload for payload in chunk_payloads}
            for future in as_completed(future_map):
                chunk_result = future.result()
                merge_chunk_result(chunk_result)
                completed += len(chunk_result['positions'])
                elapsed = time.time() - tic
                avgT = elapsed / completed if completed > 0 else 0
                eta = avgT * (len(idx_tot) - completed) / 3600 if completed > 0 else 0
                progress_bar(completed, len(idx_tot), 'Events evaluated ' + str(completed) + '/' + str(len(idx_tot)), eta, 1, 70, '█')

    if len(idx_tot) > 0:
        progress_bar(len(idx_tot), len(idx_tot), 'Events evaluated ' + str(len(idx_tot)) + '/' + str(len(idx_tot)), 0, 1, 70, '█')
        sys.stdout.write('\n')
        sys.stdout.flush()

    with open('../pkl/' + source_type + '_losses_' + case + '_' + source_type + '_sum_high_z_worstbest.pkl', 'wb') as file:
        pickle.dump(results, file)

    with open('../pkl/' + source_type + '_times_to_merge_' + case + '_' + source_type + '_sum_high_z_worstbest.pkl', 'wb') as file:
        pickle.dump((time_tot, time_to_merge, time_to_m_SNR), file)
