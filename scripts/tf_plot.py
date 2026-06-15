# Script to generate Figure 3 of the paper

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



import pickle
import matplotlib.pyplot as plt
import numpy as np

with open('../pkl/tf_evo_low.pkl', 'rb') as input_file:

    f = pickle.load(input_file)
    
with open('../pkl/tf_evo_high.pkl', 'rb') as input_file2:

    f2 = pickle.load(input_file2)
    
plt.figure()
plt.grid(which='both', alpha=1)
plt.plot(f.sample_times/3600, f, label='TF Evolution', color = 'k')
plt.plot(f2.sample_times[90000:]/3600, f2[90000:],color = 'k')

#plt.axhline(y = f_cut, color = 'red', label = 'Frequency cut '+str(f_cut)+' Hz')
plt.axhspan(2, 10, alpha=0.5, color='red', label = 'Frequency region of interest ' + str(2) + '-' + str(10) + 'Hz')
#plt.axvspan(float(f.sample_times[idx_f_start]), float(f.sample_times[idx_f_cut]), alpha=0.5, color='blue', label = 'Time spent in region of interest ' + str(f_start) + '-' + str(f_cut) + 'Hz')
plt.xlabel('Time to merger [hours]')
plt.ylabel('Frequency [Hz]')
plt.yscale('log')
plt.ylim(2,1e4)
plt.xlim(-21,0)
plt.legend()
plt.show()

