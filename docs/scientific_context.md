# Scientific Context

Future gravitational-wave observatories such as the Einstein Telescope will operate in the low-frequency regime (a few Hz), allowing signals to remain in-band for minutes to hours before merger.
Understanding how detector sensitivity affects signal detectability requires:

* Generation of realistic source populations.
* Simulation of detector noise.
* Projection of gravitational-wave polarizations onto detector responses.
* Matched-filter searches using realistic noise power spectral densities (PSDs).
* Comparison of network performance under different site and sensitivity assumptions.

This script automates the complete workflow.

## Handling Source Population

The code supports:
* Binary Black Hole (BBH) mergers
* Binary Neutron Star (BNS) mergers

Event parameters are loaded from astrophysical population catalogs stored in HDF5 format.
Relevant source properties include:
* component masses
* redshift
* spins
* sky position
* inclination
* luminosity distance
* polarization angle

## Detector Network Modelling

Two detector configurations are currently supported.
### ET Triangle
Three co-located interferometers with different arm orientations.
Possible sites:
* Sardinia (SOS)
* Euregio Meuse-Rhine (TERZ)
### 2L Network
Two geographically separated L-shaped detectors.
This configuration is used to compare performance against the triangular ET design.
Possible sites:
* Sardinia (SOS)
* Lausitz Region (DZA)

Detector locations and arm orientations are generated directly from geographical coordinates.

## Waveform Generation
Gravitational-wave signals are generated using PyCBC waveform models.
Source Type	Approximant:
* BBH:	IMRPhenomD
* BNS:	IMRPhenomPv2_NRTidalv2
  
Waveforms are generated in the time domain and include:
* cosmological redshift effects
* source inclination
* component spins
* tidal effects (for BNS systems)

## Detector Response Projection
The plus and cross polarizations:
$h_+(t),h_{\times}(t)$
are projected onto each detector using the antenna response functions
$F_+(t),F_{\times}(t)$
​	
 
to obtain the measured strain:
$h(t) = h_+(t)F_+ + h_{\times}(t)F_{\times}$

This step accounts for:
* detector orientation
* source sky location
* polarization angle
* Earth rotation through GPS time

## Noise Simulation
Detector noise is synthesized from a target Amplitude Spectral Density (ASD).

The procedure is:
* Generate Gaussian white noise in the frequency domain.
* Interpolate the desired ASD.
* Color the white noise using the ASD.
* Transform back to the time domain.
  
This produces realistic stationary Gaussian noise consistent with the specified detector sensitivity curve.

## Signal Injection
The projected waveform is injected into the simulated detector noise:
$d(t)=n(t)+h(t)$

where:

* d(t) = observed data
* n(t) = detector noise
* h(t) = gravitational-wave signal

## SNR Computation

Detection performance is evaluated through matched filtering.

For each detector:
* Estimate the PSD of the simulated data.
* Compute the matched-filter SNR time series.
* Extract the maximum SNR.

