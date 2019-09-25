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
fs = 47.6

'''
    Reading Video Result
'''
hor_f_fit_set, ver_f_fit_set, hor_phase_centers, ver_phase_centers, fs_cam = Read_Data_4Ch(Video_result_name)
 
hor_angle = (V_x-Lamda*hor_f_fit_set/2)*1e6 ### urad
hor_length = np.unwrap(hor_phase_centers)/4/np.pi*Lamda*1e9 ### nm
ver_angle = (V_y-Lamda*ver_f_fit_set/2)*1e6 ### urad
ver_length = np.unwrap(ver_phase_centers)/4/np.pi*Lamda*1e9 ### nm
# if 1:
#     '''
#         lost trigger compensation
#     '''
#     missing_pos = [946, 1550]
#     for factor in missing_pos:
# #     factor = 946
#         hor_angle = np.insert(hor_angle, factor, (hor_angle[factor]+hor_angle[factor-1])/2)
#         hor_length = np.insert(hor_length, factor, (hor_length[factor]+hor_length[factor-1])/2)
#         ver_angle = np.insert(ver_angle, factor, (ver_angle[factor]+ver_angle[factor-1])/2)
#         ver_length = np.insert(ver_length, factor, (ver_length[factor]+ver_length[factor-1])/2)
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
SmarAct_CH1 = SmarAct_CH1[::50]
SmarAct_CH2 = SmarAct_CH2[::50]
# if 1:
#     '''
#         lost trigger compensation
#     '''
#     SmarAct_CH1 = np.insert(SmarAct_CH1, 464, (SmarAct_CH1[464]+SmarAct_CH1[463])/2)
#     SmarAct_CH2 = np.insert(SmarAct_CH2, 464, (SmarAct_CH2[464]+SmarAct_CH2[463])/2)
print('CH1: ', SmarAct_CH1.shape)
print('CH2: ', SmarAct_CH2.shape)
length_PI = length_PI
Hor_PI = Hor_PI
Ver_PI = Ver_PI
# print('PI: ', len(length_PI))

SmarAct_CH2 = -SmarAct_CH2



if 1:
    start = 300
    end = 2200
    timeline = np.linspace(0, (end-start)/fs, num=(end-start))
    hor_angle, hor_length, ver_angle, ver_length = hor_angle[start:end], hor_length[start:end], ver_angle[start:end], ver_length[start:end]
    SmarAct_CH1, SmarAct_CH2 = SmarAct_CH1[start:end], SmarAct_CH2[start:end]    
    length_PI, Hor_PI, Ver_PI = length_PI[start:end], Hor_PI[start:end], Ver_PI[start:end]
    

SmarAct_common, SmarAct_diff = (SmarAct_CH2+SmarAct_CH1)/2, (SmarAct_CH2-SmarAct_CH1)/2
angle_SmarAct = np.arctan(np.array(SmarAct_diff/5e6))*1e6 ### 5mm distance

# video_length = (hor_length+ver_length)/2
# video_length = video_length-np.average(video_length)

# video_length = video_length * (np.max(length_PI)-np.min(length_PI))/(np.max(video_length)-np.min(video_length))
# SmarAct_common = -SmarAct_common * (np.max(length_PI)-np.min(length_PI))/(np.max(SmarAct_common)-np.min(SmarAct_common))


# video_length = np.insert(video_length, 705, (video_length[704]+video_length[705])/2)
# video_length = np.insert(video_length, 4655, (video_length[4654]+video_length[4655])/2)
# print('Video', len(video_length))
# length_Senson_PI = video_length - length_PI

if 1:
    '''
        Nonlinearity Video
    '''
    
    length_dof = 10
    angle_dof = 3
    
    video_length = (hor_length+ver_length)/2
    video_length = video_length-np.average(video_length)
    video_length_fit_params = np.polyfit(timeline, video_length, length_dof)
    video_length_fit_poly = np.poly1d(video_length_fit_params)
    video_length_fitline = video_length_fit_poly(timeline)
    video_length_nonlinearity_T = video_length - video_length_fitline
    spline = interp1d(video_length_fitline, video_length_nonlinearity_T, kind='cubic', bounds_error=False, fill_value=0)
    video_length_new = np.linspace(video_length[0], video_length[-1], num=len(video_length))
    video_length_nonlinearity_P = spline(video_length_new)
    f_video_length_nonlinearity, fft, FFT_video_length_nonlinearity_T, phi = FFT_cal(video_length_nonlinearity_T, 1/fs)
    f_video_length_nonlinearity_P, fft, FFT_video_length_nonlinearity_P, phi = FFT_cal(video_length_nonlinearity_P, (video_length_new[1]-video_length_new[0]))
