# -*- coding: utf-8 -*-
'''
Created on 17.09.2019

@author: yu03
'''
from File_name_define import PI_name, SmarAct_name_1, SmarAct_name_2, Video_result_name
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from FFT_Interpolation import FFT_cal

def Read_Data_4Ch(name):
    '''
        Return Data in File (4 Channels: Data_Ch1, Data_Ch2, Data_Ch3, Data_Ch4)
        File name required (default path)
    '''
    print('Reading Data Video')
    with open(name,'r') as fid:
        line=''
        while line[0:4] != '----':
            line = fid.readline()
#             print(line)
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
    Reading Video Result
'''
hor_f_fit_set, ver_f_fit_set, hor_phase_centers, ver_phase_centers, fs_cam = Read_Data_4Ch(Video_result_name)
 
hor_angle = (V_x-Lamda*hor_f_fit_set/2)*1e6 ### urad
hor_length = np.unwrap(hor_phase_centers)/4/np.pi*Lamda*1e9 ### nm
ver_angle = (V_y-Lamda*ver_f_fit_set/2)*1e6 ### urad
ver_length = np.unwrap(ver_phase_centers)/4/np.pi*Lamda*1e9 ### nm
print('Video', len(hor_angle))

'''
    Reading SmarAct
'''
SmarAct_CH1 = np.fromfile(SmarAct_name_1, dtype='>d')
print('CH1: ', SmarAct_CH1.shape)
SmarAct_CH2 = np.fromfile(SmarAct_name_2, dtype='>d')
print('CH2: ', SmarAct_CH2.shape)

SmarAct_CH1 = SmarAct_CH1[(SmarAct_CH1<-1e-200) | (SmarAct_CH1>1e-200)]
print('CH1: ',SmarAct_CH1.shape)
SmarAct_CH2 = SmarAct_CH2[(SmarAct_CH2<-1e-200) | (SmarAct_CH2>1e-200)]
print('CH2: ',SmarAct_CH2.shape)

SmarAct_CH1 = SmarAct_CH1*1e9 ###in nm
SmarAct_CH2 = SmarAct_CH2*1e9 ###in nm

'''
    Reading PI 6Dof
'''
length_PI, Hor_PI, Ver_PI = Read_Data_3Ch(PI_name)
print('PI: ', len(length_PI))
length_PI = length_PI*1e3 ### nm

'''
    Data Alignment
'''
print('Video', len(hor_angle))
SmarAct_CH1 = SmarAct_CH1[::10]
SmarAct_CH2 = SmarAct_CH2[::10]
print('CH1: ', SmarAct_CH1.shape)
print('CH2: ', SmarAct_CH2.shape)
length_PI = length_PI[20:520]
Hor_PI = Hor_PI[20:520]
Ver_PI = Ver_PI[20:520]
print('PI: ', len(length_PI))

start = 100
end = 400
timeline = np.linspace(0, (end-start)/fs, num=(end-start))
hor_angle, hor_length, ver_angle, ver_length = hor_angle[start:end], hor_length[start:end], ver_angle[start:end], ver_length[start:end]
SmarAct_CH1, SmarAct_CH2 = SmarAct_CH1[start:end], SmarAct_CH2[start:end]
SmarAct_common, SmarAct_diff = (SmarAct_CH2-SmarAct_CH1)/2, (SmarAct_CH2+SmarAct_CH1)/2
length_PI, Hor_PI, Ver_PI = length_PI[start:end], Hor_PI[start:end], Ver_PI[start:end]



'''
    Nonlinearity Video
