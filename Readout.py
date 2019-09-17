# -*- coding: utf-8 -*-
'''
Created on 17.09.2019

@author: yu03
'''
from File_name_define import PI_name, SmarAct_name_1, SmarAct_name_2, Video_result_name
import numpy as np
import matplotlib.pyplot as plt

def Read_Data_4Ch(name):
    '''
        Return Data in File (4 Channels: Data_Ch1, Data_Ch2, Data_Ch3, Data_Ch4)
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
                Fs = float(m)
                print('Fs = %f\n'%Fs)
        out_str = fid.readlines()
    Data_Ch1, Data_Ch2, Data_Ch3, Data_Ch4 = [], [], [], []
    for line in out_str:
        a, b, c, d= line.strip().split(', ')
        Data_Ch1.append(float(a))
        Data_Ch2.append(float(b))
        Data_Ch3.append(float(c))
        Data_Ch4.append(float(d))    
    Data_Ch1 = np.array(Data_Ch1)
    Data_Ch2 = np.array(Data_Ch2)
    Data_Ch3 = np.array(Data_Ch3)
    Data_Ch4 = np.array(Data_Ch4)
    return Data_Ch1, Data_Ch2, Data_Ch3, Data_Ch4, Fs
    
def Read_Data_3Ch(name):
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

Lamda = 633e-9
pix_size = 5.3e-6
V_x, V_y, V_z = 0, 0, 0

 
'''
    Reading Video Result
'''
# hor_f_fit_set, ver_f_fit_set, hor_phase_centers, ver_phase_centers, fs_cam = Read_Data_4Ch(Video_result_name)
# 
# hor_angle = (V_x-Lamda*hor_f_fit_set/2)*1e6 ### urad
# hor_length = np.unwrap(hor_phase_centers)/4/np.pi*Lamda*1e9 ### nm
# ver_angle = (V_y-Lamda*ver_f_fit_set/2)*1e6 ### urad
# ver_length = np.unwrap(ver_phase_centers)/4/np.pi*Lamda*1e9 ### nm
# print(len(hor_angle))

'''
    Reading SmarAct
'''
SmarAct_CH1 = np.fromfile(SmarAct_name_1, dtype='>d')
print(SmarAct_CH1.shape)
SmarAct_CH2 = np.fromfile(SmarAct_name_2, dtype='>d')
print(SmarAct_CH2.shape)

SmarAct_CH1 = SmarAct_CH1[(SmarAct_CH1<-1e-200) | (SmarAct_CH1>1e-200)]
print(SmarAct_CH1.shape)
SmarAct_CH2 = SmarAct_CH2[(SmarAct_CH2<-1e-200) | (SmarAct_CH2>1e-200)]
print(SmarAct_CH2.shape)

SmarAct_CH1 = SmarAct_CH1*1e9 ###in nm
SmarAct_CH2 = SmarAct_CH2*1e9 ###in nm

'''
    Reading PI 6Dof
'''
length_PI, Hor_PI, Ver_PI= Read_Data_3Ch(PI_name)
print(len(length_PI))

plt.figure(1)
# plt.subplot(3,3,1)
# plt.plot(hor_length, color='blue', label='hor_length')
# plt.plot(ver_length, color='red', label='ver_length')
# plt.grid(which='both', axis='both')
# plt.legend()
# 
# plt.subplot(3,3,2)
# plt.plot(hor_angle, color='blue', label='hor_angle')
# plt.grid(which='both', axis='both')
# plt.legend()
# 
# plt.subplot(3,3,3)
# plt.plot(ver_angle, color='blue', label='ver_angle')
# plt.grid(which='both', axis='both')
# plt.legend()

plt.subplot(3,3,4)
plt.plot((SmarAct_CH2-SmarAct_CH1)/2, color='blue', label='(Ch2-Ch1)/2')
plt.grid(which='both', axis='both')
plt.legend()

plt.subplot(3,3,5)
plt.plot(SmarAct_CH1, color='blue', label='Ch1')
plt.grid(which='both', axis='both')
plt.legend()

plt.subplot(3,3,6)
plt.plot(SmarAct_CH2, color='blue', label='Ch2')
plt.grid(which='both', axis='both')
plt.legend()

plt.subplot(3,3,7)
plt.grid(which='both', axis='both')
plt.plot(length_PI, color='blue', label='length_PI')
plt.legend()

plt.subplot(3,3,8)
plt.grid(which='both', axis='both')
plt.plot(Hor_PI, color='blue', label='Hor_PI')
plt.legend()

plt.subplot(3,3,9)
plt.grid(which='both', axis='both')
plt.plot(Ver_PI, color='blue', label='Ver_PI')
plt.legend()

plt.show()