#     print(video_length_nonlinearity_P)
    
    video_hor = hor_angle
    video_hor = video_hor - np.average(video_hor)
    video_hor_fit_params = np.polyfit(timeline, video_hor, angle_dof)
    video_hor_fit_poly = np.poly1d(video_hor_fit_params)
    video_hor_fitline = video_hor_fit_poly(timeline)
    video_hor_nonlinearity_T = video_hor - video_hor_fitline
    spline = interp1d(video_length_fitline, video_hor_nonlinearity_T, kind='cubic', bounds_error=False, fill_value=0)
    video_hor_nonlinearity_P = spline(video_length_new)
    f_video_hor_nonlinearity, fft, FFT_video_hor_nonlinearity_T, phi = FFT_cal(video_hor_nonlinearity_T, 1/fs)
    f_video_hor_nonlinearity_P, fft, FFT_video_hor_nonlinearity_P, phi = FFT_cal(video_hor_nonlinearity_P, (video_length_new[1]-video_length_new[0]))
     
    video_ver = ver_angle
    video_ver = video_ver - np.average(video_ver)
    video_ver_fit_params = np.polyfit(timeline, video_ver, angle_dof)
    video_ver_fit_poly = np.poly1d(video_ver_fit_params)
    video_ver_fitline = video_ver_fit_poly(timeline)
    video_ver_nonlinearity_T = video_ver - video_ver_fitline
    spline = interp1d(video_length_fitline, video_ver_nonlinearity_T, kind='cubic', bounds_error=False, fill_value=0)
    video_ver_nonlinearity_P = spline(video_length_new)
    f_video_ver_nonlinearity, fft, FFT_video_ver_nonlinearity_T, phi = FFT_cal(video_ver_nonlinearity_T, 1/fs)
    f_video_ver_nonlinearity_P, fft, FFT_video_ver_nonlinearity_P, phi = FFT_cal(video_ver_nonlinearity_P, (video_length_new[1]-video_length_new[0]))
     
    '''
        Nonlinearity Video-SmarAct
    '''
    length_Senson_SmarAct = video_length - SmarAct_common
    length_Senson_SmarAct = length_Senson_SmarAct-np.average(length_Senson_SmarAct)
    length_Senson_SmarAct_fit_params = np.polyfit(timeline, length_Senson_SmarAct, length_dof)
    length_Senson_SmarAct_fit_poly = np.poly1d(length_Senson_SmarAct_fit_params)
    length_Senson_SmarAct_fitline = length_Senson_SmarAct_fit_poly(timeline)
    length_Senson_SmarAct_nonlinearity_T = length_Senson_SmarAct - length_Senson_SmarAct_fitline
    spline = interp1d(SmarAct_common, length_Senson_SmarAct_nonlinearity_T, kind='cubic')
    SmarAct_length_new = np.linspace(SmarAct_common[0], SmarAct_common[-1], num=len(SmarAct_common))
    length_Senson_SmarAct_nonlinearity_P = spline(SmarAct_length_new)
    f_length_Senson_SmarAct_nonlinearity, fft, FFT_length_Senson_SmarAct_nonlinearity_T, phi = FFT_cal(length_Senson_SmarAct_nonlinearity_T, 1/fs)
    f_length_Senson_SmarAct_nonlinearity_P, fft, FFT_length_Senson_SmarAct_nonlinearity_P, phi = FFT_cal(length_Senson_SmarAct_nonlinearity_P, (SmarAct_length_new[1]-SmarAct_length_new[0]))

    
    '''
        Nonlinearity SmarAct
    '''
    length_SmarAct = SmarAct_common - np.average(SmarAct_common)
    length_SmarAct_fit_params = np.polyfit(timeline, length_SmarAct, length_dof)
    length_SmarAct_fit_poly = np.poly1d(length_SmarAct_fit_params)
    length_SmarAct_fitline = length_SmarAct_fit_poly(timeline)
    length_SmarAct_nonlinearity_T = length_SmarAct - length_SmarAct_fitline
    spline = interp1d(length_SmarAct, length_SmarAct_nonlinearity_T, kind='cubic', bounds_error=False, fill_value=0)
    length_SmarAct_new = np.linspace(length_SmarAct[0], length_SmarAct[-1], num=len(length_SmarAct))
    length_SmarAct_nonlinearity_P = spline(length_SmarAct_new)
    f_length_SmarAct_nonlinearity, fft, FFT_length_SmarAct_nonlinearity_T, phi = FFT_cal(length_SmarAct_nonlinearity_T, 1/fs)
    f_length_SmarAct_nonlinearity_P, fft, FFT_length_SmarAct_nonlinearity_P, phi = FFT_cal(length_SmarAct_nonlinearity_P, (length_SmarAct_new[1]-length_SmarAct_new[0]))
    
    hor_SmarAct = angle_SmarAct - np.average(angle_SmarAct)
    hor_SmarAct_fit_params = np.polyfit(timeline, hor_SmarAct, angle_dof)
    hor_SmarAct_fit_poly = np.poly1d(hor_SmarAct_fit_params)
    hor_SmarAct_fitline = hor_SmarAct_fit_poly(timeline)
    hor_SmarAct_nonlinearity_T = hor_SmarAct - hor_SmarAct_fitline
    spline = interp1d(length_SmarAct, hor_SmarAct_nonlinearity_T, kind='cubic', bounds_error=False, fill_value=0)
    hor_SmarAct_new = np.linspace(length_SmarAct[0], length_SmarAct[-1], num=len(hor_SmarAct))
    hor_SmarAct_nonlinearity_P = spline(hor_SmarAct_new)
    f_hor_SmarAct_nonlinearity, fft, FFT_hor_SmarAct_nonlinearity_T, phi = FFT_cal(hor_SmarAct_nonlinearity_T, 1/fs)
    f_hor_SmarAct_nonlinearity_P, fft, FFT_hor_SmarAct_nonlinearity_P, phi = FFT_cal(hor_SmarAct_nonlinearity_P, (hor_SmarAct_new[1]-hor_SmarAct_new[0]))
    
    
    
    '''
        Nonlinearity Video-PI
    '''
    length_Senson_PI = video_length - length_PI
    length_Senson_PI = length_Senson_PI-np.average(length_Senson_PI)
    length_Senson_PI_fit_params = np.polyfit(timeline, length_Senson_PI, length_dof)
    length_Senson_PI_fit_poly = np.poly1d(length_Senson_PI_fit_params)
    length_Senson_PI_fitline = length_Senson_PI_fit_poly(timeline)
    length_Senson_PI_nonlinearity_T = length_Senson_PI - length_Senson_PI_fitline
    spline = interp1d(video_length_fitline, length_Senson_PI_nonlinearity_T, kind='cubic', bounds_error=False, fill_value=0)
    length_Senson_PI_new = np.linspace(video_length[0], video_length[-1], num=len(video_length))
    length_Senson_PI_nonlinearity_P = spline(length_Senson_PI_new)
    f_length_Senson_PI_nonlinearity, fft, FFT_length_Senson_PI_nonlinearity_T, phi = FFT_cal(length_Senson_PI_nonlinearity_T, 1/fs)
    f_length_Senson_PI_nonlinearity_P, fft, FFT_length_Senson_PI_nonlinearity_P, phi = FFT_cal(length_Senson_PI_nonlinearity_P, (length_Senson_PI_new[1]-length_Senson_PI_new[0]))
     
    Hor_PI = Hor_PI - np.average(Hor_PI)
    Ver_PI = Ver_PI - np.average(Ver_PI)

    '''
        Nonlinearity SmarAct-PI
    '''
    length_SmarAct_PI = SmarAct_common - length_PI
    length_SmarAct_PI = length_Senson_PI-np.average(length_Senson_PI)
    length_SmarAct_PI_fit_params = np.polyfit(timeline, length_SmarAct_PI, length_dof)
    length_SmarAct_PI_fit_poly = np.poly1d(length_SmarAct_PI_fit_params)
    length_SmarAct_PI_fitline = length_SmarAct_PI_fit_poly(timeline)
    length_SmarAct_PI_nonlinearity_T = length_SmarAct_PI - length_SmarAct_PI_fitline
    spline = interp1d(SmarAct_common, length_SmarAct_PI_nonlinearity_T, kind='cubic')
    length_SmarAct_PI_new = np.linspace(SmarAct_common[0], SmarAct_common[-1], num=len(SmarAct_common))
    length_SmarAct_PI_nonlinearity_P = spline(length_SmarAct_PI_new)
    f_length_SmarAct_PI_nonlinearity, fft, FFT_length_SmarAct_PI_nonlinearity_T, phi = FFT_cal(length_SmarAct_PI_nonlinearity_T, 1/fs)
    f_length_SmarAct_PI_nonlinearity_P, fft, FFT_length_SmarAct_PI_nonlinearity_P, phi = FFT_cal(length_SmarAct_PI_nonlinearity_P, (length_SmarAct_PI_new[1]-length_SmarAct_PI_new[0]))