'''
video_length = (hor_length+ver_length)/2
video_length = video_length-np.average(video_length)
video_length_fit_params = np.polyfit(timeline, video_length, 2)
video_length_fit_poly = np.poly1d(video_length_fit_params)
video_length_fitline = video_length_fit_poly(timeline)
video_length_nonlinearity_T = video_length - video_length_fitline
spline = interp1d(video_length, video_length_nonlinearity_T, kind='cubic')
video_length_new = np.linspace(video_length[0], video_length[-1], num=len(video_length))
video_length_nonlinearity_P = spline(video_length_new)
f_video_length_nonlinearity, fft, FFT_video_length_nonlinearity_T, phi = FFT_cal(video_length_nonlinearity_T, 1/fs)
f_video_length_nonlinearity_P, fft, FFT_video_length_nonlinearity_P, phi = FFT_cal(video_length_nonlinearity_P, (video_length_new[1]-video_length_new[0]))

video_hor = hor_angle + Hor_PI
video_hor = video_hor - np.average(video_hor)
video_hor_fit_params = np.polyfit(timeline, video_hor, 1)
video_hor_fit_poly = np.poly1d(video_hor_fit_params)
video_hor_fitline = video_hor_fit_poly(timeline)
video_hor_nonlinearity_T = video_hor - video_hor_fitline
spline = interp1d(video_length, video_hor_nonlinearity_T, kind='cubic')
video_hor_nonlinearity_P = spline(video_length_new)
f_video_hor_nonlinearity, fft, FFT_video_hor_nonlinearity_T, phi = FFT_cal(video_hor_nonlinearity_T, 1/fs)
f_video_hor_nonlinearity_P, fft, FFT_video_hor_nonlinearity_P, phi = FFT_cal(video_hor_nonlinearity_P, (video_length_new[1]-video_length_new[0]))

video_ver = ver_angle + Ver_PI
video_ver = video_ver - np.average(video_ver)
video_ver_fit_params = np.polyfit(timeline, video_ver, 1)
video_ver_fit_poly = np.poly1d(video_ver_fit_params)
video_ver_fitline = video_ver_fit_poly(timeline)
video_ver_nonlinearity_T = video_ver - video_ver_fitline
spline = interp1d(video_length, video_ver_nonlinearity_T, kind='cubic')
video_ver_nonlinearity_P = spline(video_length_new)
f_video_ver_nonlinearity, fft, FFT_video_ver_nonlinearity_T, phi = FFT_cal(video_ver_nonlinearity_T, 1/fs)
f_video_ver_nonlinearity_P, fft, FFT_video_ver_nonlinearity_P, phi = FFT_cal(video_ver_nonlinearity_P, (video_length_new[1]-video_length_new[0]))


'''
    Nonlinearity Video-SmarAct
'''
length_Senson_SmarAct = video_length - SmarAct_common
length_Senson_SmarAct = length_Senson_SmarAct-np.average(length_Senson_SmarAct)
length_Senson_SmarAct_fit_params = np.polyfit(timeline, length_Senson_SmarAct, 2)
length_Senson_SmarAct_fit_poly = np.poly1d(length_Senson_SmarAct_fit_params)
length_Senson_SmarAct_fitline = length_Senson_SmarAct_fit_poly(timeline)
length_Senson_SmarAct_nonlinearity_T = length_Senson_SmarAct - length_Senson_SmarAct_fitline
spline = interp1d(SmarAct_common, length_Senson_SmarAct_nonlinearity_T, kind='cubic')
SmarAct_length_new = np.linspace(SmarAct_common[0], SmarAct_common[-1], num=len(SmarAct_common))
length_Senson_SmarAct_nonlinearity_P = spline(SmarAct_length_new)
f_length_Senson_SmarAct_nonlinearity, fft, FFT_length_Senson_SmarAct_nonlinearity_T, phi = FFT_cal(length_Senson_SmarAct_nonlinearity_T, 1/fs)
f_length_Senson_SmarAct_nonlinearity_P, fft, FFT_length_Senson_SmarAct_nonlinearity_P, phi = FFT_cal(length_Senson_SmarAct_nonlinearity_P, (SmarAct_length_new[1]-SmarAct_length_new[0]))

hor_SmarAct = np.arctan(np.array(SmarAct_diff/5e6))*1e6 ### 5mm distance

'''
    Nonlinearity Video-PI
'''
length_Senson_PI = video_length - length_PI
length_Senson_PI = length_Senson_PI-np.average(length_Senson_PI)
length_Senson_PI_fit_params = np.polyfit(timeline, length_Senson_PI, 2)
length_Senson_PI_fit_poly = np.poly1d(length_Senson_PI_fit_params)
length_Senson_PI_fitline = length_Senson_PI_fit_poly(timeline)
length_Senson_PI_nonlinearity_T = length_Senson_PI - length_Senson_PI_fitline
spline = interp1d(video_length, length_Senson_PI_nonlinearity_T, kind='cubic')
length_Senson_PI_new = np.linspace(video_length[0], video_length[-1], num=len(video_length))
length_Senson_PI_nonlinearity_P = spline(length_Senson_PI_new)
f_length_Senson_PI_nonlinearity, fft, FFT_length_Senson_PI_nonlinearity_T, phi = FFT_cal(length_Senson_PI_nonlinearity_T, 1/fs)
f_length_Senson_PI_nonlinearity_P, fft, FFT_length_Senson_PI_nonlinearity_P, phi = FFT_cal(length_Senson_PI_nonlinearity_P, (length_Senson_PI_new[1]-length_Senson_PI_new[0]))

Hor_PI = Hor_PI - np.average(Hor_PI)



'''
    Plotting
