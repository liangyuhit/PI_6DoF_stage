# -*- coding: utf-8 -*-
'''
Created on 23.09.2019

@author: yu03
'''
from File_name_define import PI_name, SmarAct_name_1, SmarAct_name_2, Video_result_name, Numpy_result_name
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from FFT_Interpolation import FFT_cal


def Read_Data_2Ch(name):
    '''
        Return Data in File (4 Channels: Data_Ch1, Data_Ch2)
        File name required (default path)
    '''
    print('Reading Data')
    with open(name,'r') as fid:
        line=''
        while line[0:4] != '----':
            line = fid.readline()
            print(line)
            if line[0:2] == 'Fs':
                p, q, m, n = line.strip().split(' ')
                fs_cam = float(m)
                print('fs_cam = %f\n'%fs_cam)
        out_str = fid.readlines()
    Data_Ch1, Data_Ch2 = [], []
    for line in out_str:
        a, b= line.strip().split(', ')
        Data_Ch1.append(float(a))
        Data_Ch2.append(float(b))
    Data_Ch1 = np.array(Data_Ch1)
    Data_Ch2 = np.array(Data_Ch2)
    return Data_Ch1, Data_Ch2, fs_cam

def Read_Data_3Ch(name):
    '''
        Return Data in File (4 Channels: Data_Ch1, Data_Ch2)
        File name required (default path)
    '''
    print('Reading Data PI')
    with open(name,'r') as fid:
        line=''
        while line[0:4] != '----':
            line = fid.readline()
#             print(line)
            if line[0:2] == 'Fs':
                p, q, m, n = line.strip().split(' ')
                fs_cam = float(m)
                print('fs_cam = %f\n'%fs_cam)
        out_str = fid.readlines()
    Data_Ch1, Data_Ch2, Data_Ch3 = [], [], []
    for line in out_str:
        a, b, c= line.strip().split(', ')
        Data_Ch1.append(float(a))
        Data_Ch2.append(float(b))
        Data_Ch3.append(float(c))
    Data_Ch1 = np.array(Data_Ch1)
    Data_Ch2 = np.array(Data_Ch2)
    Data_Ch3 = np.array(Data_Ch3)
    return Data_Ch1, Data_Ch2, Data_Ch3

np.seterr(divide='ignore')
Lamda = 633e-9
pix_size = 5.3e-6
V_x, V_y, V_z = 0, 0, 0
fs = 50

'''
    Reading numpy result
'''

hor_f_fit_set, hor_phase_centers, fs_cam = Read_Data_2Ch(Numpy_result_name)
hor_angle = (V_x-Lamda*hor_f_fit_set/2)*1e6 ### urad
hor_length = np.unwrap(hor_phase_centers)/4/np.pi*Lamda*1e9 ### nm

'''
    Reading SmarAct
'''
SmarAct_CH1 = np.fromfile(SmarAct_name_1, dtype='>d')
print('CH1: ', SmarAct_CH1.shape)
SmarAct_CH2 = np.fromfile(SmarAct_name_2, dtype='>d')
print('CH2: ', SmarAct_CH2.shape)

SmarAct_CH1 = np.insert(SmarAct_CH1, -1, SmarAct_CH1[-1])
SmarAct_CH2 = np.insert(SmarAct_CH2, -1, SmarAct_CH2[-1])
SmarAct_CH2 = np.insert(SmarAct_CH2, -1, SmarAct_CH2[-1])

SmarAct_CH1 = SmarAct_CH1[(SmarAct_CH1<-1e-200) | (SmarAct_CH1>1e-200)]
print('CH1: ',SmarAct_CH1.shape)
SmarAct_CH2 = SmarAct_CH2[(SmarAct_CH2<-1e-200) | (SmarAct_CH2>1e-200)]
print('CH2: ',SmarAct_CH2.shape)




SmarAct_CH1 = SmarAct_CH1*1e9 ###in nm
SmarAct_CH2 = SmarAct_CH2*1e9 ###in nm

SmarAct_CH1 = -SmarAct_CH1
# SmarAct_CH2 = -SmarAct_CH2

SmarAct_common, SmarAct_diff = (SmarAct_CH2+SmarAct_CH1)/2, (SmarAct_CH2-SmarAct_CH1)/2
angle_SmarAct = np.arctan(np.array(SmarAct_diff/3.3e6))*1e6 ### 5mm distance

timeline = np.arange(len(hor_length))/fs_cam/3600 ### in hour
# print(timeline)
'''
    Plotting
'''
plt.figure('Stability')
plt.gcf().set_size_inches(18,9)

plt.subplot(2,2,1)
# plt.plot(timeline, SmarAct_diff*10, color='black', label='10 x SmarAct Diff.')
plt.plot(timeline, SmarAct_CH1, color='green', label='SmarAct CH1')
plt.plot(timeline, SmarAct_CH2, color='cyan', label='SmarAct CH2')
plt.plot(timeline, SmarAct_common, color='red', label='SmarAct Common')
plt.plot(timeline, hor_length, color='blue', label='Sensor length')
plt.grid(which='both', axis='both')
plt.title('length')
plt.xlabel('Time /h')
plt.ylabel('Position /nm')
plt.legend()
plt.subplot(2,2,2)
plt.plot(timeline, SmarAct_common-hor_length, color='red', label='SmarAct - Sensor')
# plt.plot(timeline, hor_length, color='blue', label='Sensor length')
plt.grid(which='both', axis='both')
plt.title('length')
plt.xlabel('Time /h')
plt.ylabel('Position /nm')
plt.legend()


plt.subplot(2,2,3)
plt.plot(timeline, hor_angle-np.average(hor_angle), color='blue', label='Sensor hor. tilt')
plt.plot(timeline, angle_SmarAct, color='red', label='SmarAct hor. tilt')
plt.grid(which='both', axis='both')
plt.title('Hor. Tilt')
plt.xlabel('Time /h')
plt.ylabel('Angle /urad')
plt.legend()
plt.subplot(2,2,4)
plt.plot(timeline, angle_SmarAct-(hor_angle-np.average(hor_angle)), color='blue', label='SmarAct-Sensor')
# plt.plot(timeline, angle_SmarAct, color='red', label='SmarAct hor. tilt')
plt.grid(which='both', axis='both')
plt.title('Hor. Tilt')
plt.xlabel('Time /h')
plt.ylabel('Angle /urad')
plt.legend()

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.tight_layout()

plt.show()