'''
    Plotting
'''
plt.figure('Raw Data Overview')
plt.gcf().set_size_inches(18,9)
plt.subplot(3,3,1)
plt.plot(hor_length, color='blue', label='hor_length')
plt.plot(ver_length, color='red', label='ver_length')
# plt.plot(video_length, color='black', label='vidoe length(common)')
plt.grid(which='both', axis='both')
plt.title('Video length')
plt.xlabel('Sample')
plt.ylabel('Position /nm')
plt.legend()
plt.subplot(3,3,2)
plt.plot(hor_angle, color='blue', label='hor_angle')
plt.grid(which='both', axis='both')
plt.title('Video Horizontal Angle')
plt.xlabel('Sample')
plt.ylabel('Angle /urad')
plt.legend()
plt.subplot(3,3,3)
plt.plot(ver_angle, color='blue', label='ver_angle')
plt.grid(which='both', axis='both')
plt.title('Video Vertical Angle')
plt.xlabel('Sample')
plt.ylabel('Angle /urad')
plt.legend()

plt.subplot(3,3,4)
plt.plot(SmarAct_common, color='blue', label='common')
plt.grid(which='both', axis='both')
plt.title('SmarAct length')
plt.xlabel('Sample')
plt.ylabel('Position /nm')
plt.legend()
plt.subplot(3,3,5)
plt.plot(SmarAct_diff, color='blue', label='differential')
plt.grid(which='both', axis='both')
plt.title('SmarAct length')
plt.xlabel('Sample')
plt.ylabel('Position /nm')
plt.legend()
plt.subplot(3,3,6)
plt.plot(SmarAct_CH2, color='blue', label='Ch2')
plt.plot(SmarAct_CH1, color='red', label='Ch1')
plt.grid(which='both', axis='both')
plt.title('SmarAct length')
plt.xlabel('Sample')
plt.ylabel('Position /nm')
plt.legend()