'''
plt.figure('Raw Data Overview')
plt.gcf().set_size_inches(18,9)
plt.subplot(3,3,1)
plt.plot(timeline, hor_length, color='blue', label='hor_length')
plt.plot(timeline, ver_length, color='red', label='ver_length')
plt.grid(which='both', axis='both')
plt.title('Video length')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()
 
plt.subplot(3,3,2)
plt.plot(timeline, hor_angle, color='blue', label='hor_angle')
plt.grid(which='both', axis='both')
plt.title('Video Horizontal Angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.legend()
 
plt.subplot(3,3,3)
plt.plot(timeline, ver_angle, color='blue', label='ver_angle')
plt.grid(which='both', axis='both')
plt.title('Video Vertical Angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(3,3,4)
plt.plot(timeline, SmarAct_common, color='blue', label='common')
plt.grid(which='both', axis='both')
plt.title('SmarAct length')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,5)
plt.plot(timeline, SmarAct_diff, color='blue', label='differential')
plt.grid(which='both', axis='both')
plt.title('SmarAct length')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,6)
plt.plot(timeline, SmarAct_CH2, color='blue', label='Ch2')
plt.plot(timeline, SmarAct_CH1, color='red', label='Ch1')
plt.grid(which='both', axis='both')
plt.title('SmarAct length')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,7)
plt.plot(timeline, length_PI, color='blue', label='length_PI')
plt.title('PI length')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.grid(which='both', axis='both')
plt.legend()

plt.subplot(3,3,8)
plt.plot(timeline, Hor_PI, color='blue', label='Hor_PI')
plt.title('PI Horizontal Angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.grid(which='both', axis='both')
plt.legend()


plt.subplot(3,3,9)
plt.grid(which='both', axis='both')
plt.plot(timeline, Ver_PI, color='blue', label='Ver_PI')
plt.title('PI Vertical Angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.legend()

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.tight_layout()



plt.figure('Length Nonlinearity')
plt.gcf().set_size_inches(18,9)
plt.subplot(3,3,1)
plt.plot(timeline, video_length, color='blue', label='video_length=(hor+ver)/2')
plt.plot(timeline, video_length_fitline, color='red', label='fitting')
plt.grid(which='both', axis='both')
plt.title('Video length')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,2)
plt.plot(video_length, video_length_nonlinearity_T, color='blue', label='video_length_nonlinearity_Time')
plt.plot(video_length, video_length_nonlinearity_P, color='red', label='video_length_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.title('Video length Nonlinearity')
plt.xlabel('Position /nm')
plt.ylabel('Deviation /nm')
plt.legend()

plt.subplot(3,3,3)
plt.loglog(1/f_video_length_nonlinearity_P, FFT_video_length_nonlinearity_T, color='blue', label='video_length_nonlinearity_Time')
plt.loglog(1/f_video_length_nonlinearity_P, FFT_video_length_nonlinearity_P, color='red', label='video_length_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.gca().invert_xaxis()
plt.title('Video length Nonlinearity FFT')
plt.xlabel('Wavelength /nm')
plt.ylabel('Position Amplitude /nm')
plt.legend()

plt.subplot(3,3,4)
plt.plot(timeline, length_Senson_SmarAct, color='blue', label='length:Senson-SmarAct')
plt.plot(timeline, length_Senson_SmarAct_fitline, color='red', label='fitting')
plt.grid(which='both', axis='both')
plt.title('length:Senson-SmarAct')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,5)
plt.plot(SmarAct_common, length_Senson_SmarAct_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
plt.plot(SmarAct_common, length_Senson_SmarAct_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.title('length Nonlinearity: Senson-SmarAct')
plt.xlabel('Position /nm')
plt.ylabel('Deviation /nm')
plt.legend()

plt.subplot(3,3,6)
plt.loglog(1/f_length_Senson_SmarAct_nonlinearity_P, FFT_length_Senson_SmarAct_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
plt.loglog(1/f_length_Senson_SmarAct_nonlinearity_P, FFT_length_Senson_SmarAct_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.gca().invert_xaxis()
plt.title('length Nonlinearity FFT: Senson-SmarAct')
plt.xlabel('Wavelength /nm')
plt.ylabel('Position Amplitude /nm')
plt.legend()

plt.subplot(3,3,7)
plt.plot(timeline, length_Senson_PI, color='blue', label='length:Senson-PI')
plt.plot(timeline, length_Senson_PI_fitline, color='red', label='fitting')
plt.grid(which='both', axis='both')
plt.title('length:Senson-PI')
plt.xlabel('Time /s')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,8)
plt.plot(video_length, length_Senson_PI_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
plt.plot(video_length, length_Senson_PI_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.title('length Nonlinearity: Senson-PI')
plt.xlabel('Position /nm')
plt.ylabel('Deviation /nm')
plt.legend()

plt.subplot(3,3,9)
plt.loglog(1/f_length_Senson_PI_nonlinearity_P, FFT_length_Senson_PI_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
plt.loglog(1/f_length_Senson_PI_nonlinearity_P, FFT_length_Senson_PI_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.gca().invert_xaxis()
plt.title('length Nonlinearity FFT: Senson-PI')
plt.xlabel('Wavelength /nm')
plt.ylabel('Position Amplitude /nm')
plt.legend()

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.tight_layout()


plt.figure('Angular Nonlinearity')
plt.gcf().set_size_inches(18,9)
plt.subplot(2,3,1)
plt.plot(timeline, video_hor, color='blue', label='hor: Video-PI')
plt.plot(timeline, video_hor_fitline, color='red', label='fitting')
plt.plot(timeline, Hor_PI, color='black', label='PI')
plt.plot(timeline, hor_SmarAct, color='green', label='SmarAct')
plt.grid(which='both', axis='both')
plt.title('Video horizontal angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(2,3,2)
plt.plot(video_length, video_hor_nonlinearity_T, color='blue', label='hor_video-PI_nonlinearity_Time')
plt.plot(video_length, video_hor_nonlinearity_P, color='red', label='hor_video-PI_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.title('Video horizontal angle Nonlinearity')
plt.xlabel('Position /nm')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(2,3,3)
plt.loglog(1/f_video_hor_nonlinearity_P, FFT_video_hor_nonlinearity_T, color='blue', label='hor_video-PI_nonlinearity_Time')
plt.loglog(1/f_video_hor_nonlinearity_P, FFT_video_hor_nonlinearity_P, color='red', label='hor_video-PI_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.gca().invert_xaxis()
plt.title('Video horizontal angle Nonlinearity FFT')
plt.xlabel('Wavelength /nm')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(2,3,4)
plt.plot(timeline, video_ver, color='blue', label='ver: Video-PI')
plt.plot(timeline, video_ver_fitline, color='red', label='fitting')
plt.plot(timeline, Ver_PI, color='black', label='PI')
plt.grid(which='both', axis='both')
plt.title('Video vertical angle')
plt.xlabel('Time /s')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(2,3,5)
plt.plot(video_length, video_ver_nonlinearity_T, color='blue', label='video_ver_angle_nonlinearity_Time')
plt.plot(video_length, video_ver_nonlinearity_P, color='red', label='video_ver_angle_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.title('Video vertical angle Nonlinearity')
plt.xlabel('Position /nm')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(2,3,6)
plt.loglog(1/f_video_ver_nonlinearity_P, FFT_video_ver_nonlinearity_T, color='blue', label='ver_video-PI_nonlinearity_Time')
plt.loglog(1/f_video_ver_nonlinearity_P, FFT_video_ver_nonlinearity_P, color='red', label='ver_video-PI_nonlinearity_Pos.')
plt.grid(which='both', axis='both')
plt.gca().invert_xaxis()
plt.title('Video horizontal angle Nonlinearity FFT')
plt.xlabel('Wavelength /nm')
plt.ylabel('Angle /urad')
plt.legend()

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.tight_layout()
plt.show()