plt.subplot(3,3,7)
plt.plot(length_PI, color='blue', label='length_PI')
plt.title('PI length')
plt.xlabel('Sample')
plt.ylabel('Position /nm')
plt.grid(which='both', axis='both')
plt.legend()
plt.subplot(3,3,8)
plt.plot(Hor_PI, color='blue', label='Hor_PI')
plt.title('PI Horizontal Angle')
plt.xlabel('Sample')
plt.ylabel('Angle /urad')
plt.grid(which='both', axis='both')
plt.legend()
plt.subplot(3,3,9)
plt.grid(which='both', axis='both')
plt.plot(Ver_PI, color='blue', label='Ver_PI')
plt.title('PI Vertical Angle')
plt.xlabel('Sample')
plt.ylabel('Angle /urad')
plt.legend()

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.tight_layout()


if 1:  
    '''
        Length Nonlinearity
    '''
    plt.figure('Length Nonlinearity')
    plt.gcf().set_size_inches(18,9)
    
    plt.subplot(4,3,1)
    plt.plot(timeline, video_length, color='blue', label='video_length=(hor+ver)/2')
    plt.plot(timeline, video_length_fitline, color='red', label='fitting')
    plt.grid(which='both', axis='both')
    plt.title('Video length')
    plt.xlabel('Time /s')
    plt.ylabel('Position /nm')
    plt.legend()
    plt.subplot(4,3,2)
    plt.plot(video_length, video_length_nonlinearity_T, color='blue', label='video_length_nonlinearity_Time')
    plt.plot(video_length, video_length_nonlinearity_P, color='red', label='video_length_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('Video length Nonlinearity')
    plt.xlabel('Position /nm')
    plt.ylabel('Deviation /nm')
    plt.legend()
    plt.subplot(4,3,3)
    plt.loglog(1/f_video_length_nonlinearity_P, FFT_video_length_nonlinearity_T, color='blue', label='video_length_nonlinearity_Time')
    plt.loglog(1/f_video_length_nonlinearity_P, FFT_video_length_nonlinearity_P, color='red', label='video_length_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('Video length Nonlinearity FFT')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Position Amplitude /nm')
    plt.xlim(1e4,30)
    plt.ylim(1e-4,1)
    plt.legend()
    
    plt.subplot(4,3,4)
    plt.plot(timeline, length_SmarAct, color='green', label='SmarAct_length=(ch1+ch2)/2')
    plt.plot(timeline, length_SmarAct_fitline, color='red', label='fitting')
    plt.grid(which='both', axis='both')
    plt.title('SmarAct length')
    plt.xlabel('Time /s')
    plt.ylabel('Position /nm')
    plt.legend()
    plt.subplot(4,3,5)
    plt.plot(length_SmarAct, length_SmarAct_nonlinearity_T, color='green', label='SmarAct_nonlinearity_Time')
    plt.plot(length_SmarAct, length_SmarAct_nonlinearity_P, color='red', label='SmarAct_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('SmarAct Length Nonlinearity')
    plt.xlabel('Position /nm')
    plt.ylabel('Deviation /nm')
    plt.legend()
    plt.subplot(4,3,6)
    plt.loglog(1/f_length_SmarAct_nonlinearity_P, FFT_length_SmarAct_nonlinearity_T, color='green', label='SmarAct_nonlinearity_Time')
    plt.loglog(1/f_length_SmarAct_nonlinearity_P, FFT_length_SmarAct_nonlinearity_P, color='red', label='SmarAct_nonlinearity_Pos.')
    plt.loglog(1/f_length_SmarAct_nonlinearity_P, FFT_video_length_nonlinearity_P, color='blue', label='video_length_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('SmarAct length Nonlinearity FFT')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Position Amplitude /nm')
    plt.xlim(1e4,30)
    plt.ylim(1e-4,1)
    plt.legend()
    
    plt.subplot(4,3,7)
    plt.plot(length_Senson_SmarAct, color='blue', label='length:Senson-SmarAct')
    plt.plot(length_Senson_SmarAct_fitline, color='red', label='fitting')
    plt.grid(which='both', axis='both')
    plt.title('length:Senson-SmarAct')
    plt.xlabel('Time /s')
    plt.ylabel('Position /nm')
    plt.legend()
    plt.subplot(4,3,8)
    plt.plot(SmarAct_common, length_Senson_SmarAct_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
    plt.plot(SmarAct_common, length_Senson_SmarAct_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('length Nonlinearity: Senson-SmarAct')
    plt.xlabel('Position /nm')
    plt.ylabel('Deviation /nm')
    plt.legend()
    plt.subplot(4,3,9)
    plt.loglog(1/f_length_Senson_SmarAct_nonlinearity_P, FFT_length_Senson_SmarAct_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
    plt.loglog(1/f_length_Senson_SmarAct_nonlinearity_P, FFT_length_Senson_SmarAct_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('length Nonlinearity FFT: Senson-SmarAct')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Position Amplitude /nm')
    plt.xlim(1e4,30)
    plt.ylim(1e-4, 1)
    plt.legend()
     
    
    plt.subplot(4,3,10)
    plt.plot(timeline, length_Senson_PI, color='blue', label='length:Senson-PI')
    plt.plot(timeline, length_Senson_PI_fitline, color='red', label='fitting')
    plt.grid(which='both', axis='both')
    plt.title('length:Senson-PI')
    plt.xlabel('Time /s')
    plt.ylabel('Position /nm')
    plt.legend()
    plt.subplot(4,3,11)
    plt.plot(video_length, length_Senson_PI_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
    plt.plot(video_length, length_Senson_PI_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('length Nonlinearity: Senson-PI')
    plt.xlabel('Position /nm')
    plt.ylabel('Deviation /nm')
    plt.legend()
    plt.subplot(4,3,12)
    plt.loglog(1/f_length_Senson_PI_nonlinearity_P, FFT_length_Senson_PI_nonlinearity_T, color='blue', label='diff_nonlinearity_Time')
    plt.loglog(1/f_length_Senson_PI_nonlinearity_P, FFT_length_Senson_PI_nonlinearity_P, color='red', label='diff_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('length Nonlinearity FFT: Senson-PI')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Position Amplitude /nm')
    plt.xlim(1e4,30)
    plt.ylim(1e-4, 1)
    plt.legend()
     
     
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    
    
    '''
        Angular Nonlinearity
    '''
    plt.figure('Angular Nonlinearity')
    plt.gcf().set_size_inches(18,9)
    
    plt.subplot(3,3,1)
    plt.plot(timeline, video_hor, color='blue', label='hor: Video')
    plt.plot(timeline, video_hor_fitline, color='red', label='fitting')
    plt.plot(timeline, Hor_PI, color='black', label='PI')
#     plt.plot(timeline, hor_SmarAct, color='green', label='SmarAct')
    plt.grid(which='both', axis='both')
    plt.title('Video horizontal angle')
    plt.xlabel('Time /s')
    plt.ylabel('Angle /urad')
    plt.legend()
    plt.subplot(3,3,2)
    plt.plot(video_length, video_hor_nonlinearity_T, color='blue', label='hor_video_nonlinearity_Time')
    plt.plot(video_length, video_hor_nonlinearity_P, color='red', label='hor_video_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('Video horizontal angle Nonlinearity')
    plt.xlabel('Position /nm')
    plt.ylabel('Angle /urad')
    plt.legend()
    plt.subplot(3,3,3)
    plt.loglog(1/f_video_hor_nonlinearity_P, FFT_video_hor_nonlinearity_T, color='blue', label='hor_video_nonlinearity_Time')
    plt.loglog(1/f_video_hor_nonlinearity_P, FFT_video_hor_nonlinearity_P, color='red', label='hor_video_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('Video horizontal angle Nonlinearity FFT')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Angle /urad')
    plt.xlim(1e3,30)
    plt.legend()
    
    plt.subplot(3,3,4)
    plt.plot(timeline, video_hor, color='blue', label='hor: Video_hor')
    plt.plot(timeline, video_hor_fitline, color='red', label='fitting')
    plt.plot(timeline, Hor_PI, color='black', label='PI')
    plt.plot(timeline, hor_SmarAct, color='green', label='SmarAct')
    plt.plot(timeline, hor_SmarAct_fitline, color='red')
    plt.grid(which='both', axis='both')
    plt.title('SmarAct horizontal angle')
    plt.xlabel('Time /s')
    plt.ylabel('Angle /urad')
    plt.legend()
    plt.subplot(3,3,5)
    plt.plot(length_SmarAct, hor_SmarAct_nonlinearity_T, color='green', label='SmarAct_hor_nonlinearity_Time')
    plt.plot(length_SmarAct, hor_SmarAct_nonlinearity_P, color='red', label='SmarAct_hor_nonlinearity_Pos.')
    plt.plot(length_SmarAct, video_hor_nonlinearity_P, color='blue', label='Video_hor_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('SmarAct horizontal angle Nonlinearity')
    plt.xlabel('Position /nm')
    plt.ylabel('Angle /urad')
    plt.legend()
    plt.subplot(3,3,6)
    plt.loglog(1/f_hor_SmarAct_nonlinearity_P, FFT_hor_SmarAct_nonlinearity_T, color='green', label='SmarAct_hor_nonlinearity_Time')
    plt.loglog(1/f_hor_SmarAct_nonlinearity_P, FFT_hor_SmarAct_nonlinearity_P, color='red', label='SmarAct_hor_nonlinearity_Pos.')
    plt.loglog(1/f_hor_SmarAct_nonlinearity_P, FFT_video_hor_nonlinearity_P, color='blue', label='Video_hor_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('SmarAct horizontal angle Nonlinearity FFT')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Angle /urad')
    plt.xlim(1e3,30)
    plt.legend()
     
    plt.subplot(3,3,7)
    plt.plot(timeline, video_ver, color='blue', label='ver: Video')
    plt.plot(timeline, video_ver_fitline, color='red', label='fitting')
    plt.plot(timeline, Ver_PI, color='black', label='PI')
    plt.grid(which='both', axis='both')
    plt.title('Video vertical angle')
    plt.xlabel('Time /s')
    plt.ylabel('Angle /urad')
    plt.legend()
    plt.subplot(3,3,8)
    plt.plot(video_length, video_ver_nonlinearity_T, color='blue', label='video_ver_angle_nonlinearity_Time')
    plt.plot(video_length, video_ver_nonlinearity_P, color='red', label='video_ver_angle_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.title('Video vertical angle Nonlinearity')
    plt.xlabel('Position /nm')
    plt.ylabel('Angle /urad')
    plt.legend()
    plt.subplot(3,3,9)
    plt.loglog(1/f_video_ver_nonlinearity_P, FFT_video_ver_nonlinearity_T, color='blue', label='ver_video_nonlinearity_Time')
    plt.loglog(1/f_video_ver_nonlinearity_P, FFT_video_ver_nonlinearity_P, color='red', label='ver_video_nonlinearity_Pos.')
    plt.grid(which='both', axis='both')
    plt.gca().invert_xaxis()
    plt.title('Video Vertical angle Nonlinearity FFT')
    plt.xlabel('Wavelength /nm')
    plt.ylabel('Angle /urad')
    plt.xlim(1e3,30)
    plt.legend()
     
    figManager = plt.get_current_fig_manager()
    figManager.window.showMaximized()
    plt.tight_layout()
    
if 0:
    plt.figure('Ellipse')
    plt.subplot(3,2,1)
    plt.plot(video_length, color='blue', label='Video_common_scaled')
    plt.plot(length_PI, color='red', label='length_PI')
    plt.grid(which='both', axis='both')
    plt.xlabel('Samples')
    plt.ylabel('Position /nm')
    plt.legend()
    plt.subplot(3,2,3)
    plt.plot(length_Senson_PI, color='blue', label='Video - PI')
    plt.grid(which='both', axis='both')
    plt.xlabel('Samples')
    plt.ylabel('Position difference /nm')
    plt.legend()
    plt.subplot(3,2,5)
    plt.plot(length_PI, length_Senson_PI, color='blue', label='Video - PI')
    plt.grid(which='both', axis='both')
    plt.xlabel('Position PI /nm')
    plt.ylabel('Position difference /nm')
    plt.legend()
    
    
#     plt.subplot(3,2,2)
#     plt.plot(SmarAct_common, color='green', label='SmarAct_common_scaled')
#     plt.plot(length_PI, color='red', label='length_PI')
#     plt.grid(which='both', axis='both')
#     plt.xlabel('Samples')
#     plt.ylabel('Position /nm')
#     plt.legend()
#     plt.subplot(3,2,4)
#     length_SmarAct_PI = SmarAct_common - length_PI
#     plt.plot(length_SmarAct_PI, color='green', label='SmarAct - PI')
#     plt.grid(which='both', axis='both')
#     plt.xlabel('Samples')
#     plt.ylabel('Position difference /nm')
#     plt.legend()
#     plt.subplot(3,2,6)
#     plt.plot(length_PI, length_SmarAct_PI, color='green', label='SmarAct - PI')
#     plt.grid(which='both', axis='both')
#     plt.xlabel('Position PI /nm')
#     plt.ylabel('Position difference /nm')
#     plt.legend()
#     
#     plt.figure(5)
#     plt.plot(length_PI, length_SmarAct_PI-np.average(length_SmarAct_PI), color='green', label='SmarAct - PI')
#     plt.plot(length_PI, length_Senson_PI-np.average(length_Senson_PI), color='blue', label='Video - PI')
#     plt.grid(which='both', axis='both')
#     plt.xlabel('Position PI /nm')
#     plt.ylabel('Position difference /nm')
#     plt.legend()

plt.show()


